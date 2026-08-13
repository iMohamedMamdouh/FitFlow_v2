"""اختبارات قيود المخطط.

كل اختبار هنا يثبت أن قاعدة البيانات **ترفض** بيانات غير منطقية. القيمة
ليست في أن الكود الحالي لا يكتبها — بل في أن أي كود مستقبلي، أو سكربت
استيراد، أو تعديل يدوي، لن يستطيع كتابتها أيضًا.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import today
from app.models.care_team import SpecialistPatient
from app.models.catalog import Exercise, ExerciseContraindication, Food, InjuryType
from app.models.clinical import DailyLog, Injury, PhysiologicalReading
from app.models.enums import (
    BodyRegion,
    ExerciseCategory,
    ExerciseDifficulty,
    FoodCategory,
    Gender,
    Goal,
    InjuryStatus,
    PlanType,
    ReadingSource,
)
from app.models.plan import NutritionPlan, Plan, PlanExercise
from app.models.profile import UserProfile
from app.models.user import User

TODAY = today()


# ------------------------------------------------------------- مصانع مساعدة
def make_food(**overrides: object) -> Food:
    defaults: dict[str, object] = {
        "name_ar": "أرز أبيض",
        "category": FoodCategory.GRAINS,
        "calories_per_100g": Decimal("130"),
        "protein_g": Decimal("2.7"),
        "carbs_g": Decimal("28"),
        "fat_g": Decimal("0.3"),
    }
    return Food(**(defaults | overrides))  # type: ignore[arg-type]


def make_injury_type(**overrides: object) -> InjuryType:
    defaults: dict[str, object] = {
        "name_ar": "قطع الرباط الصليبي الأمامي",
        "slug": f"acl-{uuid.uuid4().hex[:8]}",
        "body_region": BodyRegion.KNEE,
    }
    return InjuryType(**(defaults | overrides))  # type: ignore[arg-type]


def make_exercise(**overrides: object) -> Exercise:
    defaults: dict[str, object] = {
        "name_ar": "قرفصاء",
        "slug": f"squat-{uuid.uuid4().hex[:8]}",
        "category": ExerciseCategory.STRENGTH,
        "difficulty": ExerciseDifficulty.INTERMEDIATE,
        "primary_region": BodyRegion.KNEE,
    }
    return Exercise(**(defaults | overrides))  # type: ignore[arg-type]


def make_profile(user: User, **overrides: object) -> UserProfile:
    defaults: dict[str, object] = {
        "user_id": user.id,
        "birth_date": date(1995, 5, 20),
        "gender": Gender.MALE,
        "height_cm": Decimal("178"),
        "goal": Goal.WEIGHT_LOSS,
    }
    return UserProfile(**(defaults | overrides))  # type: ignore[arg-type]


async def _expect_rejected(session: AsyncSession, instance: object) -> None:
    session.add(instance)
    with pytest.raises((IntegrityError, DBAPIError)):
        await session.commit()
    await session.rollback()


# ------------------------------------------------------------ الملف الشخصي
async def test_valid_profile_is_accepted(session: AsyncSession, patient_user: User) -> None:
    session.add(make_profile(patient_user))
    await session.commit()

    stored = await session.get(UserProfile, patient_user.id)
    assert stored is not None
    assert stored.age_years >= 25


async def test_impossible_height_is_rejected(session: AsyncSession, patient_user: User) -> None:
    await _expect_rejected(session, make_profile(patient_user, height_cm=Decimal("300")))


async def test_future_birth_date_is_rejected(session: AsyncSession, patient_user: User) -> None:
    await _expect_rejected(
        session, make_profile(patient_user, birth_date=TODAY + timedelta(days=1))
    )


async def test_birth_date_beyond_120_years_is_rejected(
    session: AsyncSession, patient_user: User
) -> None:
    await _expect_rejected(session, make_profile(patient_user, birth_date=date(1850, 1, 1)))


# ------------------------------------------------------------------ الأغذية
async def test_macros_cannot_exceed_100g_per_100g(session: AsyncSession) -> None:
    """60 بروتين + 60 كارب في 100 جرام مستحيل فيزيائيًا."""
    await _expect_rejected(
        session, make_food(protein_g=Decimal("60"), carbs_g=Decimal("60"), fat_g=Decimal("10"))
    )


async def test_negative_calories_are_rejected(session: AsyncSession) -> None:
    await _expect_rejected(session, make_food(calories_per_100g=Decimal("-5")))


async def test_arabic_food_name_search_index_is_usable(session: AsyncSession) -> None:
    """يتحقق أن امتداد pg_trgm مفعّل وأن البحث الجزئي بالعربية يعمل."""
    session.add(make_food(name_ar="كشري مصري"))
    await session.commit()

    found = await session.scalar(
        Food.__table__.select().where(Food.name_ar.like("%كشري%")).with_only_columns(Food.name_ar)
    )
    assert found == "كشري مصري"


# ----------------------------------------------------------------- الإصابات
async def _injury_defaults(session: AsyncSession, user: User) -> dict[str, object]:
    injury_type = make_injury_type()
    session.add(injury_type)
    await session.commit()
    return {
        "user_id": user.id,
        "injury_type_id": injury_type.id,
        "injury_date": TODAY - timedelta(days=30),
        "pain_level": 5,
        "status": InjuryStatus.SUBACUTE,
    }


async def test_pain_level_above_ten_is_rejected(session: AsyncSession, patient_user: User) -> None:
    fields = await _injury_defaults(session, patient_user)
    await _expect_rejected(session, Injury(**(fields | {"pain_level": 11})))  # type: ignore[arg-type]


async def test_negative_pain_level_is_rejected(session: AsyncSession, patient_user: User) -> None:
    fields = await _injury_defaults(session, patient_user)
    await _expect_rejected(session, Injury(**(fields | {"pain_level": -1})))  # type: ignore[arg-type]


async def test_surgery_date_without_surgery_flag_is_rejected(
    session: AsyncSession, patient_user: User
) -> None:
    fields = await _injury_defaults(session, patient_user)
    await _expect_rejected(
        session,
        Injury(**(fields | {"had_surgery": False, "surgery_date": TODAY})),  # type: ignore[arg-type]
    )


async def test_surgery_before_the_injury_is_rejected(
    session: AsyncSession, patient_user: User
) -> None:
    fields = await _injury_defaults(session, patient_user)
    await _expect_rejected(
        session,
        Injury(  # type: ignore[arg-type]
            **(fields | {"had_surgery": True, "surgery_date": TODAY - timedelta(days=60)})
        ),
    )


async def test_future_injury_date_is_rejected(session: AsyncSession, patient_user: User) -> None:
    fields = await _injury_defaults(session, patient_user)
    await _expect_rejected(
        session,
        Injury(**(fields | {"injury_date": TODAY + timedelta(days=1)})),  # type: ignore[arg-type]
    )


async def test_acute_injury_blocks_resistance_training(
    session: AsyncSession, patient_user: User
) -> None:
    """الخاصية التي سيقرأها محرك القواعد في المرحلة 4 (ADR-007)."""
    fields = await _injury_defaults(session, patient_user)
    injury = Injury(**(fields | {"status": InjuryStatus.ACUTE}))  # type: ignore[arg-type]
    session.add(injury)
    await session.commit()

    assert injury.blocks_resistance_training is True
    assert injury.is_active is True


# ------------------------------------------------- سلامة الموانع المرجعية
async def test_contraindication_requires_a_real_injury_type(
    session: AsyncSession,
) -> None:
    """أخطر ثغرة محتملة: مانع يشير إلى إصابة غير موجودة فلا يُطبَّق أبدًا."""
    exercise = make_exercise()
    session.add(exercise)
    await session.commit()

    await _expect_rejected(
        session,
        ExerciseContraindication(exercise_id=exercise.id, injury_type_id=uuid.uuid4()),
    )


async def test_injury_type_in_use_cannot_be_deleted(
    session: AsyncSession, patient_user: User
) -> None:
    """RESTRICT: حذف نوع إصابة مسجَّل على مريض يفشل بدل أن يمحو إصابته."""
    fields = await _injury_defaults(session, patient_user)
    session.add(Injury(**fields))  # type: ignore[arg-type]
    await session.commit()

    injury_type = await session.get(InjuryType, fields["injury_type_id"])
    assert injury_type is not None
    await session.delete(injury_type)

    with pytest.raises(IntegrityError):
        await session.commit()
    await session.rollback()


# --------------------------------------------------------------- القياسات
async def test_duplicate_manual_reading_on_the_same_day_is_rejected(
    session: AsyncSession, patient_user: User
) -> None:
    for _ in range(2):
        session.add(
            PhysiologicalReading(
                user_id=patient_user.id,
                reading_date=TODAY,
                source=ReadingSource.MANUAL,
                weight_kg=Decimal("80"),
            )
        )
    with pytest.raises(IntegrityError):
        await session.commit()
    await session.rollback()


async def test_same_day_readings_from_different_sources_coexist(
    session: AsyncSession, patient_user: User
) -> None:
    """القيد على (المستخدم، اليوم، المصدر) — الجهاز والإدخال اليدوي لا يتعارضان."""
    session.add_all(
        [
            PhysiologicalReading(
                user_id=patient_user.id,
                reading_date=TODAY,
                source=ReadingSource.MANUAL,
                weight_kg=Decimal("80"),
            ),
            PhysiologicalReading(
                user_id=patient_user.id,
                reading_date=TODAY,
                source=ReadingSource.SMARTWATCH,
                weight_kg=Decimal("80.4"),
            ),
        ]
    )
    await session.commit()


async def test_impossible_weight_is_rejected(session: AsyncSession, patient_user: User) -> None:
    await _expect_rejected(
        session,
        PhysiologicalReading(user_id=patient_user.id, reading_date=TODAY, weight_kg=Decimal("700")),
    )


async def test_absurd_future_reading_date_is_rejected(
    session: AsyncSession, patient_user: User
) -> None:
    """القيد هنا سياج ضد القيم العبثية لا القاعدة الدقيقة.

    يوم واحد للأمام مسموح على مستوى قاعدة البيانات عمدًا: ``CURRENT_DATE``
    تاريخ خادم القاعدة (UTC)، والمنصة تعمل بتوقيت آخر، فالمنع الحرفي كان
    يرفض تسجيل المساء عند المستخدم. القاعدة الدقيقة — "لا تاريخ في مستقبل
    **المنصة**" — في طبقة التطبيق حيث يُعرف التوقيت (``tests/test_clock.py``).
    """
    await _expect_rejected(
        session,
        PhysiologicalReading(
            user_id=patient_user.id,
            reading_date=TODAY + timedelta(days=2),
            weight_kg=Decimal("80"),
        ),
    )


# ------------------------------------------------------------ التسجيل اليومي
async def test_only_one_daily_log_per_day(session: AsyncSession, patient_user: User) -> None:
    session.add_all(
        [
            DailyLog(user_id=patient_user.id, log_date=TODAY, pain_level=3),
            DailyLog(user_id=patient_user.id, log_date=TODAY, pain_level=4),
        ]
    )
    with pytest.raises(IntegrityError):
        await session.commit()
    await session.rollback()


async def test_adherence_above_100_percent_is_rejected(
    session: AsyncSession, patient_user: User
) -> None:
    await _expect_rejected(
        session,
        DailyLog(user_id=patient_user.id, log_date=TODAY, diet_adherence_pct=120),
    )


# ------------------------------------------------- الحد الأدنى للسعرات
async def _make_plan(session: AsyncSession, user: User) -> Plan:
    plan = Plan(user_id=user.id, plan_type=PlanType.NUTRITION, rule_engine_version="0.1.0")
    session.add(plan)
    await session.commit()
    return plan


async def test_starvation_calories_are_rejected_by_the_database(
    session: AsyncSession, patient_user: User
) -> None:
    """حاجز ADR-007 الأخير: لا خطة تحت 1200 سعرة مهما كان مصدر الكتابة."""
    plan = await _make_plan(session, patient_user)

    await _expect_rejected(
        session,
        NutritionPlan(
            plan_id=plan.id,
            daily_calories=800,
            protein_g=Decimal("60"),
            carbs_g=Decimal("80"),
            fat_g=Decimal("25"),
        ),
    )


async def test_calories_at_the_floor_are_accepted(
    session: AsyncSession, patient_user: User
) -> None:
    plan = await _make_plan(session, patient_user)
    session.add(
        NutritionPlan(
            plan_id=plan.id,
            daily_calories=1200,
            protein_g=Decimal("90"),
            carbs_g=Decimal("120"),
            fat_g=Decimal("40"),
        )
    )
    await session.commit()


async def test_absurdly_high_calories_are_rejected(
    session: AsyncSession, patient_user: User
) -> None:
    plan = await _make_plan(session, patient_user)
    await _expect_rejected(
        session,
        NutritionPlan(
            plan_id=plan.id,
            daily_calories=9000,
            protein_g=Decimal("90"),
            carbs_g=Decimal("120"),
            fat_g=Decimal("40"),
        ),
    )


# ------------------------------------------------------------ تمارين الخطة
async def test_exercise_without_reps_or_duration_is_rejected(
    session: AsyncSession, patient_user: User
) -> None:
    """تمرين بلا تكرارات ولا مدة لا يمكن للمريض تنفيذه."""
    plan = await _make_plan(session, patient_user)
    exercise = make_exercise()
    session.add(exercise)
    await session.commit()

    await _expect_rejected(
        session,
        PlanExercise(
            plan_id=plan.id, exercise_id=exercise.id, sets=3, reps=None, duration_seconds=None
        ),
    )


async def test_exercise_with_duration_only_is_accepted(
    session: AsyncSession, patient_user: User
) -> None:
    plan = await _make_plan(session, patient_user)
    exercise = make_exercise(category=ExerciseCategory.STRETCHING)
    session.add(exercise)
    await session.commit()

    session.add(PlanExercise(plan_id=plan.id, exercise_id=exercise.id, sets=3, duration_seconds=30))
    await session.commit()


# ------------------------------------------------------- فريق الرعاية
async def test_patient_cannot_be_assigned_as_a_specialist(
    session: AsyncSession, patient_user: User, admin_user: User
) -> None:
    """المفتاح الأجنبي المركّب يمنع إسناد مرضى إلى من ليس أخصائيًا."""
    await _expect_rejected(
        session,
        SpecialistPatient(specialist_id=patient_user.id, patient_id=admin_user.id),
    )


async def test_specialist_assignment_is_accepted(
    session: AsyncSession, specialist_user: User, patient_user: User
) -> None:
    session.add(SpecialistPatient(specialist_id=specialist_user.id, patient_id=patient_user.id))
    await session.commit()

    stored = await session.get(SpecialistPatient, (specialist_user.id, patient_user.id))
    assert stored is not None
    assert stored.is_active is True


async def test_specialist_cannot_be_their_own_patient(
    session: AsyncSession, specialist_user: User
) -> None:
    await _expect_rejected(
        session,
        SpecialistPatient(specialist_id=specialist_user.id, patient_id=specialist_user.id),
    )
