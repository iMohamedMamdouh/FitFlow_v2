"""اختبارات التسجيل والدخول ودورة حياة الرموز."""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from tests.conftest import TEST_PASSWORD, login

REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"
REFRESH = "/api/v1/auth/refresh"
LOGOUT = "/api/v1/auth/logout"
ME = "/api/v1/users/me"

VALID_REGISTRATION = {
    "email": "new.patient@example.com",
    "password": "StrongPassword123!",
    "full_name": "مريض جديد",
}


# ------------------------------------------------------------------ register
async def test_register_creates_patient(client: AsyncClient) -> None:
    response = await client.post(REGISTER, json=VALID_REGISTRATION)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new.patient@example.com"
    assert body["role"] == "patient"
    assert body["is_active"] is True


async def test_register_never_returns_password_hash(client: AsyncClient) -> None:
    response = await client.post(REGISTER, json=VALID_REGISTRATION)

    assert "password_hash" not in response.json()
    assert "password" not in response.json()


async def test_register_ignores_attempt_to_choose_role(client: AsyncClient) -> None:
    """أهم اختبار في هذا الملف: التسجيل العام لا يرفع الصلاحيات أبدًا."""
    response = await client.post(REGISTER, json={**VALID_REGISTRATION, "role": "admin"})

    assert response.status_code == 201
    assert response.json()["role"] == "patient"


async def test_register_normalizes_email_case(client: AsyncClient) -> None:
    response = await client.post(
        REGISTER, json={**VALID_REGISTRATION, "email": "  MiXeD@Example.Com "}
    )

    assert response.status_code == 201
    assert response.json()["email"] == "mixed@example.com"


async def test_register_rejects_duplicate_email_regardless_of_case(client: AsyncClient) -> None:
    await client.post(REGISTER, json=VALID_REGISTRATION)

    duplicate = await client.post(
        REGISTER, json={**VALID_REGISTRATION, "email": "NEW.PATIENT@EXAMPLE.COM"}
    )

    assert duplicate.status_code == 409


async def test_register_rejects_short_password(client: AsyncClient) -> None:
    response = await client.post(REGISTER, json={**VALID_REGISTRATION, "password": "Short1!"})

    assert response.status_code == 422


async def test_register_rejects_malformed_email(client: AsyncClient) -> None:
    response = await client.post(REGISTER, json={**VALID_REGISTRATION, "email": "not-an-email"})

    assert response.status_code == 422


async def test_registered_password_is_hashed_not_stored_plainly(
    client: AsyncClient, session: AsyncSession
) -> None:
    await client.post(REGISTER, json=VALID_REGISTRATION)

    user = await session.scalar(select(User).where(User.email == VALID_REGISTRATION["email"]))
    assert user is not None
    assert user.password_hash != VALID_REGISTRATION["password"]
    assert user.password_hash.startswith("$argon2")


