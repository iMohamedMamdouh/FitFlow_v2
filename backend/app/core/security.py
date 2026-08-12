"""تجزئة كلمات السر وإصدار الرموز.

كلمات السر: **Argon2id** — الخوارزمية الموصى بها حاليًا، وأقوى من bcrypt
ضد الهجمات المعتمدة على العتاد المتخصص (GPU/ASIC).
"""

from __future__ import annotations

import uuid
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Final, Literal

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error, InvalidHashError, VerifyMismatchError

from app.core.config import get_settings
from app.models.user import UserRole

ALGORITHM: Final = "HS256"
TokenType = Literal["access", "refresh"]

_hasher = PasswordHasher()

# تجزئة وهمية تُستخدم عندما لا يوجد مستخدم بالبريد المُدخل.
# الغرض: أن يستغرق الفشل نفس زمن النجاح تقريبًا، فلا يستطيع المهاجم
# استنتاج البُرد المسجّلة من فرق التوقيت (timing attack).
_DUMMY_HASH: Final = _hasher.hash("dummy-password-for-constant-time-comparison")


class InvalidTokenError(Exception):
    """رمز غير صالح: توقيع خاطئ، أو منتهٍ، أو من نوع غير متوقع."""


@dataclass(frozen=True, slots=True)
class TokenPayload:
    user_id: uuid.UUID
    role: UserRole
    token_type: TokenType
    jti: uuid.UUID
    expires_at: datetime


# ------------------------------------------------------------------ passwords
def hash_password(plain_password: str) -> str:
    return _hasher.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, plain_password)
    except (VerifyMismatchError, Argon2Error, InvalidHashError):
        return False


def verify_dummy_password(plain_password: str) -> None:
    """تُستدعى عند عدم وجود المستخدم، لتثبيت زمن الاستجابة."""
    with suppress(VerifyMismatchError, Argon2Error, InvalidHashError):
        _hasher.verify(_DUMMY_HASH, plain_password)


def password_needs_rehash(password_hash: str) -> bool:
    """هل التجزئة أُنشئت بمعاملات أضعف من الحالية؟"""
    try:
        return _hasher.check_needs_rehash(password_hash)
    except (Argon2Error, InvalidHashError):
        return True


# --------------------------------------------------------------------- tokens
def _create_token(
    *,
    user_id: uuid.UUID,
    role: UserRole,
    token_type: TokenType,
    lifetime: timedelta,
    jti: uuid.UUID,
) -> tuple[str, datetime]:
    settings = get_settings()
    issued_at = datetime.now(UTC)
    expires_at = issued_at + lifetime

    claims: dict[str, Any] = {
        "sub": str(user_id),
        "role": role.value,
        "type": token_type,
        "jti": str(jti),
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(claims, settings.secret_key.get_secret_value(), algorithm=ALGORITHM)
    return token, expires_at


def create_access_token(user_id: uuid.UUID, role: UserRole) -> tuple[str, datetime]:
    settings = get_settings()
    return _create_token(
        user_id=user_id,
        role=role,
        token_type="access",
        lifetime=timedelta(minutes=settings.access_token_expire_minutes),
        jti=uuid.uuid4(),
    )


def create_refresh_token(
    user_id: uuid.UUID,
    role: UserRole,
    jti: uuid.UUID,
) -> tuple[str, datetime]:
    """``jti`` هو معرّف صف ``refresh_tokens`` — به يتم الإبطال."""
    settings = get_settings()
    return _create_token(
        user_id=user_id,
        role=role,
        token_type="refresh",
        lifetime=timedelta(days=settings.refresh_token_expire_days),
        jti=jti,
    )


def decode_token(token: str, *, expected_type: TokenType) -> TokenPayload:
    settings = get_settings()
    try:
        claims = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[ALGORITHM],
            options={"require": ["sub", "exp", "iat", "jti"]},
        )
    except jwt.PyJWTError as exc:
        raise InvalidTokenError(str(exc)) from exc

    # فحص النوع إلزامي: بدونه يصلح رمز التحديث كرمز وصول، فتصبح مدة
    # صلاحية الوصول أسابيع بدل دقائق.
    if claims.get("type") != expected_type:
        raise InvalidTokenError(f"نوع الرمز غير متوقع: {claims.get('type')!r}")

    try:
        return TokenPayload(
            user_id=uuid.UUID(claims["sub"]),
            role=UserRole(claims["role"]),
            token_type=expected_type,
            jti=uuid.UUID(claims["jti"]),
            expires_at=datetime.fromtimestamp(claims["exp"], tz=UTC),
        )
    except (KeyError, ValueError) as exc:
        raise InvalidTokenError("محتوى الرمز غير صالح") from exc


__all__ = [
    "ALGORITHM",
    "InvalidTokenError",
    "TokenPayload",
    "TokenType",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "hash_password",
    "password_needs_rehash",
    "verify_dummy_password",
    "verify_password",
]
