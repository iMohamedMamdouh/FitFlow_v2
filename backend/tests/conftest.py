"""إعداد بيئة الاختبار.

يجب ضبط متغيرات البيئة **قبل** استيراد أي وحدة من ``app`` لأن الإعدادات
تُقرأ وقت الاستيراد. pytest يحمّل conftest قبل ملفات الاختبار، فهذا المكان
الصحيح لذلك.

نقطتان مقصودتان في هذا الإعداد:

1. الاختبارات تعمل على **PostgreSQL حقيقي** لا على SQLite. النظام يعتمد
   على أنواع خاصة بـ Postgres (UUID، ENUM، JSONB) وعلى قيود CHECK، واختباره
   على محرك آخر يعني اختبار نظام مختلف عن الذي سيُنشر.

2. نستخدم ``httpx.AsyncClient`` لا ``TestClient``. الأخير يشغّل التطبيق في
   حلقة أحداث منفصلة داخل خيط آخر، فتتوزع اتصالات asyncpg على حلقتين
   ويفشل المجمّع بـ "attached to a different loop". العميل غير المتزامن
   يُبقي التطبيق والاختبار على الحلقة نفسها.
"""

from __future__ import annotations

import os

_TEST_ENV = {
    "ENVIRONMENT": "local",
    "DEBUG": "false",
    "POSTGRES_USER": "fitflow",
    "POSTGRES_PASSWORD": "fitflow",
    "POSTGRES_DB": "fitflow_test",
    "POSTGRES_HOST": "127.0.0.1",
    "POSTGRES_PORT": "5432",
    "REDIS_HOST": "127.0.0.1",
    "REDIS_PORT": "6379",
    "SECRET_KEY": "test_secret_key_at_least_32_characters_long",
    "CORS_ORIGINS": "http://localhost:3000",
}

for _key, _value in _TEST_ENV.items():
    os.environ[_key] = os.environ.get(_key) or _value

from collections.abc import AsyncIterator  # noqa: E402

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config as AlembicConfig  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.core.db import SessionFactory, engine  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEST_PASSWORD = "TestPassword123!"
BASE_URL = "http://testserver"


@pytest.fixture(scope="session", autouse=True)
def _migrate_test_database() -> None:
    """تُطبَّق الـ migrations الحقيقية — فتُختبر هي نفسها في كل جولة."""
    config = AlembicConfig(os.path.join(_ROOT, "alembic.ini"))
    config.set_main_option("script_location", os.path.join(_ROOT, "alembic"))
    command.downgrade(config, "base")
    command.upgrade(config, "head")


@pytest.fixture(autouse=True)
async def _clean_tables() -> AsyncIterator[None]:
    """تفريغ الجداول بعد كل اختبار حتى تبقى الاختبارات مستقلة.

    القائمة تُقرأ من قاعدة البيانات لا تُكتب يدويًا: جدول جديد يُنسى في قائمة
    ثابتة يسرّب بياناته إلى الاختبار التالي، وينتج فشلًا يعتمد على ترتيب
    التنفيذ — أصعب أنواع الفشل في التشخيص.
    """
    yield
    async with engine.begin() as conn:
        result = await conn.execute(
            text(
                "SELECT tablename FROM pg_tables"
                " WHERE schemaname = 'public' AND tablename <> 'alembic_version'"
            )
        )
        tables = [f'"{row[0]}"' for row in result]
        if tables:
            await conn.execute(text(f"TRUNCATE TABLE {', '.join(tables)} RESTART IDENTITY CASCADE"))


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url=BASE_URL) as test_client:
        yield test_client


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    async with SessionFactory() as db_session:
        yield db_session


async def _create_user(role: UserRole, email: str, *, is_active: bool = True) -> User:
    async with SessionFactory() as db_session:
        user = User(
            email=email,
            password_hash=hash_password(TEST_PASSWORD),
            full_name="مستخدم اختبار",
            role=role,
            is_active=is_active,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user


@pytest.fixture
async def patient_user() -> User:
    return await _create_user(UserRole.PATIENT, "patient@example.com")


@pytest.fixture
async def specialist_user() -> User:
    return await _create_user(UserRole.SPECIALIST, "specialist@example.com")


@pytest.fixture
async def admin_user() -> User:
    return await _create_user(UserRole.ADMIN, "admin@example.com")


async def login(
    client: AsyncClient,
    email: str,
    password: str = TEST_PASSWORD,
) -> dict[str, str]:
    """يسجّل الدخول ويرجّع ترويسة التفويض الجاهزة."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