# --------------------------------------------------------------------- login
async def test_login_returns_token_pair(client: AsyncClient, patient_user: User) -> None:
    response = await client.post(
        LOGIN, json={"email": patient_user.email, "password": TEST_PASSWORD}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["access_token"] != body["refresh_token"]


async def test_login_with_wrong_password_is_rejected(
    client: AsyncClient, patient_user: User
) -> None:
    response = await client.post(
        LOGIN, json={"email": patient_user.email, "password": "WrongPass123!"}
    )

    assert response.status_code == 401


async def test_login_does_not_reveal_whether_email_exists(
    client: AsyncClient, patient_user: User
) -> None:
    """رسالة وحالة موحّدتان، وإلا صار نموذج الدخول أداة لحصر المسجّلين."""
    wrong_password = await client.post(
        LOGIN, json={"email": patient_user.email, "password": "WrongPass123!"}
    )
    unknown_email = await client.post(
        LOGIN, json={"email": "ghost@example.com", "password": "WrongPass123!"}
    )

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


async def test_login_rejected_for_deactivated_account(client: AsyncClient, session: AsyncSession):
    user = await session.scalar(select(User))  # لا يوجد مستخدمون بعد
    assert user is None

    await client.post(REGISTER, json=VALID_REGISTRATION)
    created = await session.scalar(select(User).where(User.email == VALID_REGISTRATION["email"]))
    assert created is not None
    created.is_active = False
    await session.commit()

    response = await client.post(
        LOGIN, json={"email": VALID_REGISTRATION["email"], "password": "StrongPassword123!"}
    )

    assert response.status_code == 401


# ------------------------------------------------------------------- session
async def test_access_token_grants_access_to_own_profile(
    client: AsyncClient, patient_user: User
) -> None:
    headers = await login(client, patient_user.email)

    response = await client.get(ME, headers=headers)

    assert response.status_code == 200
    assert response.json()["email"] == patient_user.email


async def test_profile_requires_authentication(client: AsyncClient) -> None:
    assert (await client.get(ME)).status_code == 401


async def test_tampered_token_is_rejected(client: AsyncClient, patient_user: User) -> None:
    headers = await login(client, patient_user.email)
    headers["Authorization"] = headers["Authorization"] + "x"

    assert (await client.get(ME, headers=headers)).status_code == 401


async def test_refresh_token_cannot_be_used_as_access_token(
    client: AsyncClient, patient_user: User
) -> None:
    """بدون فحص النوع تصبح صلاحية الوصول أسابيع بدل دقائق."""
    tokens = (
        await client.post(LOGIN, json={"email": patient_user.email, "password": TEST_PASSWORD})
    ).json()

    response = await client.get(ME, headers={"Authorization": f"Bearer {tokens['refresh_token']}"})

    assert response.status_code == 401


# ------------------------------------------------------------------- refresh
async def test_refresh_issues_a_new_token_pair(client: AsyncClient, patient_user: User) -> None:
    tokens = (
        await client.post(LOGIN, json={"email": patient_user.email, "password": TEST_PASSWORD})
    ).json()

    response = await client.post(REFRESH, json={"refresh_token": tokens["refresh_token"]})

    assert response.status_code == 200
    assert response.json()["refresh_token"] != tokens["refresh_token"]


async def test_rotated_refresh_token_cannot_be_reused(
    client: AsyncClient, patient_user: User
) -> None:
    tokens = (
        await client.post(LOGIN, json={"email": patient_user.email, "password": TEST_PASSWORD})
    ).json()
    await client.post(REFRESH, json={"refresh_token": tokens["refresh_token"]})

    replay = await client.post(REFRESH, json={"refresh_token": tokens["refresh_token"]})

    assert replay.status_code == 401


async def test_reusing_a_revoked_token_kills_every_session(
    client: AsyncClient, patient_user: User
) -> None:
    """إعادة استخدام رمز مُبطل = مؤشر تسريب، فتُبطل كل الجلسات لا الطلب فقط."""
    first = (
        await client.post(LOGIN, json={"email": patient_user.email, "password": TEST_PASSWORD})
    ).json()
    rotated = (await client.post(REFRESH, json={"refresh_token": first["refresh_token"]})).json()

    await client.post(REFRESH, json={"refresh_token": first["refresh_token"]})  # إعادة استخدام

    # الرمز الجديد الصالح يجب أن يكون قد أُبطل هو أيضًا
    assert (
        await client.post(REFRESH, json={"refresh_token": rotated["refresh_token"]})
    ).status_code == 401


async def test_refresh_rejects_garbage_token(client: AsyncClient) -> None:
    assert (await client.post(REFRESH, json={"refresh_token": "not.a.token"})).status_code == 401


# -------------------------------------------------------------------- logout
async def test_logout_revokes_the_refresh_token(client: AsyncClient, patient_user: User) -> None:
    tokens = (
        await client.post(LOGIN, json={"email": patient_user.email, "password": TEST_PASSWORD})
    ).json()

    assert (
        await client.post(LOGOUT, json={"refresh_token": tokens["refresh_token"]})
    ).status_code == 204
    assert (
        await client.post(REFRESH, json={"refresh_token": tokens["refresh_token"]})
    ).status_code == 401


async def test_logout_does_not_invalidate_other_sessions(
    client: AsyncClient, patient_user: User
) -> None:
    phone = (
        await client.post(LOGIN, json={"email": patient_user.email, "password": TEST_PASSWORD})
    ).json()
    laptop = (
        await client.post(LOGIN, json={"email": patient_user.email, "password": TEST_PASSWORD})
    ).json()

    await client.post(LOGOUT, json={"refresh_token": phone["refresh_token"]})

    assert (
        await client.post(REFRESH, json={"refresh_token": laptop["refresh_token"]})
    ).status_code == 200


async def test_registered_user_role_is_patient_in_database(
    client: AsyncClient, admin_user: User
) -> None:
    await client.post(REGISTER, json=VALID_REGISTRATION)
    headers = await login(client, admin_user.email)

    users = (await client.get("/api/v1/admin/users", headers=headers)).json()
    created = next(u for u in users if u["email"] == VALID_REGISTRATION["email"])

    assert created["role"] == UserRole.PATIENT.value
