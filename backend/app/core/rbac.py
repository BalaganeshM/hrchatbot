import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User, UserRole
from app.core.security import get_current_user


class RoleChecker:
    def __init__(self, *allowed_roles: UserRole):
        self.allowed_roles = allowed_roles

    async def __call__(self, current_user: User = Depends(get_current_user)):
        if current_user.role not in self.allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user


allow_admin = RoleChecker(UserRole.admin)
allow_manager = RoleChecker(UserRole.manager, UserRole.admin)
allow_employee = RoleChecker(UserRole.employee, UserRole.manager, UserRole.admin)


async def can_access_employee(
    target_user_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> bool:
    """Check if current_user can access target_user's data based on role hierarchy."""
    if current_user.role == UserRole.admin:
        return True
    if current_user.id == target_user_id:
        return True
    if current_user.role == UserRole.manager:
        return await _is_subordinate(target_user_id, current_user.id, db)
    return False


async def _is_subordinate(target_id: uuid.UUID, manager_id: uuid.UUID, db: AsyncSession, _seen: set | None = None) -> bool:
    """Recursively check if target_id is under manager_id in the org hierarchy."""
    if _seen is None:
        _seen = set()
    if manager_id in _seen:
        return False
    _seen.add(manager_id)

    result = await db.execute(
        select(User).where(User.manager_id == manager_id, User.is_active == True)
    )
    direct_reports = result.scalars().all()
    for report in direct_reports:
        if report.id == target_id:
            return True
        if await _is_subordinate(target_id, report.id, db, _seen):
            return True
    return False


async def get_employee_hierarchy(user_id: uuid.UUID, db: AsyncSession, _seen: set | None = None) -> list[User]:
    """Get all subordinates (direct and indirect) of a user with cycle detection."""
    if _seen is None:
        _seen = set()
    if user_id in _seen:
        return []
    _seen.add(user_id)

    subordinates = []
    result = await db.execute(
        select(User).where(User.manager_id == user_id, User.is_active == True)
    )
    direct_reports = result.scalars().all()
    for report in direct_reports:
        subordinates.append(report)
        subordinates.extend(await get_employee_hierarchy(report.id, db, _seen))
    return subordinates
