"""اختبارات الإعدادات — التحقق من أن التطبيق يرفض الإقلاع بإعدادات غير صالحة."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings

_VALID = {
    "postgres_user": "u",
    "postgres_password": "p",
    "postgres_db": "d",
    "secret_key": "x" * 32,
}


def test_missing_required_setting_fails_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("POSTGRES_USER", raising=False)
    fields = {k: v for k, v in _VALID.items() if k != "postgres_user"}

    with pytest.raises(ValidationError):
        Settings(_env_file=None, **fields)  # type: ignore[arg-type]


def test_short_secret_key_is_rejected() -> None:
    with pytest.raises(ValidationError, match="32"):
        Settings(_env_file=None, **{**_VALID, "secret_key": "too_short"})  # type: ignore[arg-type]


def test_database_url_is_async_and_contains_credentials() -> None:
    settings = Settings(_env_file=None, **_VALID)  # type: ignore[arg-type]

    assert settings.database_url.startswith("postgresql+asyncpg://")
    assert "u:p@" in settings.database_url


def test_cors_origins_are_split_and_trimmed() -> None:
    settings = Settings(  # type: ignore[arg-type]
        _env_file=None, **{**_VALID, "cors_origins": "http://a.com, http://b.com ,"}
    )

    assert settings.cors_origin_list == ["http://a.com", "http://b.com"]
