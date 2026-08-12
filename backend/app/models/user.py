"""نموذج المستخدم والأدوار."""

from __future__ import annotations

import enum

from sqlalchemy import Boolean, CheckConstraint, Enum, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class UserRole(enum.StrEnum):
    """أدوار النظام الثلاثة.

    التسجيل العام يُنشئ ``PATIENT`` فقط. حسابات الأخصائيين والمديرين
    يُنشئها مدير من لوحة الإدارة — لا يوجد أي مسار عام يرفع الصلاحيات.
    """

    PATIENT = "patient"
    SPECIALIST = "specialist"
    ADMIN = "admin"


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            name="user_role",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=UserRole.PATIENT,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )

    __table_args__ = (
        # البريد يُخزَّن دائمًا بحروف صغيرة ومنزوع المسافات (يُطبَّق في طبقة
        # المخططات). القيد هنا يمنع أي مسار آخر — سكربت أو migration — من
        # إدخال صيغة مختلفة تكسر فحص التفرّد.
        CheckConstraint("email = lower(email)", name="email_is_lowercase"),
        CheckConstraint("position('@' in email) > 1", name="email_has_local_part"),
    )

    @property
    def can_authenticate(self) -> bool:
        return self.is_active and self.deleted_at is None

    def __repr__(self) -> str:
        # لا نطبع البريد أو الاسم — لا تُسجَّل بيانات تعريف في السجلات.
        return f"<User id={self.id} role={self.role.value}>"


__all__ = ["User", "UserRole"]
