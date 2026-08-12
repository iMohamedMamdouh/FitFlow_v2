"""الحدود الآمنة وأخطاء المدخلات (تنفيذ ADR-007).

مبدأ هذا الملف: **لا قيمة افتراضية صامتة**. أي مدخل خارج النطاق المنطقي
يرفع استثناءً صريحًا. البديل — تصحيح المدخل بهدوء — يحوّل خطأ في نموذج
التسجيل إلى خطة غذائية خاطئة يثق بها المريض.
"""

from __future__ import annotations

from typing import Final

from app.core.enums import ActivityLevel, Gender

# ------------------------------------------------------------ حدود المدخلات
MIN_AGE_YEARS: Final = 14
MAX_AGE_YEARS: Final = 100
MIN_HEIGHT_CM: Final = 120.0
MAX_HEIGHT_CM: Final = 230.0
MIN_WEIGHT_KG: Final = 30.0
MAX_WEIGHT_KG: Final = 350.0

# ------------------------------------------------------- حدود الطاقة الآمنة
# الحد الأدنى للسعرات اليومية. أقل من ذلك لا يضمن الاحتياجات الدقيقة
# (فيتامينات ومعادن) ويخاطر بفقد الكتلة العضلية، ويحتاج إشرافًا طبيًا
# مباشرًا لا منصة دعم قرار.
CALORIE_FLOOR_BY_GENDER: Final[dict[Gender, int]] = {
    Gender.FEMALE: 1200,
    Gender.MALE: 1500,
}

# أقصى عجز حراري كنسبة من الاحتياج اليومي. العجز الأكبر يسرّع فقد العضل
# ويخفض الأيض، فيصبح الثبات أقرب لا أبعد.
MAX_DEFICIT_RATIO: Final = 0.25
TARGET_DEFICIT_KCAL: Final = 500  # ≈ نصف كيلو أسبوعيًا
TARGET_SURPLUS_KCAL: Final = 300

MAX_DAILY_CALORIES: Final = 6000

# معاملات النشاط المعتمدة مع معادلة Mifflin-St Jeor.
ACTIVITY_MULTIPLIERS: Final[dict[ActivityLevel, float]] = {
    ActivityLevel.SEDENTARY: 1.2,
    ActivityLevel.LIGHT: 1.375,
    ActivityLevel.MODERATE: 1.55,
    ActivityLevel.ACTIVE: 1.725,
    ActivityLevel.VERY_ACTIVE: 1.9,
}

# ------------------------------------------------------------ حدود الماكروز
MIN_PROTEIN_G_PER_KG: Final = 0.8
MAX_PROTEIN_G_PER_KG: Final = 2.5
MIN_FAT_G_PER_KG: Final = 0.6  # أقل من ذلك يخل بالتوازن الهرموني
FAT_CALORIE_SHARE: Final = 0.25

# ---------------------------------------------------------- حدود إدارة الوزن
# فقد أسرع من 1% من وزن الجسم أسبوعيًا مؤشر خطر لا إنجاز.
MAX_SAFE_WEEKLY_LOSS_RATIO: Final = 0.01
# تغيّر أقل من هذا خلال نافذة المتابعة يُعتبر ثباتًا.
PLATEAU_THRESHOLD_KG: Final = 0.3
PLATEAU_WINDOW_DAYS: Final = 14
MIN_DAYS_FOR_TREND: Final = 10
PLATEAU_CALORIE_STEP: Final = 100


class RuleEngineError(Exception):
    """خطأ في محرك القواعد."""


class InvalidInputError(RuleEngineError):
    """مدخل خارج النطاق المنطقي — يُرفض ولا يُصحَّح ضمنيًا."""


class InsufficientDataError(RuleEngineError):
    """لا تكفي البيانات لاتخاذ قرار — ليس خطأ، بل امتناع صريح."""


def require_range(value: float, low: float, high: float, *, field: str, unit: str = "") -> None:
    """يرفع ``InvalidInputError`` إذا خرجت القيمة عن النطاق."""
    if not low <= value <= high:
        suffix = f" {unit}" if unit else ""
        raise InvalidInputError(
            f"{field} = {value}{suffix} خارج النطاق المقبول [{low}, {high}]{suffix}"
        )


def calorie_floor(gender: Gender) -> int:
    return CALORIE_FLOOR_BY_GENDER[gender]


__all__ = [
    "ACTIVITY_MULTIPLIERS",
    "CALORIE_FLOOR_BY_GENDER",
    "FAT_CALORIE_SHARE",
    "MAX_DAILY_CALORIES",
    "MAX_DEFICIT_RATIO",
    "MAX_PROTEIN_G_PER_KG",
    "MAX_SAFE_WEEKLY_LOSS_RATIO",
    "MIN_DAYS_FOR_TREND",
    "MIN_FAT_G_PER_KG",
    "MIN_PROTEIN_G_PER_KG",
    "PLATEAU_CALORIE_STEP",
    "PLATEAU_THRESHOLD_KG",
    "PLATEAU_WINDOW_DAYS",
    "TARGET_DEFICIT_KCAL",
    "TARGET_SURPLUS_KCAL",
    "InsufficientDataError",
    "InvalidInputError",
    "RuleEngineError",
    "calorie_floor",
    "require_range",
]
