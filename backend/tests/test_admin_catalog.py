"""إدارة القاعدة العلمية (الخطوة 10.2).

الاختبارات هنا تحرس ثلاث قواعد لا تظهر في شكل المسارات: المحتوى يُعطَّل
ولا يُحذف، وإصدار المحتوى يتحرك مع المضمون فقط، والمراجعة لا تُسجَّل بلا
مراجِع ومرجع (ADR-003).
"""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditAction, AuditLog
from app.models.catalog import Food, FoodAllergenLink
from app.models.user import User
from tests.conftest import login

pytestmark = pytest.mark.asyncio

CATALOG = "/api/v1/admin/catalog"

FOOD = {
    "name_ar": "عدس مطبوخ",
    "name_en": "Cooked lentils",
    "category": "legumes",
    "calories_per_100g": "116",
    "protein_g": "9",
    "carbs_g": "20",
    "fat_g": "0.4",
    "fiber_g": "7.9",
    "allergens": [],
    "is_active": True,
}

EXERCISE = {
    "name_ar": "قرفصاء بوزن الجسم",
    "name_en": "Bodyweight squat",
    "slug": "bodyweight-squat",
    "category": "strength",
    "difficulty": "beginner",
    "primary_region": "knee",
    "target_muscles": ["quadriceps", "glutes"],
    "equipment": [],
    "instructions_ar": "قف بعرض الكتفين وانزل حتى موازاة الفخذ للأرض.",
    "video_url": None,
    "is_active": True,
}

INJURY = {
    "name_ar": "التهاب اللفافة الأخمصية",
    "name_en": "Plantar fasciitis",
    "slug": "plantar-fasciitis",
    "body_region": "foot",
    "description_ar": "ألم أسفل القدم يزيد مع أول خطوات الصباح.",
    "phases": [{"phase": 1, "name_ar": "تهدئة", "typical_duration_days": 14}],
    "is_active": True,
}


# ----------------------------------------------------------------- الأغذية
async def test_food_create_update_and_deactivate(
    client: AsyncClient, session: AsyncSession, admin_user: User
) -> None:
    headers = await login(client, admin_user.email)

    created = await client.post(f"{CATALOG}/foods", headers=headers, json=FOOD)
    assert created.status_code == 201, created.text
    food_id = created.json()["id"]
    assert created.json()["source"] == "admin"

    listed = await client.get(f"{CATALOG}/foods?search=عدس", headers=headers)
    assert [row["id"] for row in listed.json()] == [food_id]

    updated = await client.patch(
        f"{CATALOG}/foods/{food_id}",
        headers=headers,
        json={**FOOD, "protein_g": "9.5", "allergens": ["gluten"], "is_active": False},
    )
    assert updated.status_code == 200
    assert updated.json()["allergens"] == ["gluten"]
    assert updated.json()["is_active"] is False

    # التعطيل لا يحذف: الخطط المولَّدة تشير إلى هذا الصنف.
    still_there = await session.get(Food, uuid.UUID(food_id))
    assert still_there is not None

    only_active = await client.get(f"{CATALOG}/foods?is_active=true", headers=headers)
    assert food_id not in [row["id"] for row in only_active.json()]


async def test_food_allergens_are_replaced_not_appended(
    client: AsyncClient, session: AsyncSession, admin_user: User
) -> None:
    headers = await login(client, admin_user.email)
    created = await client.post(
        f"{CATALOG}/foods", headers=headers, json={**FOOD, "allergens": ["gluten", "dairy"]}
    )
    food_id = created.json()["id"]

    await client.patch(
        f"{CATALOG}/foods/{food_id}", headers=headers, json={**FOOD, "allergens": ["dairy"]}
    )

    links = list(
        await session.scalars(
            select(FoodAllergenLink).where(FoodAllergenLink.food_id == uuid.UUID(food_id))
        )
    )
    assert [link.allergen.value for link in links] == ["dairy"]


async def test_food_rejects_impossible_macros(client: AsyncClient, admin_user: User) -> None:
    headers = await login(client, admin_user.email)
    refused = await client.post(
        f"{CATALOG}/foods", headers=headers, json={**FOOD, "protein_g": "160"}
    )
    assert refused.status_code == 422


