"""الأساس المشترك لكل نماذج قاعدة البيانات."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# تسمية موحّدة للقيود والفهارس.
# بدونها يولّد Postgres أسماء عشوائية، فتفشل عمليات downgrade في Alembic
# لأنها لا تعرف اسم القيد الذي تحذفه — وهذا أحد أشهر أسباب فشل التراجع.
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class UUIDPrimaryKeyMixin:
    """مفتاح أساسي من نوع UUID.

    نستخدم UUID بدل الأرقام المتسلسلة لأن معرّفات المرضى تظهر في الروابط،
    والأرقام المتسلسلة تسرّب عدد المستخدمين وتسمح بتخمين معرّفات أخرى.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """حذف منطقي.

    البيانات الصحية لا تُحذف فعليًا — نحتاجها للتدقيق والمساءلة القانونية.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


__all__ = [
    "NAMING_CONVENTION",
    "Base",
    "SoftDeleteMixin",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
]
