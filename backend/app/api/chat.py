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

    org_lines = ["Name | Role | Position | Dept | Manager | Salary"]
    dept_map = {d.id: d.name for u in all_users if u.department for d in [u.department]}
    name_map = {u.id: u.full_name for u in all_users}
    for u in all_users:
        mgr = name_map.get(u.manager_id, "top")
        dept = dept_map.get(u.department_id, "-")
        sal = f"${u.salary:,.0f}" if u.salary else "-"
        org_lines.append(f"{u.full_name} | {u.role.value} | {u.position} | {dept} | {mgr} | {sal}")
    org_context = "\n".join(org_lines)

    user_role_str = user.role.value if user else current_user.role.value
    user_display_name = user.full_name if user else current_user.full_name
    if user_role_str == "admin":
        salary_rule = f"ACCESS: {user_display_name} (admin) MAY see any salary."
    elif user_role_str == "manager":
        salary_rule = f"ACCESS: {user_display_name} (manager) may see salary of own reports ONLY."
    else:
        salary_rule = f"ACCESS: {user_display_name} (employee) may see OWN salary ONLY. NEVER reveal others' salaries."

    async def event_stream():
        full_text = ""

        try:
            async for token in ask_hr_policy_stream(
                message,
                session_id,
                user_name=user.full_name if user else current_user.full_name,
                user_role=user_role_str,
                user_department=user.department.name if user and user.department else "Unknown",
                org_context=org_context,
                salary_rule=salary_rule,
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
