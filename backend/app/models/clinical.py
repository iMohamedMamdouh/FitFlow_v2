"""بيانات المريض السريرية: الإصابات ومرفقاتها والقياسات الفسيولوجية."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    AttachmentType,
    BodySide,
    InjuryStatus,
    ReadingSource,
    pg_enum,
)


class Injury(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """إصابة مسجَّلة على مريض."""

    __tablename__ = "injuries"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # RESTRICT لا CASCADE: حذف نوع إصابة من القاعدة العلمية يجب أن يفشل ما
    # دامت هناك إصابات مسجّلة عليه، لا أن يمحوها.
    injury_type_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("injury_types.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    side: Mapped[BodySide] = mapped_column(
        pg_enum(BodySide, "body_side"),
        nullable=False,
        default=BodySide.NOT_APPLICABLE,
    )
    injury_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[InjuryStatus] = mapped_column(
        pg_enum(InjuryStatus, "injury_status"),
        nullable=False,
        default=InjuryStatus.ACUTE,
        index=True,
    )
    current_phase: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default=text("1")
    )

    pain_level: Mapped[int] = mapped_column(Integer, nullable=False)
    # قياسات مدى الحركة لكل مفصل: {"knee_flexion": 95, "knee_extension": 0}
    range_of_motion: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )

    had_surgery: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    surgery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint("pain_level BETWEEN 0 AND 10", name="pain_level_within_scale"),
        CheckConstraint("current_phase BETWEEN 1 AND 10", name="current_phase_within_range"),
        CheckConstraint("injury_date <= CURRENT_DATE", name="injury_date_not_in_future"),
        # تاريخ جراحة بدون جراحة تناقض، وجراحة قبل الإصابة مستحيلة.
        CheckConstraint(
            "(had_surgery AND surgery_date IS NOT NULL AND surgery_date >= injury_date)"
            " OR (NOT had_surgery AND surgery_date IS NULL)",
            name="surgery_fields_are_consistent",
        ),
        Index("ix_injuries_user_status", "user_id", "status"),
    )

    @property
    def is_active(self) -> bool:
        return self.status is not InjuryStatus.RECOVERED

    @property
    def blocks_resistance_training(self) -> bool:
        """الإصابة الحادة تمنع تمارين المقاومة على المنطقة المصابة (ADR-007)."""
        return self.status is InjuryStatus.ACUTE


class InjuryAttachment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """صور الأشعة والتقارير الطبية.

    نخزّن مفتاح الملف في التخزين الخارجي فقط، لا الملف نفسه: الوصول يتم
    عبر روابط موقّعة قصيرة العمر تُولَّد في المرحلة 5، فلا يصبح أي رابط
    دائمًا وقابلًا للمشاركة.
    """

    __tablename__ = "injury_attachments"

    injury_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("injuries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[AttachmentType] = mapped_column(
        pg_enum(AttachmentType, "attachment_type"), nullable=False
    )
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    __table_args__ = (
        CheckConstraint("size_bytes > 0 AND size_bytes <= 52428800", name="size_within_50mb"),
    )


class PhysiologicalReading(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """قياس فسيولوجي مؤرَّخ.

    الوزن هنا لا في الملف الشخصي: هو سلسلة زمنية يبني عليها كشف الثبات
    (المرحلة 4). و**مؤشر كتلة الجسم لا يُخزَّن** — يُحسب من الوزن والطول عند
    الحاجة، لأن قيمة مخزَّنة تصبح خاطئة بمجرد تغيّر أي من طرفيها.
    """

    __tablename__ = "physiological_readings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    reading_date: Mapped[date] = mapped_column(Date, nullable=False)
    source: Mapped[ReadingSource] = mapped_column(
        pg_enum(ReadingSource, "reading_source"),
        nullable=False,
        default=ReadingSource.MANUAL,
    )

    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    body_fat_pct: Mapped[Decimal | None] = mapped_column(Numeric(4, 1), nullable=True)
    muscle_mass_kg: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    resting_hr: Mapped[int | None] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "weight_kg IS NULL OR weight_kg BETWEEN 20 AND 500", name="weight_within_range"
        ),
        CheckConstraint(
            "body_fat_pct IS NULL OR body_fat_pct BETWEEN 1 AND 70", name="body_fat_within_range"
        ),
        CheckConstraint(
            "muscle_mass_kg IS NULL OR muscle_mass_kg BETWEEN 5 AND 150",
            name="muscle_mass_within_range",
        ),
        CheckConstraint(
            "resting_hr IS NULL OR resting_hr BETWEEN 25 AND 250", name="resting_hr_within_range"
        ),
        CheckConstraint("reading_date <= CURRENT_DATE", name="reading_date_not_in_future"),
        # قياس واحد لكل يوم من كل مصدر — يمنع تكرار الإدخال اليدوي بالخطأ
        # دون منع جهاز من إرسال قياسه في نفس اليوم.
        UniqueConstraint("user_id", "reading_date", "source", name="one_reading_per_day_source"),
        Index("ix_readings_user_date", "user_id", "reading_date"),
    )


class DailyLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """التسجيل اليومي للمريض — أساس المتابعة والتعديل التلقائي."""

    __tablename__ = "daily_logs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    log_date: Mapped[date] = mapped_column(Date, nullable=False)

    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    pain_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    diet_adherence_pct: Mapped[int | None] = mapped_column(Integer, nullable=True)
    exercise_adherence_pct: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "pain_level IS NULL OR pain_level BETWEEN 0 AND 10", name="pain_level_within_scale"
        ),
        CheckConstraint(
            "diet_adherence_pct IS NULL OR diet_adherence_pct BETWEEN 0 AND 100",
            name="diet_adherence_within_range",
        ),
        CheckConstraint(
            "exercise_adherence_pct IS NULL OR exercise_adherence_pct BETWEEN 0 AND 100",
            name="exercise_adherence_within_range",
        ),
        CheckConstraint(
            "weight_kg IS NULL OR weight_kg BETWEEN 20 AND 500", name="weight_within_range"
        ),
        CheckConstraint("log_date <= CURRENT_DATE", name="log_date_not_in_future"),
        UniqueConstraint("user_id", "log_date", name="one_log_per_day"),
        Index("ix_daily_logs_user_date", "user_id", "log_date"),
    )


__all__ = ["DailyLog", "Injury", "InjuryAttachment", "PhysiologicalReading"]
