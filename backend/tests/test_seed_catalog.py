"""اختبارات قاعدة البداية.

الغرض المعلن لهذه القاعدة أن تجعل النظام يعمل من طرف إلى طرف قبل المرحلة
3. فالاختبار الحقيقي ليس "هل حُمِّلت الصفوف" بل **هل تكفي لتوليد خطة
لمريض لديه أسوأ تركيبة حساسية ممكنة**.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cli.seed_catalog import seed_catalogue
from app.core.enums import Allergen
from app.core.rule_engine.meals import exclude_allergens
from app.data.starter_catalogue import FOODS, INJURY_TYPES
from app.models.catalog import Food, FoodAllergenLink, InjuryType
from app.services.plans import load_food_catalogue


async def test_seeding_loads_the_whole_catalogue(session: AsyncSession) -> None:
    await seed_catalogue()

    assert await session.scalar(select(func.count()).select_from(Food)) == len(FOODS)
    assert await session.scalar(select(func.count()).select_from(InjuryType)) == len(INJURY_TYPES)


async def test_seeding_twice_does_not_duplicate(session: AsyncSession) -> None:
    await seed_catalogue()
    await seed_catalogue()

    assert await session.scalar(select(func.count()).select_from(Food)) == len(FOODS)
    assert await session.scalar(select(func.count()).select_from(FoodAllergenLink)) == sum(
        len(food.allergens) for food in FOODS
    )


async def test_seeding_updates_corrected_values(session: AsyncSession) -> None:
    """تصحيح قيمة غذائية خاطئة لازم يصل لقاعدة بيانات قائمة."""
    await seed_catalogue()
    food = await session.scalar(select(Food).where(Food.external_id == "white-rice"))
    assert food is not None
    food.calories_per_100g = 1  # type: ignore[assignment]
    await session.commit()

    await seed_catalogue()
    await session.refresh(food)

    assert int(food.calories_per_100g) == 130


async def test_a_specialist_review_survives_reseeding(session: AsyncSession) -> None:
    """إعادة التشغيل لا تمحو مراجعة أخصائي — وإلا ضاعت المرحلة 3 بأمر واحد."""
    from datetime import UTC, datetime

    await seed_catalogue()
    injury_type = await session.scalar(select(InjuryType).where(InjuryType.slug == "acl-tear"))
    assert injury_type is not None
    injury_type.reviewed_by = "د. اختبار"
    injury_type.reviewed_at = datetime.now(UTC)
    await session.commit()

    await seed_catalogue()
    await session.refresh(injury_type)

    assert injury_type.is_clinically_reviewed


async def test_nothing_is_shipped_as_clinically_reviewed(session: AsyncSession) -> None:
    """ADR-003: لا محتوى علمي يُعتبر مراجَعًا بغير مراجعة بشرية فعلية."""
    await seed_catalogue()

    injury_types = list(await session.scalars(select(InjuryType)))

    assert injury_types
    assert not any(injury_type.is_clinically_reviewed for injury_type in injury_types)
    assert all(injury_type.phases == [] for injury_type in injury_types)


async def test_the_catalogue_survives_every_single_allergy(session: AsyncSession) -> None:
    """مريض حسّاس لكل شيء لازم يبقى أمامه طعام — وإلا فشل التوليد."""
    await seed_catalogue()
    catalogue = await load_food_catalogue(session)

    remaining = exclude_allergens(catalogue, frozenset(Allergen))

    assert remaining
    categories = {food.category for food in remaining}
    # المحرك يحتاج مصدر بروتين ومصدر دهون ومصدر نشويات لبناء وجبة كاملة.
    assert any(food.protein_g > 0 for food in remaining)
    assert any(food.fat_g > 0 for food in remaining)
    assert any(food.carbs_g > 0 for food in remaining)
    assert len(categories) >= 3


async def test_food_slugs_are_unique() -> None:
    assert len({food.slug for food in FOODS}) == len(FOODS)
    assert len({injury_type.slug for injury_type in INJURY_TYPES}) == len(INJURY_TYPES)


async def test_macros_fit_in_a_hundred_grams() -> None:
    """نفس القيد الموجود في قاعدة البيانات، مفحوصًا على البيانات قبل تحميلها."""
    for food in FOODS:
        assert food.protein_g + food.carbs_g + food.fat_g <= 100, food.slug
        assert 0 <= food.calories <= 950, food.slug
