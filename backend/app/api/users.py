"""مسارات المستخدم الحالي."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.deps import CurrentUser
from app.models.user import User
from app.schemas.auth import UserPublic

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserPublic)
async def read_current_user(user: CurrentUser) -> User:
    return user
