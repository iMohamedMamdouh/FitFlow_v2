"""مسارات المصادقة: تسجيل، دخول، تحديث الرمز، خروج."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit
from app.core.config import get_settings
from app.core.db import get_session
from app.core.security import (
    InvalidTokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_dummy_password,
    verify_password,
)
from app.models.audit import AuditAction
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UserPublic,
)

router = APIRouter(prefix="/auth", tags=["auth"])

Session = Annotated[AsyncSession, Depends(get_session)]

# رسالة واحدة لكل حالات فشل الدخول — بريد غير مسجّل، كلمة سر خاطئة، أو
# حساب موقوف. أي تمييز بينها يحوّل نموذج الدخول إلى أداة لحصر البُرد
# المسجّلة في المنصة.
_LOGIN_FAILED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="البريد الإلكتروني أو كلمة السر غير صحيحة",
)

_INVALID_REFRESH = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="رمز التحديث غير صالح أو منتهي الصلاحية",
)


async def _issue_token_pair(
    session: AsyncSession,
    user: User,
    *,
    request: Request,
) -> TokenPair:
    """ينشئ صف رمز تحديث جديد ويصدر زوج الرموز."""
    settings = get_settings()
    now = datetime.now(UTC)
    jti = uuid.uuid4()

    session.add(
        RefreshToken(
            id=jti,
            user_id=user.id,
            expires_at=now + timedelta(days=settings.refresh_token_expire_days),
            user_agent=(request.headers.get("user-agent") or None),
        )
    )

    access_token, access_expires_at = create_access_token(user.id, user.role)
    refresh_token, _ = create_refresh_token(user.id, user.role, jti)

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=access_expires_at,
    )


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, request: Request, session: Session) -> User:
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
        role=UserRole.PATIENT,
    )
    session.add(user)
    await session.flush()

    await record_audit(
        session,
        action=AuditAction.USER_REGISTERED,
        entity_type="user",
        entity_id=user.id,
        actor_user_id=user.id,
        after={"email": user.email, "role": user.role.value},
        request=request,
    )
    await session.commit()
    await session.refresh(user)
    return user


@router.post("/login", response_model=TokenPair)
async def login(payload: LoginRequest, request: Request, session: Session) -> TokenPair:
    user = await session.scalar(select(User).where(User.email == payload.email))

    if user is None:
        # نجزّئ كلمة سر وهمية حتى يتساوى زمن الاستجابة مع حالة وجود المستخدم.
        verify_dummy_password(payload.password)
        raise _LOGIN_FAILED

    if not verify_password(payload.password, user.password_hash) or not user.can_authenticate:
        await record_audit(
            session,
            action=AuditAction.LOGIN_FAILED,
            entity_type="user",
            entity_id=user.id,
            actor_user_id=user.id,
            request=request,
        )
        await session.commit()
        raise _LOGIN_FAILED

    tokens = await _issue_token_pair(session, user, request=request)
    await record_audit(
        session,
        action=AuditAction.LOGIN_SUCCEEDED,
        entity_type="user",
        entity_id=user.id,
        actor_user_id=user.id,
        request=request,
    )
    await session.commit()
    return tokens


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, request: Request, session: Session) -> TokenPair:
    try:
        token_payload = decode_token(payload.refresh_token, expected_type="refresh")
    except InvalidTokenError as exc:
        raise _INVALID_REFRESH from exc

    stored = await session.scalar(select(RefreshToken).where(RefreshToken.id == token_payload.jti))
    if stored is None:
        raise _INVALID_REFRESH

    now = datetime.now(UTC)

    # استخدام رمز سبق إبطاله = مؤشر على تسريب. نبطل كل جلسات المستخدم
    # فورًا بدل الاكتفاء برفض الطلب الحالي.
    if stored.revoked_at is not None:
        await session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == stored.user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        await record_audit(
            session,
            action=AuditAction.TOKEN_REUSE_DETECTED,
            entity_type="refresh_token",
            entity_id=stored.id,
            actor_user_id=stored.user_id,
            request=request,
        )
        await session.commit()
        raise _INVALID_REFRESH

    if not stored.is_usable(now):
        raise _INVALID_REFRESH

    user = await session.scalar(select(User).where(User.id == stored.user_id))
    if user is None or not user.can_authenticate:
        raise _INVALID_REFRESH

    # تدوير الرمز: كل تحديث يُبطل الرمز المستخدم ويصدر غيره.
    stored.revoked_at = now
    tokens = await _issue_token_pair(session, user, request=request)

    await record_audit(
        session,
        action=AuditAction.TOKEN_REFRESHED,
        entity_type="refresh_token",
        entity_id=stored.id,
        actor_user_id=user.id,
        request=request,
    )
    await session.commit()
    return tokens


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: RefreshRequest, request: Request, session: Session) -> Response:
    try:
        token_payload = decode_token(payload.refresh_token, expected_type="refresh")
    except InvalidTokenError as exc:
        raise _INVALID_REFRESH from exc

    stored = await session.scalar(select(RefreshToken).where(RefreshToken.id == token_payload.jti))
    if stored is not None and stored.revoked_at is None:
        stored.revoked_at = datetime.now(UTC)
        await record_audit(
            session,
            action=AuditAction.LOGOUT,
            entity_type="refresh_token",
            entity_id=stored.id,
            actor_user_id=stored.user_id,
            request=request,
        )
        await session.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
