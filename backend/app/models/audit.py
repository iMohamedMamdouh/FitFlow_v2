"""سجل التدقيق (Audit Log).

جدول **للإضافة فقط** — لا تعديل ولا حذف. أي تغيير على كيان حساس يُسجَّل هنا:
مين عمل إيه، على أي كيان، وامتى، وقيمة الحقول قبل وبعد.

مبني من المرحلة 1 وليس لاحقًا: سجل تدقيق يُضاف بعد أن تتراكم البيانات
يترك فجوة دائمة لا يمكن سدها بأثر رجعي.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin


class AuditAction(enum.StrEnum):
    """الأفعال المسجَّلة. تتوسع مع كل مرحلة."""

    USER_REGISTERED = "user.registered"
    USER_CREATED_BY_ADMIN = "user.created_by_admin"
    USER_UPDATED_BY_ADMIN = "user.updated_by_admin"
    PATIENT_ASSIGNED = "care_team.patient_assigned"
    PATIENT_UNASSIGNED = "care_team.patient_unassigned"
    CATALOG_CREATED = "catalog.created"
    CATALOG_UPDATED = "catalog.updated"
    CATALOG_REVIEWED = "catalog.reviewed"
    LOGIN_SUCCEEDED = "auth.login_succeeded"
    LOGIN_FAILED = "auth.login_failed"
    LOGOUT = "auth.logout"
    TOKEN_REFRESHED = "auth.token_refreshed"
    TOKEN_REUSE_DETECTED = "auth.token_reuse_detected"

    PROFILE_UPDATED = "profile.updated"
    CONSENT_ACCEPTED = "profile.consent_accepted"
    INJURY_RECORDED = "injury.recorded"
    INJURY_ATTACHMENT_UPLOADED = "injury.attachment_uploaded"

    PLAN_GENERATED = "plan.generated"
    PLAN_SUBMITTED_FOR_REVIEW = "plan.submitted_for_review"
    PLAN_APPROVED = "plan.approved"
    PLAN_CHANGES_REQUESTED = "plan.changes_requested"
    PLAN_ACTIVATED = "plan.activated"
    PLAN_ARCHIVED = "plan.archived"
    PATIENT_RECORD_VIEWED = "patient.record_viewed"


class AuditLog(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "audit_logs"

    # يبقى السجل قائمًا حتى لو حُذف المستخدم — لذلك SET NULL وليس CASCADE.
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    before: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    after: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)  # يتسع لـ IPv6
    user_agent: Mapped[str | None] = mapped_column(String(400), nullable=True)

    # لا يوجد updated_at — السجل غير قابل للتعديل بحكم التصميم.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )


__all__ = ["AuditAction", "AuditLog"]
