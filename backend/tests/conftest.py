"""إعداد بيئة الاختبار.

يجب ضبط متغيرات البيئة **قبل** استيراد أي وحدة من ``app`` لأن الإعدادات
تُقرأ وقت الاستيراد. pytest يحمّل conftest قبل ملفات الاختبار، فهذا المكان
الصحيح لذلك.
"""

from __future__ import annotations

import os

_TEST_ENV = {
    "ENVIRONMENT": "local",
    "DEBUG": "false",
    "POSTGRES_USER": "test",
    "POSTGRES_PASSWORD": "test",
    "POSTGRES_DB": "test",
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
    "REDIS_HOST": "localhost",
    "REDIS_PORT": "6379",
    "SECRET_KEY": "test_secret_key_at_least_32_characters_long",
    "CORS_ORIGINS": "http://localhost:3000",
}

for _key, _value in _TEST_ENV.items():
    os.environ.setdefault(_key, _value)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import create_app  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())
