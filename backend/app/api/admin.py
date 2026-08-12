"""مسارات المدير.

كل مسار هنا محمي بـ ``require_roles(UserRole.ADMIN)``. لوحة الإدارة
الكاملة في المرحلة 10 — هنا فقط ما تحتاجه المرحلة 1: إنشاء حسابات
الأخصائيين، لأنه لا يوجد تسجيل عام لها.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit
from app.core.db import get_session
from app.core.deps import require_roles
from app.core.security import hash_password
from app.models.audit import AuditAction
from app.models.user import User, UserRole
from app.schemas.auth import CreateStaffRequest, UserPublic

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)

Session = Annotated[AsyncSession, Depends(get_session)]
Admin = Annotated[User, Depends(require_roles(UserRole.ADMIN))]


@router.get("/users", response_model=list[UserPublic])
async def list_users(session: Session, limit: int = 50, offset: int = 0) -> list[User]:
    limit = min(max(limit, 1), 200)
    result = await session.scalars(
        select(User)
        .where(User.deleted_at.is_(None))
        .order_by(User.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result)


@router.post("/users", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def create_staff_user(
    payload: CreateStaffRequest,
    request: Request,
    session: Session,
    admin: Admin,
) -> User:
    existing = await session.scalar(select(User.id).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="هذا البريد الإلكتروني مسجّل بالفعل",
        )

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name.strip(),
        role=payload.role,
    )
    session.add(user)
    await session.flush()

    await record_audit(
        session,
        action=AuditAction.USER_CREATED_BY_ADMIN,
        entity_type="user",
        entity_id=user.id,
        actor_user_id=admin.id,
        after={"email": user.email, "role": user.role.value},
        request=request,
    )
    await session.commit()
    await session.refresh(user)
    return user
