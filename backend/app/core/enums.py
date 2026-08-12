"""التعدادات المشتركة — وحدة نقية بلا أي اعتماديات خارجية.

مفصولة عن ``app/models/enums.py`` عمدًا: محرك القواعد (المرحلة 4) ممنوع
أن يستورد SQLAlchemy، لكنه يحتاج نفس القيم بالحرف. مصدر واحد للقيم يمنع
أن يُنتج المحرك قيمة لا تقبلها قاعدة البيانات.
"""

from __future__ import annotations

import enum


class Gender(enum.StrEnum):
    """يُستخدم في معادلة Mifflin-St Jeor التي تفرّق بين الجنسين."""

    MALE = "male"
    FEMALE = "female"


class ActivityLevel(enum.StrEnum):
    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    ACTIVE = "active"
    VERY_ACTIVE = "very_active"


class Goal(enum.StrEnum):
    WEIGHT_LOSS = "weight_loss"
    MUSCLE_GAIN = "muscle_gain"
    MAINTENANCE = "maintenance"
    REHABILITATION = "rehabilitation"


class BodyRegion(enum.StrEnum):
    SHOULDER = "shoulder"
    ELBOW = "elbow"
    WRIST = "wrist"
    NECK = "neck"
    UPPER_BACK = "upper_back"
    LOWER_BACK = "lower_back"
    HIP = "hip"
    KNEE = "knee"
    ANKLE = "ankle"
    FOOT = "foot"
    OTHER = "other"


class BodySide(enum.StrEnum):
    LEFT = "left"
    RIGHT = "right"
    BILATERAL = "bilateral"
    NOT_APPLICABLE = "not_applicable"


class InjuryStatus(enum.StrEnum):
    """مرحلة الإصابة — تحدد ما يُسمح به من تمارين.

    ``ACUTE`` تمنع تمامًا أي تمرين مقاومة على المنطقة المصابة (ADR-007).
    """

    ACUTE = "acute"
    SUBACUTE = "subacute"
    CHRONIC = "chronic"
    RECOVERED = "recovered"


class ExerciseCategory(enum.StrEnum):
    STRENGTH = "strength"
    MOBILITY = "mobility"
    STABILITY = "stability"
    BALANCE = "balance"
    CARDIO = "cardio"
    STRETCHING = "stretching"


class ExerciseDifficulty(enum.StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ContraindicationSeverity(enum.StrEnum):
    """``ABSOLUTE`` تعني منعًا قاطعًا، و``RELATIVE`` تعني بشروط ومتابعة."""

    ABSOLUTE = "absolute"
    RELATIVE = "relative"


class Allergen(enum.StrEnum):
    """مسبّبات الحساسية الشائعة.

    نوع محدود لا نص حر: خطأ إملائي في اسم مسبّب حساسية يعني طعامًا خطرًا
    يمر من الفلتر بصمت.
    """

    GLUTEN = "gluten"
    DAIRY = "dairy"
    EGGS = "eggs"
    PEANUTS = "peanuts"
    TREE_NUTS = "tree_nuts"
    SOY = "soy"
    FISH = "fish"
    SHELLFISH = "shellfish"
    SESAME = "sesame"


class FoodCategory(enum.StrEnum):
    GRAINS = "grains"
    PROTEIN = "protein"
    DAIRY = "dairy"
    VEGETABLES = "vegetables"
    FRUITS = "fruits"
    LEGUMES = "legumes"
    FATS = "fats"
    BEVERAGES = "beverages"
    SWEETS = "sweets"
    OTHER = "other"


class MealSlot(enum.StrEnum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class PlanType(enum.StrEnum):
    REHAB = "rehab"
    NUTRITION = "nutrition"
    TRAINING = "training"
    COMBINED = "combined"


class PlanStatus(enum.StrEnum):
    """حالات الخطة — آلة حالات مفروضة على مستوى قاعدة البيانات (ADR-006).

    الانتقالات المسموحة::

        draft ──────────▶ pending_review ──▶ approved ──▶ active ──▶ archived
          ▲                     │
          └── changes_requested ┘

    والأرشفة متاحة من أي حالة.
    """

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    CHANGES_REQUESTED = "changes_requested"
    APPROVED = "approved"
    ACTIVE = "active"
    ARCHIVED = "archived"

    @property
    def is_visible_to_patient(self) -> bool:
        """المريض لا يرى إلا الخطط المعتمدة والمفعّلة."""
        return self in {PlanStatus.ACTIVE, PlanStatus.ARCHIVED}


class ReadingSource(enum.StrEnum):
    MANUAL = "manual"
    SMARTWATCH = "smartwatch"
    DEVICE = "device"


class AttachmentType(enum.StrEnum):
    XRAY = "xray"
    MRI = "mri"
    CT_SCAN = "ct_scan"
    ULTRASOUND = "ultrasound"
    REPORT = "report"
    PHOTO = "photo"
    OTHER = "other"


__all__ = [
    "ActivityLevel",
    "Allergen",
    "AttachmentType",
    "BodyRegion",
    "BodySide",
    "ContraindicationSeverity",
    "ExerciseCategory",
    "ExerciseDifficulty",
    "FoodCategory",
    "Gender",
    "Goal",
    "InjuryStatus",
    "MealSlot",
    "PlanStatus",
    "PlanType",
    "ReadingSource",
]
