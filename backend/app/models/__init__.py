"""نماذج قاعدة البيانات.

كل نموذج جديد **لازم** يُستورد هنا، وإلا لن يراه Alembic عند التوليد
التلقائي وستُولَّد migration ناقصة بصمت.
"""

from app.models.audit import AuditAction, AuditLog
from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.care_team import SpecialistNote, SpecialistPatient
from app.models.catalog import (
    Exercise,
    ExerciseContraindication,
    Food,
    FoodAllergenLink,
    InjuryType,
    ReviewedContentMixin,
)
from app.models.clinical import DailyLog, Injury, InjuryAttachment, PhysiologicalReading
from app.models.enums import (
    ActivityLevel,
    Allergen,
    AttachmentType,
    BodyRegion,
    BodySide,
    ContraindicationSeverity,
    ExerciseCategory,
    ExerciseDifficulty,
    FoodCategory,
    Gender,
    Goal,
    InjuryStatus,
    MealSlot,
    PlanStatus,
    PlanType,
    ReadingSource,
)
from app.models.plan import (
    ALLOWED_STATUS_TRANSITIONS,
    NutritionPlan,
    Plan,
    PlanExercise,
    PlanMeal,
    PlanMealItem,
    PlanStatusTransition,
    RehabPlan,
    TrainingPlan,
)
from app.models.profile import FoodAllergy, UserProfile
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole

__all__ = [
    "ALLOWED_STATUS_TRANSITIONS",
    "ActivityLevel",
    "Allergen",
    "AttachmentType",
    "AuditAction",
    "AuditLog",
    "Base",
    "BodyRegion",
    "BodySide",
    "ContraindicationSeverity",
    "DailyLog",
    "Exercise",
    "ExerciseCategory",
    "ExerciseContraindication",
    "ExerciseDifficulty",
    "Food",
    "FoodAllergenLink",
    "FoodAllergy",
    "FoodCategory",
    "Gender",
    "Goal",
    "Injury",
    "InjuryAttachment",
    "InjuryStatus",
    "InjuryType",
    "MealSlot",
    "NutritionPlan",
    "PhysiologicalReading",
    "Plan",
    "PlanExercise",
    "PlanMeal",
    "PlanMealItem",
    "PlanStatus",
    "PlanStatusTransition",
    "PlanType",
    "ReadingSource",
    "RefreshToken",
    "RehabPlan",
    "ReviewedContentMixin",
    "SoftDeleteMixin",
    "SpecialistNote",
    "SpecialistPatient",
    "TimestampMixin",
    "TrainingPlan",
    "UUIDPrimaryKeyMixin",
    "User",
    "UserProfile",
    "UserRole",
]
