from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.core.security import hash_password, get_current_user
from app.core.rbac import allow_admin, allow_manager, allow_employee, can_access_employee, RoleChecker

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.get("/", response_model=list[UserResponse])
async def list_employees(
    department_id: str | None = Query(None),
    current_user: User = Depends(allow_employee),
    db: AsyncSession = Depends(get_db),
):
    """Admin/Manager sees all employees (manager only sees their subordinates)."""
    query = select(User).where(User.is_active == True)

    if department_id:
        query = query.where(User.department_id == uuid.UUID(department_id))

    if current_user.role == UserRole.manager:
        from app.core.rbac import get_employee_hierarchy
        subordinates = await get_employee_hierarchy(current_user.id, db)
        sub_ids = {s.id for s in subordinates}
        sub_ids.add(current_user.id)
        query = query.where(User.id.in_(sub_ids))
    elif current_user.role == UserRole.employee:
        query = query.where(User.id == current_user.id)

    result = await db.execute(query)
    users = result.scalars().all()
    return [UserResponse.model_validate(u) for u in users]


@router.get("/{user_id}", response_model=UserResponse)
async def get_employee(
    user_id: uuid.UUID,
    current_user: User = Depends(allow_employee),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific employee's details (RBAC enforced)."""
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    if not await can_access_employee(user_id, current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return UserResponse.model_validate(target)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    body: UserCreate,
    current_user: User = Depends(allow_admin),
    db: AsyncSession = Depends(get_db),
):
    """Only admin can create employees."""
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        first_name=body.first_name,
        last_name=body.last_name,
        position=body.position,
        phone=body.phone,
        salary=body.salary,
        hire_date=body.hire_date,
        role=body.role if current_user.role == UserRole.admin else UserRole.employee,
        department_id=uuid.UUID(body.department_id) if body.department_id else None,
        manager_id=uuid.UUID(body.manager_id) if body.manager_id else None,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_employee(
    user_id: uuid.UUID,
    body: UserUpdate,
    current_user: User = Depends(allow_manager),
    db: AsyncSession = Depends(get_db),
):
    """Manager can edit subordinates; Admin can edit anyone."""
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    if not await can_access_employee(user_id, current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    update_data = body.model_dump(exclude_unset=True)
    if current_user.role != UserRole.admin:
        update_data.pop("role", None)
        if "manager_id" in update_data:
            if not await can_access_employee(user_id, current_user, db):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only change reporting for your subordinates")

    for field, value in update_data.items():
        setattr(target, field, value)

    await db.commit()
    await db.refresh(target)
    return UserResponse.model_validate(target)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(
    user_id: uuid.UUID,
    current_user: User = Depends(allow_admin),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete (deactivate) an employee. Admin only."""
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    target.is_active = False
    await db.commit()
