"""اختبارات العزل بين المرضى (خطوة 5.6).

أخطر ثغرة في نظام صحي ليست كسر كلمة سر، بل **تسريب أفقي**: مستخدم مصادَق
عليه يقرأ سجل مريض آخر بتغيير معرّف في الرابط. المصادقة وحدها لا تمنعه —
كل مسار يقرأ بيانات مريض يحتاج فحصًا خاصًا، وهذه الاختبارات هي ما يثبت
وجوده في كل مسار على حدة.
"""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.care_team import SpecialistPatient
from app.models.user import User, UserRole
from tests.conftest import TEST_PASSWORD, SessionFactory, login
from tests.test_plan_workflow import assign_specialist, onboard_patient


async def make_other_patient(email: str = "other.patient@example.com") -> User:
    async with SessionFactory() as session:
        user = User(
            email=email,
            password_hash=hash_password(TEST_PASSWORD),
            full_name="مريض آخر",
            role=UserRole.PATIENT,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


# ------------------------------------------------- مريض ضد مريض
async def test_patient_cannot_read_another_patients_plan(
    client: AsyncClient, patient_user: User, specialist_user: User, session: AsyncSession
) -> None:
    owner_headers = await onboard_patient(client, patient_user, session)
    await assign_specialist(session, specialist_user, patient_user)
    plan_id = (await client.post("/api/v1/plans/generate", json={}, headers=owner_headers)).json()[
        "id"
    ]
    reviewer = await login(client, specialist_user.email)
    await client.post(f"/api/v1/plans/{plan_id}/submit", headers=owner_headers)
    await client.post(f"/api/v1/plans/{plan_id}/approve", json={}, headers=reviewer)
    await client.post(f"/api/v1/plans/{plan_id}/activate", headers=reviewer)

    intruder = await make_other_patient()
    intruder_headers = await login(client, intruder.email)

    response = await client.get(f"/api/v1/plans/{plan_id}", headers=intruder_headers)

    assert response.status_code == 404


async def test_patient_cannot_submit_another_patients_plan(
    client: AsyncClient, patient_user: User, session: AsyncSession
) -> None:
    owner_headers = await onboard_patient(client, patient_user, session)
    plan_id = (await client.post("/api/v1/plans/generate", json={}, headers=owner_headers)).json()[
        "id"
    ]

    intruder = await make_other_patient()
    intruder_headers = await login(client, intruder.email)

    response = await client.post(f"/api/v1/plans/{plan_id}/submit", headers=intruder_headers)

    assert response.status_code == 404


async def test_patient_cannot_generate_a_plan_for_someone_else(
    client: AsyncClient, patient_user: User, session: AsyncSession
) -> None:
    await onboard_patient(client, patient_user, session)
    intruder = await make_other_patient()
    intruder_headers = await login(client, intruder.email)

    response = await client.post(
        f"/api/v1/plans/generate?patient_id={patient_user.id}",
        json={},
        headers=intruder_headers,
    )

    assert response.status_code == 404


async def test_patient_plan_list_shows_only_their_own(
    client: AsyncClient, patient_user: User, specialist_user: User, session: AsyncSession
) -> None:
    owner_headers = await onboard_patient(client, patient_user, session)
    await assign_specialist(session, specialist_user, patient_user)
    plan_id = (await client.post("/api/v1/plans/generate", json={}, headers=owner_headers)).json()[
        "id"
    ]
    reviewer = await login(client, specialist_user.email)
    await client.post(f"/api/v1/plans/{plan_id}/submit", headers=owner_headers)
    await client.post(f"/api/v1/plans/{plan_id}/approve", json={}, headers=reviewer)
    await client.post(f"/api/v1/plans/{plan_id}/activate", headers=reviewer)

    intruder = await make_other_patient()
    intruder_headers = await login(client, intruder.email)

    assert (await client.get("/api/v1/me/plans", headers=intruder_headers)).json() == []


# ------------------------------------------ أخصائي غير مسنَد
@pytest.mark.parametrize(
    "path_template",
    [
        "/api/v1/specialist/patients/{patient_id}/injuries",
        "/api/v1/specialist/patients/{patient_id}/readings",
        "/api/v1/specialist/patients/{patient_id}/plans",
    ],
)
async def test_unassigned_specialist_is_blocked_from_every_patient_route(
    client: AsyncClient,
    patient_user: User,
    specialist_user: User,
    session: AsyncSession,
    path_template: str,
) -> None:
    """الأخصائي يرى مرضاه المسنَدين فقط — لا كل مرضى المنصة."""
    await onboard_patient(client, patient_user, session)
    headers = await login(client, specialist_user.email)

    response = await client.get(path_template.format(patient_id=patient_user.id), headers=headers)

    assert response.status_code == 404


async def test_assignment_grants_access(
    client: AsyncClient, patient_user: User, specialist_user: User, session: AsyncSession
) -> None:
    await onboard_patient(client, patient_user, session)
    await assign_specialist(session, specialist_user, patient_user)
    headers = await login(client, specialist_user.email)

    response = await client.get(
        f"/api/v1/specialist/patients/{patient_user.id}/readings", headers=headers
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_ending_an_assignment_revokes_access(
    client: AsyncClient, patient_user: User, specialist_user: User, session: AsyncSession
) -> None:
    """إنهاء الإسناد يقطع الوصول فورًا، لا عند انتهاء الرمز."""
    await onboard_patient(client, patient_user, session)
    await assign_specialist(session, specialist_user, patient_user)
    headers = await login(client, specialist_user.email)
    assert (
        await client.get(f"/api/v1/specialist/patients/{patient_user.id}/readings", headers=headers)
    ).status_code == 200

    assignment = await session.get(SpecialistPatient, (specialist_user.id, patient_user.id))
    assert assignment is not None
    assignment.is_active = False
    await session.commit()

    response = await client.get(
        f"/api/v1/specialist/patients/{patient_user.id}/readings", headers=headers
    )

    assert response.status_code == 404


async def test_specialist_patient_list_excludes_unassigned(
    client: AsyncClient, patient_user: User, specialist_user: User, session: AsyncSession
) -> None:
    await onboard_patient(client, patient_user, session)
    await make_other_patient()
    await assign_specialist(session, specialist_user, patient_user)
    headers = await login(client, specialist_user.email)

    patients = (await client.get("/api/v1/specialist/patients", headers=headers)).json()

    assert [p["email"] for p in patients] == [patient_user.email]


async def test_review_queue_excludes_unassigned_patients(
    client: AsyncClient, patient_user: User, specialist_user: User, session: AsyncSession
) -> None:
    owner_headers = await onboard_patient(client, patient_user, session)
    plan_id = (await client.post("/api/v1/plans/generate", json={}, headers=owner_headers)).json()[
        "id"
    ]
    await client.post(f"/api/v1/plans/{plan_id}/submit", headers=owner_headers)
    headers = await login(client, specialist_user.email)

    assert (await client.get("/api/v1/specialist/review-queue", headers=headers)).json() == []

    await assign_specialist(session, specialist_user, patient_user)
    queue = (await client.get("/api/v1/specialist/review-queue", headers=headers)).json()

    assert [entry["id"] for entry in queue] == [plan_id]


# --------------------------------------------------------- المدير
async def test_admin_reaches_any_patient(
    client: AsyncClient, patient_user: User, admin_user: User, session: AsyncSession
) -> None:
    await onboard_patient(client, patient_user, session)
    headers = await login(client, admin_user.email)

    response = await client.get(
        f"/api/v1/specialist/patients/{patient_user.id}/readings", headers=headers
    )

    assert response.status_code == 200


async def test_patient_is_blocked_from_specialist_routes(
    client: AsyncClient, patient_user: User, session: AsyncSession
) -> None:
    headers = await onboard_patient(client, patient_user, session)

    assert (await client.get("/api/v1/specialist/patients", headers=headers)).status_code == 403


# ------------------------------------------------------ معرّفات غير موجودة
async def test_unknown_plan_id_returns_not_found(
    client: AsyncClient, patient_user: User, session: AsyncSession
) -> None:
    headers = await onboard_patient(client, patient_user, session)

    response = await client.get(f"/api/v1/plans/{uuid.uuid4()}", headers=headers)

    assert response.status_code == 404


async def test_unknown_patient_id_looks_the_same_as_a_forbidden_one(
    client: AsyncClient, specialist_user: User, patient_user: User, session: AsyncSession
) -> None:
    """404 موحّد: الرد المختلف يكشف أي المعرّفات موجود فعلًا."""
    await onboard_patient(client, patient_user, session)
    headers = await login(client, specialist_user.email)

    unknown = await client.get(
        f"/api/v1/specialist/patients/{uuid.uuid4()}/readings", headers=headers
    )
    forbidden = await client.get(
        f"/api/v1/specialist/patients/{patient_user.id}/readings", headers=headers
    )

    assert unknown.status_code == forbidden.status_code == 404
    assert unknown.json() == forbidden.json()
