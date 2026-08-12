"""اختبارات فرض الأدوار (RBAC).

الاختبار الجوهري هنا: **مريض لا يصل لمسار إداري**. هذا هو معيار الإنجاز
المعلن للمرحلة 1، وهو الحاجز الذي يمنع أخطر عطل في المنصة.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.deps import require_roles
from app.models.user import User, UserRole
from tests.conftest import login

ADMIN_USERS = "/api/v1/admin/users"

NEW_SPECIALIST = {
    "email": "new.specialist@example.com",
    "password": "StrongPassword123!",
    "full_name": "أخصائي جديد",
    "role": "specialist",
}


async def test_patient_is_forbidden_from_admin_route(
    client: AsyncClient, patient_user: User
) -> None:
    headers = await login(client, patient_user.email)

    response = await client.get(ADMIN_USERS, headers=headers)

    assert response.status_code == 403


async def test_specialist_is_forbidden_from_admin_route(
    client: AsyncClient, specialist_user: User
) -> None:
    headers = await login(client, specialist_user.email)

    assert (await client.get(ADMIN_USERS, headers=headers)).status_code == 403


async def test_admin_is_allowed_on_admin_route(client: AsyncClient, admin_user: User) -> None:
    headers = await login(client, admin_user.email)

    response = await client.get(ADMIN_USERS, headers=headers)

    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_admin_route_without_token_is_unauthorized(client: AsyncClient) -> None:
    """401 لغياب الهوية و403 لنقص الصلاحية — تمييز مقصود بينهما."""
    assert (await client.get(ADMIN_USERS)).status_code == 401


async def test_patient_cannot_create_a_specialist(client: AsyncClient, patient_user: User) -> None:
    headers = await login(client, patient_user.email)

    assert (await client.post(ADMIN_USERS, json=NEW_SPECIALIST, headers=headers)).status_code == 403


async def test_admin_can_create_a_specialist(client: AsyncClient, admin_user: User) -> None:
    headers = await login(client, admin_user.email)

    response = await client.post(ADMIN_USERS, json=NEW_SPECIALIST, headers=headers)

    assert response.status_code == 201
    assert response.json()["role"] == "specialist"


async def test_created_specialist_can_log_in(client: AsyncClient, admin_user: User) -> None:
    admin_headers = await login(client, admin_user.email)
    await client.post(ADMIN_USERS, json=NEW_SPECIALIST, headers=admin_headers)

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": NEW_SPECIALIST["email"], "password": NEW_SPECIALIST["password"]},
    )

    assert response.status_code == 200


async def test_admin_cannot_create_a_patient_through_the_staff_route(
    client: AsyncClient, admin_user: User
) -> None:
    """المسار مخصص لحسابات الطاقم — المرضى يسجّلون بأنفسهم."""
    headers = await login(client, admin_user.email)

    response = await client.post(
        ADMIN_USERS, json={**NEW_SPECIALIST, "role": "patient"}, headers=headers
    )

    assert response.status_code == 422


async def test_deactivated_user_loses_access_immediately(
    client: AsyncClient, admin_user: User, session
) -> None:
    """الدور والحالة يُقرآن من قاعدة البيانات، لا من الرمز الموقّع."""
    headers = await login(client, admin_user.email)
    assert (await client.get(ADMIN_USERS, headers=headers)).status_code == 200

    admin_user.is_active = False
    session.add(admin_user)
    await session.merge(admin_user)
    await session.commit()

    assert (await client.get(ADMIN_USERS, headers=headers)).status_code == 401


async def test_require_roles_rejects_empty_role_list() -> None:
    with pytest.raises(ValueError, match="دورًا واحدًا"):
        require_roles()


async def test_require_roles_accepts_multiple_roles() -> None:
    dependency = require_roles(UserRole.SPECIALIST, UserRole.ADMIN)

    assert callable(dependency)
