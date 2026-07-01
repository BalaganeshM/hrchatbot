import json
import re

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.models.user import User, UserRole
from app.core.security import get_current_user
from app.core.rbac import allow_employee, allow_admin
from app.services.langchain_service import ask_hr_policy, ask_hr_policy_stream, ingest_hr_documents

router = APIRouter(prefix="/chat", tags=["Chat"])

ACTION_RE = re.compile(r'\[ACTION:\s*(\w+)\s+(.*?)\]')


async def _execute_update_manager(target: User, new_mgr: User, db: AsyncSession) -> str:
    """Execute a manager change in the DB with cycle prevention."""
    if new_mgr.id == target.id:
        return f"Cannot set {target.full_name} to report to themselves."

    from app.core.rbac import get_employee_hierarchy
    target_subs = await get_employee_hierarchy(target.id, db)
    if any(s.id == new_mgr.id for s in target_subs):
        return f"Cannot set {new_mgr.full_name} as manager — they are a subordinate of {target.full_name}."

    old_mgr_name = "top level"
    if target.manager_id:
        from sqlalchemy import select as sel
        r = await db.execute(sel(User).where(User.id == target.manager_id))
        old = r.scalar_one_or_none()
        old_mgr_name = old.full_name if old else "top level"

    target.manager_id = new_mgr.id
    await db.commit()
    return f"Moved {target.full_name} from {old_mgr_name} to report to {new_mgr.full_name}."


async def _handle_llm_actions(
    answer: str,
    current_user: User,
    db: AsyncSession,
    all_users: list[User],
) -> str:
    """Parse [ACTION: ...] tags from the LLM response and execute them."""
    changes = []

    for match in ACTION_RE.finditer(answer):
        action_type = match.group(1)
        body = match.group(2)
        pairs = re.findall(r'(\w+)=[\'"](.+?)[\'"]', body)
        params = {k: v for k, v in pairs} if pairs else None
        if not params:
            continue

        if action_type == "UPDATE_MANAGER":
            if current_user.role != UserRole.admin:
                changes.append("Only admins can change reporting lines.")
                continue

            emp_name = params.get("employee", "").strip().lower()
            mgr_name = params.get("new_manager", "").strip().lower()

            target = next((u for u in all_users if u.full_name.lower() == emp_name), None)
            new_mgr = next((u for u in all_users if u.full_name.lower() == mgr_name), None)

            if not target:
                changes.append(f"Employee '{params.get('employee', '')}' not found in organization.")
            elif not new_mgr:
                changes.append(f"Manager '{params.get('new_manager', '')}' not found in organization.")
            elif target.manager_id == new_mgr.id:
                changes.append(f"{target.full_name} already reports to {new_mgr.full_name}.")
            else:
                msg = await _execute_update_manager(target, new_mgr, db)
                changes.append(msg)

    if changes:
        answer = ACTION_RE.sub("", answer).strip()
        answer += "\n\n" + "\n".join(changes)

    return answer


@router.post("/ask")
async def chat(
    body: dict,
    current_user: User = Depends(allow_employee),
    db: AsyncSession = Depends(get_db),
):
    """Send a chat message and stream the LLM response via SSE."""
    message = body.get("message", "")
    session_id = body.get("session_id") or str(current_user.id)

    result = await db.execute(
        select(User)
        .options(joinedload(User.department))
        .where(User.id == current_user.id)
    )
    user = result.unique().scalar_one_or_none()

    org_result = await db.execute(
        select(User)
        .options(joinedload(User.department))
        .where(User.is_active == True)
    )
    all_users = org_result.unique().scalars().all()

    from app.core.rbac import get_employee_hierarchy
    sub_ids = set()
    if current_user.role == UserRole.manager:
        subs = await get_employee_hierarchy(current_user.id, db)
        sub_ids = {s.id for s in subs}
        sub_ids.add(current_user.id)
    elif current_user.role == UserRole.employee:
        sub_ids = {current_user.id}

    can_view_all_details = current_user.role == UserRole.admin

    org_context_lines = []
    for u in all_users:
        mgr_name = ""
        if u.manager_id:
            mgr = next((x for x in all_users if x.id == u.manager_id), None)
            mgr_name = mgr.full_name if mgr else ""
        dept = u.department.name if u.department else ""
        if can_view_all_details or u.id in sub_ids:
            salary_str = f" | ${u.salary:,.0f}" if u.salary else ""
            org_context_lines.append(f"{u.full_name} ({u.role.value}) - {u.position}, {dept} -> {mgr_name or 'top'}{salary_str}")
        else:
            org_context_lines.append(f"{u.full_name} ({u.role.value}) - {u.position}, {dept} -> {mgr_name or 'top'}")
    org_context = "\n".join(org_context_lines)

    async def event_stream():
        full_text = ""

        try:
            async for token in ask_hr_policy_stream(
                message,
                session_id,
                user_name=user.full_name if user else current_user.full_name,
                user_role=user.role.value if user else current_user.role.value,
                user_department=user.department.name if user and user.department else "Unknown",
                org_context=org_context,
                current_user_id=str(current_user.id),
                current_user_role=current_user.role.value,
            ):
                full_text += token
                yield f"data: {json.dumps({'token': token})}\n\n"

            processed = await _handle_llm_actions(full_text, current_user, db, all_users)
            extra = processed[len(full_text):]
            if extra:
                yield f"data: {json.dumps({'token': extra})}\n\n"

            yield "data: [DONE]\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/ingest")
async def ingest_documents(
    current_user: User = Depends(allow_admin),
):
    """Ingest HR documents into the vector store (admin only)."""
    count = await ingest_hr_documents()
    return {"ingested": count, "status": "ok"}


@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    """Real-time chat over WebSocket (streaming)."""
    await websocket.accept()
    session_id = "anonymous"

    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            full_text = ""
            async for token in ask_hr_policy_stream(message, session_id):
                full_text += token
                await websocket.send_json({"token": token})
            await websocket.send_json({"done": True})
    except WebSocketDisconnect:
        pass
