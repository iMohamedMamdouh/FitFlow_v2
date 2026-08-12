"""رموز التحديث (Refresh Tokens).

نخزّن الرموز في قاعدة البيانات بدل الاكتفاء بـ JWT مستقل، لأن الرمز
المستقل لا يمكن إبطاله قبل انتهاء صلاحيته. مع بيانات صحية، القدرة على
إبطال جلسة فورًا (تسجيل خروج، سرقة جهاز) شرط أساسي.

الرمز نفسه لا يُخزَّن — فقط معرّفه (``id`` = ``jti`` داخل الـ JWT).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RefreshToken(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    user_agent: Mapped[str | None] = mapped_column(String(400), nullable=True)

    def is_usable(self, now: datetime) -> bool:
        return self.revoked_at is None and self.expires_at > now


__all__ = ["RefreshToken"]
