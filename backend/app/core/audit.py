"""كتابة سجل التدقيق."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditAction, AuditLog

# حقول ممنوع تسجيلها إطلاقًا — لا في before ولا في after.
_REDACTED_FIELDS = frozenset({"password", "password_hash", "token", "secret", "refresh_token"})
_REDACTED_PLACEHOLDER = "[محذوف]"


def _sanitize(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if payload is None:
        return None
    return {
        key: (_REDACTED_PLACEHOLDER if key.lower() in _REDACTED_FIELDS else value)
        for key, value in payload.items()
    }


def _client_ip(request: Request | None) -> str | None:
    if request is None:
        return None
    # خلف عاكس (reverse proxy) يكون العنوان الحقيقي في X-Forwarded-For.
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:45]
    return request.client.host if request.client else None


async def record_audit(
    session: AsyncSession,
    *,
    action: AuditAction,
    entity_type: str,
    entity_id: str | uuid.UUID | None = None,
    actor_user_id: uuid.UUID | None = None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    request: Request | None = None,
) -> AuditLog:
    """يضيف قيدًا لسجل التدقيق ضمن نفس معاملة (transaction) الاستدعاء.

    مقصود أن يكون داخل نفس المعاملة: لو فشل التغيير الأساسي وتراجعت
    المعاملة، يتراجع القيد معه — فلا يبقى سجل لحدث لم يقع.
    """
    raw_user_agent = request.headers.get("user-agent") if request is not None else None

    entry = AuditLog(
        actor_user_id=actor_user_id,
        action=action.value,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        before=_sanitize(before),
        after=_sanitize(after),
        ip_address=_client_ip(request),
        user_agent=raw_user_agent[:400] if raw_user_agent else None,
    )
    session.add(entry)
    return entry


__all__ = ["record_audit"]
