"""اعتماديات FastAPI: المستخدم الحالي وفرض الأدوار (RBAC)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.security import InvalidTokenError, decode_token
from app.models.user import User, UserRole

_bearer_scheme = HTTPBearer(auto_error=False)

_CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="بيانات الاعتماد غير صالحة",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    if credentials is None:
        raise _CREDENTIALS_ERROR

    try:
        payload = decode_token(credentials.credentials, expected_type="access")
    except InvalidTokenError as exc:
        raise _CREDENTIALS_ERROR from exc

    user = await session.scalar(select(User).where(User.id == payload.user_id))

    # الدور يُقرأ من قاعدة البيانات لا من الرمز: لو خُفِّضت صلاحية مستخدم،
    # لا ننتظر انتهاء صلاحية رمزه ليفقد الصلاحية الأعلى.
    if user is None or not user.can_authenticate:
        raise _CREDENTIALS_ERROR

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*allowed_roles: UserRole) -> Callable[[User], Awaitable[User]]:
    """يبني اعتمادية تسمح للأدوار المحددة فقط.

    مثال::

        @router.get("/admin/users", dependencies=[Depends(require_roles(UserRole.ADMIN))])
    """
    if not allowed_roles:
        raise ValueError("require_roles تحتاج دورًا واحدًا على الأقل")

    permitted = frozenset(allowed_roles)

    async def _dependency(user: CurrentUser) -> User:
        if user.role not in permitted:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="لا تملك صلاحية الوصول لهذا المورد",
            )
        return user

    return _dependency


__all__ = ["CurrentUser", "get_current_user", "require_roles"]
