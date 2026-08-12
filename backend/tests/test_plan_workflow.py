"""اختبارات المسار الكامل: من الملف الشخصي إلى خطة مفعّلة.

معيار الإنجاز المعلن للمرحلة 5 مُختبَر هنا صراحةً: **خطة بحالة مسودة أو
قيد المراجعة لا يمكن لأي مسار أن يرجّعها للمريض**.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import Allergen, FoodCategory, PlanStatus
from app.models.care_team import SpecialistPatient
from app.models.catalog import Food, FoodAllergenLink
from app.models.plan import Plan
from app.models.user import User
from tests.conftest import login

TODAY = date.today()

PROFILE_PAYLOAD = {
    "birth_date": "1994-03-15",
    "gender": "male",
    "height_cm": "178.0",
    "activity_level": "moderate",
    "goal": "weight_loss",
    "allergens": [],
}

PANTRY = [
    ("chicken", "صدور دجاج", FoodCategory.PROTEIN, 165, 31, 0, 3.6, None),
    ("rice", "أرز أبيض", FoodCategory.GRAINS, 130, 2.7, 28, 0.3, None),
    ("olive-oil", "زيت زيتون", FoodCategory.FATS, 884, 0, 0, 100, None),
    ("yoghurt", "زبادي", FoodCategory.DAIRY, 61, 3.5, 4.7, 3.3, Allergen.DAIRY),
    ("bread", "عيش بلدي", FoodCategory.GRAINS, 250, 8, 50, 1.5, Allergen.GLUTEN),
]


async def seed_pantry(session: AsyncSession) -> None:
    for _slug, name, category, kcal, protein, carbs, fat, allergen in PANTRY:
        food = Food(
            name_ar=name,
            category=category,
            calories_per_100g=Decimal(str(kcal)),
            protein_g=Decimal(str(protein)),
            carbs_g=Decimal(str(carbs)),
            fat_g=Decimal(str(fat)),
        )
        session.add(food)
        await session.flush()
        if allergen is not None:
            session.add(FoodAllergenLink(food_id=food.id, allergen=allergen))
    await session.commit()


async def onboard_patient(
    client: AsyncClient,
    patient: User,
    session: AsyncSession,
    *,
    allergens: list[str] | None = None,
    weight: str = "92.0",
) -> dict[str, str]:
    """يجهّز مريضًا كاملًا: ملف شخصي + موافقة + وزن + أطعمة متاحة."""
    await seed_pantry(session)
    headers = await login(client, patient.email)

    payload = {**PROFILE_PAYLOAD, "allergens": allergens or []}
    response = await client.put("/api/v1/me/profile", json=payload, headers=headers)
    assert response.status_code == 200, response.text

    await client.post("/api/v1/me/profile/consent", headers=headers)
    await client.post(
        "/api/v1/me/readings",
        json={"reading_date": TODAY.isoformat(), "weight_kg": weight},
        headers=headers,
    )
    return headers


async def assign_specialist(session: AsyncSession, specialist: User, patient: User) -> None:
    session.add(SpecialistPatient(specialist_id=specialist.id, patient_id=patient.id))
    await session.commit()


# ------------------------------------------------------- الملف الشخصي
async def test_profile_is_required_before_generating_a_plan(
    client: AsyncClient, patient_user: User, session: AsyncSession
) -> None:
    await seed_pantry(session)
    headers = await login(client, patient_user.email)

    response = await client.post("/api/v1/plans/generate", json={}, headers=headers)

    assert response.status_code == 422
    assert "الملف الشخصي" in response.json()["detail"]


async def test_consent_is_required_before_generating_a_plan(
    client: AsyncClient, patient_user: User, session: AsyncSession
) -> None:
    """شرط قانوني: لا خطة قبل الموافقة على التنبيه الطبي."""
    await seed_pantry(session)
    headers = await login(client, patient_user.email)
    await client.put("/api/v1/me/profile", json=PROFILE_PAYLOAD, headers=headers)
    await client.post(
        "/api/v1/me/readings",
        json={"reading_date": TODAY.isoformat(), "weight_kg": "92.0"},
        headers=headers,
    )

    response = await client.post("/api/v1/plans/generate", json={}, headers=headers)

    assert response.status_code == 422
    assert "التنبيه الطبي" in response.json()["detail"]


async def test_weight_is_required_before_generating_a_plan(
    client: AsyncClient, patient_user: User, session: AsyncSession
) -> None:
    await seed_pantry(session)
    headers = await login(client, patient_user.email)
    await client.put("/api/v1/me/profile", json=PROFILE_PAYLOAD, headers=headers)
    await client.post("/api/v1/me/profile/consent", headers=headers)

    response = await client.post("/api/v1/plans/generate", json={}, headers=headers)

    assert response.status_code == 422
    assert "وزن" in response.json()["detail"]


async def test_profile_returns_computed_age(
    client: AsyncClient, patient_user: User, session: AsyncSession
) -> None:
    headers = await onboard_patient(client, patient_user, session)

    body = (await client.get("/api/v1/me/profile", headers=headers)).json()

    assert body["age_years"] == TODAY.year - 1994 - (
        0 if (TODAY.month, TODAY.day) >= (3, 15) else 1
    )


async def test_updating_allergens_replaces_them_entirely(
    client: AsyncClient, patient_user: User, session: AsyncSession
) -> None:
    """الدمج التراكمي يُبقي حساسية أزالها المستخدم."""
    headers = await onboard_patient(client, patient_user, session, allergens=["gluten", "dairy"])

    await client.put(
        "/api/v1/me/profile", json={**PROFILE_PAYLOAD, "allergens": ["peanuts"]}, headers=headers
    )
    body = (await client.get("/api/v1/me/profile", headers=headers)).json()

    assert body["allergens"] == ["peanuts"]


# ---------------------------------------------------------------- التوليد
async def test_generated_plan_starts_as_a_draft(
    client: AsyncClient, patient_user: User, session: AsyncSession
) -> None:
    headers = await onboard_patient(client, patient_user, session)

    response = await client.post("/api/v1/plans/generate", json={}, headers=headers)

    assert response.status_code == 201
    assert response.json()["status"] == PlanStatus.DRAFT.value


async def test_generated_plan_carries_the_engine_version_and_targets(
    client: AsyncClient, patient_user: User, session: AsyncSession
) -> None:
    headers = await onboard_patient(client, patient_user, session)

    body = (await client.post("/api/v1/plans/generate", json={}, headers=headers)).json()

    assert body["rule_engine_version"].count(".") == 2
    assert body["nutrition"]["daily_calories"] >= 1500  # أرضية الذكور
    assert body["meals"], "الخطة بلا وجبات لا تفيد المريض"


async def test_generated_plan_never_serves_an_allergen(
    client: AsyncClient, patient_user: User, session: AsyncSession
) -> None:
    """الاختبار الأهم في مسار التوليد."""
    headers = await onboard_patient(client, patient_user, session, allergens=["gluten", "dairy"])

    body = (await client.post("/api/v1/plans/generate", json={}, headers=headers)).json()

    served = {item["name_ar"] for meal in body["meals"] for item in meal["items"]}
    assert "عيش بلدي" not in served
    assert "زبادي" not in served


# ------------------------------------------- المريض لا يرى ما لم يُعتمد ⭐
async def test_patient_cannot_list_an_unapproved_plan(
    client: AsyncClient, patient_user: User, session: AsyncSession
) -> None:
    headers = await onboard_patient(client, patient_user, session)
    await client.post("/api/v1/plans/generate", json={}, headers=headers)

    visible = (await client.get("/api/v1/me/plans", headers=headers)).json()

    assert visible == []


@pytest.mark.parametrize("hidden_status", [PlanStatus.DRAFT, PlanStatus.PENDING_REVIEW])
async def test_patient_cannot_read_an_unapproved_plan_by_id(
    client: AsyncClient,
    patient_user: User,
    specialist_user: User,
    session: AsyncSession,
    hidden_status: PlanStatus,
) -> None:
    """معيار الإنجاز: 404 لا 403 — لا نؤكد حتى وجود الخطة."""
    headers = await onboard_patient(client, patient_user, session)
    plan_id = (await client.post("/api/v1/plans/generate", json={}, headers=headers)).json()["id"]

    if hidden_status is PlanStatus.PENDING_REVIEW:
        await client.post(f"/api/v1/plans/{plan_id}/submit", headers=headers)

    response = await client.get(f"/api/v1/plans/{plan_id}", headers=headers)

    assert response.status_code == 404


async def test_patient_sees_the_plan_only_after_activation(
    client: AsyncClient, patient_user: User, specialist_user: User, session: AsyncSession
) -> None:
    headers = await onboard_patient(client, patient_user, session)
    await assign_specialist(session, specialist_user, patient_user)
    plan_id = (await client.post("/api/v1/plans/generate", json={}, headers=headers)).json()["id"]
    reviewer = await login(client, specialist_user.email)

    await client.post(f"/api/v1/plans/{plan_id}/submit", headers=headers)
    assert (await client.get("/api/v1/me/plans", headers=headers)).json() == []

    await client.post(f"/api/v1/plans/{plan_id}/approve", json={}, headers=reviewer)
    assert (
        await client.get("/api/v1/me/plans", headers=headers)
    ).json() == [], "الاعتماد وحده لا يكفي — التفعيل هو ما يجعلها مرئية"

    await client.post(f"/api/v1/plans/{plan_id}/activate", headers=reviewer)
    visible = (await client.get("/api/v1/me/plans", headers=headers)).json()

    assert len(visible) == 1
    assert visible[0]["status"] == PlanStatus.ACTIVE.value


# ------------------------------------------------------------ دورة الاعتماد
async def test_specialist_cannot_approve_a_draft_directly(
    client: AsyncClient, patient_user: User, specialist_user: User, session: AsyncSession
) -> None:
    """القفز فوق المراجعة يرفضه trigger قاعدة البيانات."""
    headers = await onboard_patient(client, patient_user, session)
    await assign_specialist(session, specialist_user, patient_user)
    plan_id = (await client.post("/api/v1/plans/generate", json={}, headers=headers)).json()["id"]
    reviewer = await login(client, specialist_user.email)

    response = await client.post(f"/api/v1/plans/{plan_id}/approve", json={}, headers=reviewer)

    assert response.status_code == 409


async def test_patient_cannot_approve_their_own_plan(
    client: AsyncClient, patient_user: User, session: AsyncSession
) -> None:
    headers = await onboard_patient(client, patient_user, session)
    plan_id = (await client.post("/api/v1/plans/generate", json={}, headers=headers)).json()["id"]
    await client.post(f"/api/v1/plans/{plan_id}/submit", headers=headers)

    response = await client.post(f"/api/v1/plans/{plan_id}/approve", json={}, headers=headers)

    assert response.status_code == 403


async def test_requesting_changes_needs_a_reason(
    client: AsyncClient, patient_user: User, specialist_user: User, session: AsyncSession
) -> None:
    headers = await onboard_patient(client, patient_user, session)
    await assign_specialist(session, specialist_user, patient_user)
    plan_id = (await client.post("/api/v1/plans/generate", json={}, headers=headers)).json()["id"]
    await client.post(f"/api/v1/plans/{plan_id}/submit", headers=headers)
    reviewer = await login(client, specialist_user.email)

    response = await client.post(
        f"/api/v1/plans/{plan_id}/request-changes", json={}, headers=reviewer
    )

    assert response.status_code == 422


async def test_rejection_loop_returns_the_plan_to_draft(
    client: AsyncClient, patient_user: User, specialist_user: User, session: AsyncSession
) -> None:
    headers = await onboard_patient(client, patient_user, session)
    await assign_specialist(session, specialist_user, patient_user)
    plan_id = (await client.post("/api/v1/plans/generate", json={}, headers=headers)).json()["id"]
    await client.post(f"/api/v1/plans/{plan_id}/submit", headers=headers)
    reviewer = await login(client, specialist_user.email)

    response = await client.post(
        f"/api/v1/plans/{plan_id}/request-changes",
        json={"reason": "السعرات أعلى مما يناسب حالته"},
        headers=reviewer,
    )

    assert response.status_code == 200
    assert response.json()["status"] == PlanStatus.CHANGES_REQUESTED.value


async def test_activating_a_new_plan_archives_the_previous_one(
    client: AsyncClient, patient_user: User, specialist_user: User, session: AsyncSession
) -> None:
    """الفهرس الفريد الجزئي يسمح بمفعّلة واحدة — الأرشفة تجعل ذلك مقصودًا."""
    headers = await onboard_patient(client, patient_user, session)
    await assign_specialist(session, specialist_user, patient_user)
    reviewer = await login(client, specialist_user.email)

    activated: list[str] = []
    for _ in range(2):
        plan_id = (await client.post("/api/v1/plans/generate", json={}, headers=headers)).json()[
            "id"
        ]
        await client.post(f"/api/v1/plans/{plan_id}/submit", headers=headers)
        await client.post(f"/api/v1/plans/{plan_id}/approve", json={}, headers=reviewer)
        response = await client.post(f"/api/v1/plans/{plan_id}/activate", headers=reviewer)
        assert response.status_code == 200, response.text
        activated.append(plan_id)

    statuses = {
        str(plan.id): plan.status
        for plan in await session.scalars(select(Plan).where(Plan.user_id == patient_user.id))
    }
    assert statuses[activated[0]] is PlanStatus.ARCHIVED
    assert statuses[activated[1]] is PlanStatus.ACTIVE


async def test_the_full_history_is_recorded(
    client: AsyncClient, patient_user: User, specialist_user: User, session: AsyncSession
) -> None:
    headers = await onboard_patient(client, patient_user, session)
    await assign_specialist(session, specialist_user, patient_user)
    plan_id = (await client.post("/api/v1/plans/generate", json={}, headers=headers)).json()["id"]
    reviewer = await login(client, specialist_user.email)

    await client.post(f"/api/v1/plans/{plan_id}/submit", headers=headers)
    await client.post(f"/api/v1/plans/{plan_id}/approve", json={}, headers=reviewer)
    await client.post(f"/api/v1/plans/{plan_id}/activate", headers=reviewer)

    history = (await client.get(f"/api/v1/plans/{plan_id}/history", headers=reviewer)).json()

    assert [entry["to_status"] for entry in history] == [
        PlanStatus.DRAFT.value,
        PlanStatus.PENDING_REVIEW.value,
        PlanStatus.APPROVED.value,
        PlanStatus.ACTIVE.value,
    ]
    assert history[2]["actor_user_id"] == str(specialist_user.id)


async def test_approved_plan_records_its_approver(
    client: AsyncClient, patient_user: User, specialist_user: User, session: AsyncSession
) -> None:
    headers = await onboard_patient(client, patient_user, session)
    await assign_specialist(session, specialist_user, patient_user)
    plan_id = (await client.post("/api/v1/plans/generate", json={}, headers=headers)).json()["id"]
    await client.post(f"/api/v1/plans/{plan_id}/submit", headers=headers)
    reviewer = await login(client, specialist_user.email)

    body = (await client.post(f"/api/v1/plans/{plan_id}/approve", json={}, headers=reviewer)).json()

    assert body["approved_at"] is not None
    assert uuid.UUID(body["id"]) == uuid.UUID(plan_id)
