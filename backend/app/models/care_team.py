"""ربط الأخصائيين بمرضاهم وملاحظاتهم."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Computed,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import pg_enum
from app.models.user import UserRole


class SpecialistPatient(Base, TimestampMixin):
    """إسناد مريض إلى أخصائي.

    عمود ``specialist_role`` مولَّد بقيمة ثابتة ويدخل في مفتاح أجنبي مركّب
    على ``users(id, role)``. النتيجة: قاعدة البيانات نفسها ترفض إسناد مريض
    إلى مستخدم ليس أخصائيًا، وترفض تخفيض دور أخصائي ما دام لديه مرضى
    مسنَدون — فلا يمكن لخطأ برمجي أو سكربت صيانة أن يتجاوز القاعدة.
    """

    __tablename__ = "specialist_patients"

    specialist_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    specialist_role: Mapped[UserRole] = mapped_column(
        pg_enum(UserRole, "user_role"),
        Computed("'specialist'::user_role", persisted=True),
        nullable=False,
    )

    assigned_by: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["specialist_id", "specialist_role"],
            ["users.id", "users.role"],
            name="fk_specialist_patients_specialist_is_specialist",
            ondelete="CASCADE",
        ),
        CheckConstraint("specialist_id <> patient_id", name="specialist_is_not_the_patient"),
        Index("ix_specialist_patients_patient", "patient_id"),
    )


class SpecialistNote(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """ملاحظة من أخصائي على مريض، وربما على خطة بعينها."""

    __tablename__ = "specialist_notes"

    specialist_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("plans.id", ondelete="CASCADE"),
        nullable=True,
    )
    note: Mapped[str] = mapped_column(Text, nullable=False)
    # ملاحظة داخلية لا يراها المريض — مساحة الأخصائي للتفكير السريري.
    is_internal: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )

    __table_args__ = (
        CheckConstraint("length(trim(note)) > 0", name="note_is_not_blank"),
        Index("ix_specialist_notes_patient_created", "patient_id", "created_at"),
    )


__all__ = ["SpecialistNote", "SpecialistPatient"]
