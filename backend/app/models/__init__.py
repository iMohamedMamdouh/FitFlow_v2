"""نماذج قاعدة البيانات.

كل نموذج جديد **لازم** يُستورد هنا، وإلا لن يراه Alembic عند التوليد
التلقائي وستُولَّد migration ناقصة بصمت.
"""

from app.models.audit import AuditAction, AuditLog
from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole

__all__ = [
    "AuditAction",
    "AuditLog",
    "Base",
    "RefreshToken",
    "SoftDeleteMixin",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    "User",
    "UserRole",
]
