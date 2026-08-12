"""اختبارات سجل التدقيق."""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditAction, AuditLog
from app.models.user import User
from tests.conftest import TEST_PASSWORD, login

REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"

VALID_REGISTRATION = {
    "email": "audited@example.com",
    "password": "StrongPassword123!",
    "full_name": "مستخدم مُدقَّق",
}


async def _actions(session: AsyncSession) -> list[str]:
    result = await session.scalars(select(AuditLog.action).order_by(AuditLog.created_at))
    return list(result)


async def test_registration_is_recorded(client: AsyncClient, session: AsyncSession) -> None:
    await client.post(REGISTER, json=VALID_REGISTRATION)

    assert AuditAction.USER_REGISTERED.value in await _actions(session)


async def test_successful_login_is_recorded(
    client: AsyncClient, session: AsyncSession, patient_user: User
) -> None:
    await client.post(LOGIN, json={"email": patient_user.email, "password": TEST_PASSWORD})

    assert AuditAction.LOGIN_SUCCEEDED.value in await _actions(session)


async def test_failed_login_is_recorded(
    client: AsyncClient, session: AsyncSession, patient_user: User
) -> None:
    """محاولات الفشل تُسجَّل — بدونها لا يمكن كشف هجوم تخمين كلمات السر."""
    await client.post(LOGIN, json={"email": patient_user.email, "password": "WrongPass123!"})

    assert AuditAction.LOGIN_FAILED.value in await _actions(session)


async def test_logout_and_refresh_are_recorded(
    client: AsyncClient, session: AsyncSession, patient_user: User
) -> None:
    tokens = (
        await client.post(LOGIN, json={"email": patient_user.email, "password": TEST_PASSWORD})
    ).json()
    rotated = (
        await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    ).json()
    await client.post("/api/v1/auth/logout", json={"refresh_token": rotated["refresh_token"]})

    actions = await _actions(session)
    assert AuditAction.TOKEN_REFRESHED.value in actions
    assert AuditAction.LOGOUT.value in actions


async def test_token_reuse_is_recorded(
    client: AsyncClient, session: AsyncSession, patient_user: User
) -> None:
    tokens = (
        await client.post(LOGIN, json={"email": patient_user.email, "password": TEST_PASSWORD})
    ).json()
    await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})

    assert AuditAction.TOKEN_REUSE_DETECTED.value in await _actions(session)


async def test_admin_creating_staff_is_recorded_against_the_admin(
    client: AsyncClient, session: AsyncSession, admin_user: User
) -> None:
    headers = await login(client, admin_user.email)
    await client.post(
        "/api/v1/admin/users",
        json={
            "email": "audited.specialist@example.com",
            "password": "StrongPassword123!",
            "full_name": "أخصائي",
            "role": "specialist",
        },
        headers=headers,
    )

    entry = await session.scalar(
        select(AuditLog).where(AuditLog.action == AuditAction.USER_CREATED_BY_ADMIN.value)
    )
    assert entry is not None
    assert entry.actor_user_id == admin_user.id
    assert entry.after is not None
    assert entry.after["role"] == "specialist"


async def test_audit_entries_never_contain_passwords(
    client: AsyncClient, session: AsyncSession
) -> None:
    await client.post(REGISTER, json=VALID_REGISTRATION)

    entries = await session.scalars(select(AuditLog))
    for entry in entries:
        payload = f"{entry.before} {entry.after}"
        assert VALID_REGISTRATION["password"] not in payload
        assert "$argon2" not in payload


async def test_audit_entry_captures_request_context(
    client: AsyncClient, session: AsyncSession
) -> None:
    await client.post(REGISTER, json=VALID_REGISTRATION, headers={"User-Agent": "pytest-agent/1.0"})

    entry = await session.scalar(
        select(AuditLog).where(AuditLog.action == AuditAction.USER_REGISTERED.value)
    )
    assert entry is not None
    assert entry.user_agent == "pytest-agent/1.0"
    assert entry.ip_address is not None


async def test_failed_registration_leaves_no_audit_trail(
    client: AsyncClient, session: AsyncSession
) -> None:
    """القيد يُكتب داخل نفس المعاملة — فلا يبقى سجل لحدث لم يقع."""
    await client.post(REGISTER, json=VALID_REGISTRATION)
    duplicate = await client.post(REGISTER, json=VALID_REGISTRATION)

    assert duplicate.status_code == 409
    actions = await _actions(session)
    assert actions.count(AuditAction.USER_REGISTERED.value) == 1