# ---------------------------------------------------------------- التمارين
async def test_exercise_version_moves_with_science_only(
    client: AsyncClient, admin_user: User
) -> None:
    headers = await login(client, admin_user.email)

    created = await client.post(f"{CATALOG}/exercises", headers=headers, json=EXERCISE)
    assert created.status_code == 201, created.text
    exercise_id = created.json()["id"]
    assert created.json()["review"]["content_version"] == 1
    assert created.json()["review"]["is_reviewed"] is False

    # تصحيح اسم: عرض لا مضمون.
    renamed = await client.patch(
        f"{CATALOG}/exercises/{exercise_id}",
        headers=headers,
        json={**EXERCISE, "name_ar": "قرفصاء بوزن الجسم (تصحيح)"},
    )
    assert renamed.json()["review"]["content_version"] == 1

    # تغيير التعليمات: مضمون علمي.
    changed = await client.patch(
        f"{CATALOG}/exercises/{exercise_id}",
        headers=headers,
        json={**EXERCISE, "instructions_ar": "انزل حتى زاوية 90 درجة فقط عند وجود ألم رضفي."},
    )
    assert changed.json()["review"]["content_version"] == 2

    moved = await client.patch(
        f"{CATALOG}/exercises/{exercise_id}",
        headers=headers,
        json={**EXERCISE, "primary_region": "hip"},
    )
    assert moved.json()["review"]["content_version"] == 3


async def test_duplicate_slug_is_a_clear_conflict(client: AsyncClient, admin_user: User) -> None:
    headers = await login(client, admin_user.email)
    assert (
        await client.post(f"{CATALOG}/exercises", headers=headers, json=EXERCISE)
    ).status_code == 201

    duplicate = await client.post(
        f"{CATALOG}/exercises", headers=headers, json={**EXERCISE, "name_ar": "اسم آخر"}
    )
    assert duplicate.status_code == 409
    assert "slug" in duplicate.json()["detail"]


async def test_slug_must_be_url_safe(client: AsyncClient, admin_user: User) -> None:
    headers = await login(client, admin_user.email)
    refused = await client.post(
        f"{CATALOG}/exercises", headers=headers, json={**EXERCISE, "slug": "قرفصاء بوزن"}
    )
    assert refused.status_code == 422


# ----------------------------------------------------------- أنواع الإصابات
async def test_injury_type_lifecycle_and_patient_visibility(
    client: AsyncClient, admin_user: User, patient_user: User
) -> None:
    admin_headers = await login(client, admin_user.email)
    patient_headers = await login(client, patient_user.email)

    created = await client.post(f"{CATALOG}/injury-types", headers=admin_headers, json=INJURY)
    assert created.status_code == 201, created.text
    injury_id = created.json()["id"]

    # المريض يرى المفعَّل في قائمة الاختيار.
    visible = await client.get("/api/v1/catalog/injury-types", headers=patient_headers)
    assert injury_id in [row["id"] for row in visible.json()]

    await client.patch(
        f"{CATALOG}/injury-types/{injury_id}",
        headers=admin_headers,
        json={**INJURY, "is_active": False},
    )
    hidden = await client.get("/api/v1/catalog/injury-types", headers=patient_headers)
    assert injury_id not in [row["id"] for row in hidden.json()]


async def test_injury_phase_change_bumps_the_version(client: AsyncClient, admin_user: User) -> None:
    headers = await login(client, admin_user.email)
    created = await client.post(f"{CATALOG}/injury-types", headers=headers, json=INJURY)
    injury_id = created.json()["id"]

    same = await client.patch(
        f"{CATALOG}/injury-types/{injury_id}",
        headers=headers,
        json={**INJURY, "description_ar": "وصف أوضح لنفس البروتوكول."},
    )
    assert same.json()["review"]["content_version"] == 1

    protocol = await client.patch(
        f"{CATALOG}/injury-types/{injury_id}",
        headers=headers,
        json={
            **INJURY,
            "phases": [
                {"phase": 1, "name_ar": "تهدئة", "typical_duration_days": 10},
                {"phase": 2, "name_ar": "تقوية", "typical_duration_days": 21},
            ],
        },
    )
    assert protocol.json()["review"]["content_version"] == 2


