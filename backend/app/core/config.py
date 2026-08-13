"""إعدادات التطبيق.

كل الإعدادات تُقرأ من متغيرات البيئة. التطبيق **يرفض الإقلاع** لو متغير
مطلوب ناقص أو قيمته غير صالحة — أفضل من فشل صامت في وقت التشغيل.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["local", "staging", "production"]

_BACKEND_DIR = Path(__file__).resolve().parents[2]
_REPO_ROOT = _BACKEND_DIR.parent

# مسارات مطلقة لا نسبية: المسار النسبي يُحلّ من مجلد التشغيل، فيجد الملف
# عند تشغيل uvicorn من الجذر ويفقده عند تشغيله من backend/. الترتيب يعني
# أن backend/.env — إن وُجد — يغلب ملف الجذر.
_ENV_FILES = (_REPO_ROOT / ".env", _BACKEND_DIR / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILES,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---- General ----
    environment: Environment = "local"
    debug: bool = False
    log_level: str = "INFO"
    project_name: str = "FitFlow"
    api_v1_prefix: str = "/api/v1"

    # ---- PostgreSQL ----
    postgres_user: str
    postgres_password: SecretStr
    postgres_db: str
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    # ---- Redis ----
    redis_host: str = "redis"
    redis_port: int = 6379

    # ---- Security ----
    secret_key: SecretStr
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14
    cors_origins: str = "http://localhost:3000"

    # ---- المرفقات الطبية ----
    # مسار نسبي يُحلّ من مجلد `backend/` لا من مجلد التشغيل ولا من جذر
    # الريبو: داخل الحاوية لا يوجد جذر ريبو أصلًا (التطبيق في /app وحده)،
    # فالحل من مجلد التطبيق هو الوحيد الذي يعطي المسار نفسه في الحالتين.
    upload_dir: str = "var/uploads"
    max_upload_mb: int = 10

    # ---- أول حساب مدير (يستخدمه سكربت التهيئة فقط) ----
    first_admin_email: str = "admin@example.com"
    first_admin_password: SecretStr = SecretStr("ChangeMe_Admin_2026!")
    first_admin_name: str = "مدير النظام"

    @field_validator("secret_key")
    @classmethod
    def _secret_key_is_strong(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < 32:
            raise ValueError("SECRET_KEY لازم يكون 32 حرف على الأقل")
        return value

    @field_validator("max_upload_mb")
    @classmethod
    def _upload_limit_fits_the_column(cls, value: int) -> int:
        # قاعدة البيانات ترفض أي مرفق فوق 50 ميجابايت. حد تطبيقي أعلى منها
        # يعني رفعًا ينجح ثم يفشل عند الحفظ بخطأ قاعدة بيانات لا معنى له.
        if not 1 <= value <= 50:
            raise ValueError("MAX_UPLOAD_MB لازم يكون بين 1 و 50")
        return value

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        """رابط الاتصال غير المتزامن بقاعدة البيانات."""
        password = self.postgres_password.get_secret_value()
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def upload_path(self) -> Path:
        """مجلد المرفقات، مطلقًا دائمًا ومُنشأ عند أول استخدام."""
        path = Path(self.upload_dir)
        if not path.is_absolute():
            path = _BACKEND_DIR / path
        path.mkdir(parents=True, exist_ok=True)
        return path

    @computed_field  # type: ignore[prop-decorator]
    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """تُحمَّل الإعدادات مرة واحدة فقط طوال عمر العملية."""
    # القيم كلها تأتي من متغيرات البيئة، لذلك لا نمرر وسائط هنا.
    return Settings()


__all__ = ["Environment", "Settings", "get_settings"]
