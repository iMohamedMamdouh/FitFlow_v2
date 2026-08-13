"""تحميل قاعدة البداية: أطعمة وأنواع إصابات.

    python -m app.cli.seed_catalog

آمن للتكرار: المطابقة بالمعرّف الخارجي (``source`` + ``external_id``)
للأطعمة وبالـ ``slug`` لأنواع الإصابات، فالتشغيل مرتين لا يكرّر صفًا.
الصفوف الموجودة تُحدَّث بقيمها الجديدة بدل أن تُتجاهل، حتى يصل تصحيح قيمة
غذائية خاطئة إلى قاعدة بيانات قائمة.

كل ما يُحمَّل هنا **غير مراجَع علميًا** — راجع ``app/data/starter_catalogue.py``.
"""

from __future__ import annotations

import asyncio
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import SessionFactory, engine
from app.data.starter_catalogue import FOODS, INJURY_TYPES, SOURCE
from app.models.catalog import Food, FoodAllergenLink, InjuryType


async def _seed_foods(session: AsyncSession) -> tuple[int, int]:
    existing = {
        food.external_id: food
        for food in await session.scalars(select(Food).where(Food.source == SOURCE))
        if food.external_id is not None
    }
    created = updated = 0

    for item in FOODS:
        food = existing.get(item.slug)
        if food is None:
            food = Food(source=SOURCE, external_id=item.slug)
            session.add(food)
            created += 1
        else:
            updated += 1

        food.name_ar = item.name_ar
        food.name_en = item.name_en
        food.category = item.category
        food.calories_per_100g = Decimal(str(item.calories))
        food.protein_g = Decimal(str(item.protein_g))
        food.carbs_g = Decimal(str(item.carbs_g))
        food.fat_g = Decimal(str(item.fat_g))
        food.fiber_g = Decimal(str(item.fiber_g))
        food.is_active = True
        await session.flush()

        # الروابط تُستبدل بالكامل: الدمج التراكمي يُبقي مسبّب حساسية أزلناه
        # من البيانات، فيستبعد الصنف من خطط لا داعي لاستبعاده منها.
        for link in await session.scalars(
            select(FoodAllergenLink).where(FoodAllergenLink.food_id == food.id)
        ):
            await session.delete(link)
        await session.flush()
        for allergen in item.allergens:
            session.add(FoodAllergenLink(food_id=food.id, allergen=allergen))

    return created, updated


async def _seed_injury_types(session: AsyncSession) -> tuple[int, int]:
    existing = {
        injury_type.slug: injury_type for injury_type in await session.scalars(select(InjuryType))
    }
    created = updated = 0

    for item in INJURY_TYPES:
        injury_type = existing.get(item.slug)
        if injury_type is None:
            injury_type = InjuryType(slug=item.slug)
            session.add(injury_type)
            created += 1
        else:
            updated += 1

        injury_type.name_ar = item.name_ar
        injury_type.name_en = item.name_en
        injury_type.body_region = item.body_region
        injury_type.description_ar = item.description_ar
        injury_type.is_active = True
        # لا نلمس reviewed_by/reviewed_at/phases: لو راجع أخصائي نوعًا وأضاف
        # مراحله، إعادة تشغيل السكربت يجب ألا تمحو مراجعته.

    return created, updated


async def seed_catalogue() -> int:
    async with SessionFactory() as session:
        foods_created, foods_updated = await _seed_foods(session)
        types_created, types_updated = await _seed_injury_types(session)
        await session.commit()

    print(f"✓ الأطعمة: {foods_created} جديد، {foods_updated} محدَّث")
    print(f"✓ أنواع الإصابات: {types_created} جديد، {types_updated} محدَّث")
    print("⚠️  هذه قاعدة بداية غير مراجَعة علميًا — المرحلة 3 تستبدلها بمحتوى مراجَع.")
    return 0


async def _main() -> int:
    try:
        return await seed_catalogue()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