# ---------------------------------------------------------------- المراجعة
async def test_review_requires_a_reviewer_and_a_source(
    client: AsyncClient, admin_user: User
) -> None:
    headers = await login(client, admin_user.email)
    created = await client.post(f"{CATALOG}/injury-types", headers=headers, json=INJURY)
    injury_id = created.json()["id"]

    for payload in ({"reviewed_by": "د. أحمد"}, {"source_reference": "JOSPT 2023"}, {}):
        refused = await client.post(
            f"{CATALOG}/injury-types/{injury_id}/review", headers=headers, json=payload
        )
        assert refused.status_code == 422

    accepted = await client.post(
        f"{CATALOG}/injury-types/{injury_id}/review",
        headers=headers,
        json={"reviewed_by": "د. أحمد سالم — أخصائي علاج طبيعي", "source_reference": "JOSPT 2023"},
    )
    assert accepted.status_code == 200
    review = accepted.json()["review"]
    assert review["is_reviewed"] is True
    assert review["reviewed_at"] is not None
    assert review["source_reference"] == "JOSPT 2023"


async def test_unreviewed_filter_and_stats_agree(client: AsyncClient, admin_user: User) -> None:
    headers = await login(client, admin_user.email)
    created = await client.post(f"{CATALOG}/exercises", headers=headers, json=EXERCISE)
    exercise_id = created.json()["id"]

    unreviewed = await client.get(f"{CATALOG}/exercises?unreviewed=true", headers=headers)
    assert [row["id"] for row in unreviewed.json()] == [exercise_id]

    stats = (await client.get("/api/v1/admin/stats", headers=headers)).json()
    assert stats["catalog_unreviewed"] == 1
    assert stats["catalog_exercises"] == 1

    await client.post(
        f"{CATALOG}/exercises/{exercise_id}/review",
        headers=headers,
        json={"reviewed_by": "د. سارة", "source_reference": "NSCA guidelines"},
    )

    after = (await client.get("/api/v1/admin/stats", headers=headers)).json()
    assert after["catalog_unreviewed"] == 0
    assert (await client.get(f"{CATALOG}/exercises?unreviewed=true", headers=headers)).json() == []


# ------------------------------------------------------- الصلاحيات والتدقيق
async def test_catalog_management_is_admin_only(
    client: AsyncClient, specialist_user: User, patient_user: User
) -> None:
    for user in (specialist_user, patient_user):
        headers = await login(client, user.email)
        assert (await client.get(f"{CATALOG}/foods", headers=headers)).status_code == 403
        assert (
            await client.post(f"{CATALOG}/exercises", headers=headers, json=EXERCISE)
        ).status_code == 403


async def test_catalog_changes_are_audited(
    client: AsyncClient, session: AsyncSession, admin_user: User
) -> None:
    headers = await login(client, admin_user.email)
    created = await client.post(f"{CATALOG}/exercises", headers=headers, json=EXERCISE)
    exercise_id = created.json()["id"]
    await client.patch(
        f"{CATALOG}/exercises/{exercise_id}",
        headers=headers,
        json={**EXERCISE, "difficulty": "intermediate"},
    )
    await client.post(
        f"{CATALOG}/exercises/{exercise_id}/review",
        headers=headers,
        json={"reviewed_by": "د. سارة", "source_reference": "NSCA"},
    )

    entries = list(
        await session.scalars(select(AuditLog).where(AuditLog.entity_type == "exercise"))
    )
    actions = [entry.action for entry in entries]
    assert AuditAction.CATALOG_CREATED.value in actions
    assert AuditAction.CATALOG_UPDATED.value in actions
    assert AuditAction.CATALOG_REVIEWED.value in actions
    # كل سطر يحمل معرّف العنصر — سطر إنشاء بلا معرّف لا يمكن تتبّعه.
    assert all(entry.entity_id == exercise_id for entry in entries)

    update = next(entry for entry in entries if entry.action == AuditAction.CATALOG_UPDATED.value)
    assert update.after is not None
    assert update.after["scientific_change"] is True


async def test_updating_a_missing_item_is_404(client: AsyncClient, admin_user: User) -> None:
    headers = await login(client, admin_user.email)
    response = await client.patch(f"{CATALOG}/foods/{uuid.uuid4()}", headers=headers, json=FOOD)
    assert response.status_code == 404
