import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserOrgResponse
from app.core.security import get_current_user
from app.core.rbac import allow_employee

router = APIRouter(prefix="/org", tags=["Organization"])


@router.get("/structure", response_model=list[UserOrgResponse])
async def get_org_structure(
    current_user: User = Depends(allow_employee),
    db: AsyncSession = Depends(get_db),
):
    """Get the full reporting hierarchy visible to the current user."""
    users = await db.execute(
        select(User)
        .options(joinedload(User.department))
        .where(User.is_active == True)
        .order_by(User.manager_id)
    )
    return [
        UserOrgResponse(
            id=u.id,
            full_name=u.full_name,
            email=u.email,
            role=u.role.value,
            position=u.position,
            department_name=u.department.name if u.department else None,
            manager_id=u.manager_id,
        )
        for u in users.unique().scalars().all()
    ]


@router.get("/team/{manager_id}", response_model=list[UserOrgResponse])
async def get_team(
    manager_id: uuid.UUID,
    current_user: User = Depends(allow_employee),
    db: AsyncSession = Depends(get_db),
):
    """Get direct reports of a manager."""
    result = await db.execute(
        select(User)
        .options(joinedload(User.department))
        .where(User.manager_id == manager_id, User.is_active == True)
    )
    team = result.unique().scalars().all()
    return [
        UserOrgResponse(
            id=u.id,
            full_name=u.full_name,
            email=u.email,
            role=u.role.value,
            position=u.position,
            department_name=u.department.name if u.department else None,
            manager_id=u.manager_id,
        )
        for u in team
    ]


@router.get("/managers", response_model=list[UserOrgResponse])
async def get_all_managers(
    current_user: User = Depends(allow_employee),
    db: AsyncSession = Depends(get_db),
):
    """Get all users who have the manager role."""
    result = await db.execute(
        select(User)
        .options(joinedload(User.department))
        .where(User.role.in_(["manager", "admin"]), User.is_active == True)
    )
    managers = result.unique().scalars().all()
    return [
        UserOrgResponse(
            id=u.id,
            full_name=u.full_name,
            email=u.email,
            role=u.role.value,
            position=u.position,
            department_name=u.department.name if u.department else None,
            manager_id=u.manager_id,
        )
        for u in managers
    ]


@router.get("/my-chain", response_model=list[UserOrgResponse])
async def get_my_reporting_chain(
    current_user: User = Depends(allow_employee),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's reporting chain (managers above them)."""
    chain = []
    current = current_user
    seen = set()
    while current and current.manager_id and current.manager_id not in seen:
        seen.add(current.manager_id)
        result = await db.execute(
            select(User)
            .options(joinedload(User.department))
            .where(User.id == current.manager_id)
        )
        current = result.unique().scalar_one_or_none()
        if current:
            chain.append(UserOrgResponse(
                id=current.id,
                full_name=current.full_name,
                email=current.email,
                role=current.role.value,
                position=current.position,
                department_name=current.department.name if current.department else None,
                manager_id=current.manager_id,
            ))
    return chain
