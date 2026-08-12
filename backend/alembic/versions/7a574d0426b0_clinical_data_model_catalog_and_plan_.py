"""clinical data model, catalog and plan approval state machine

Revision ID: 7a574d0426b0
Revises: 9a2ca44f2bbb
Create Date: 2026-08-12

مُولَّدة تلقائيًا ثم روجعت يدويًا. الإضافات التي لا يعرفها التوليد التلقائي:

1. امتداد ``pg_trgm`` — يحتاجه فهرس البحث الجزئي في الأسماء العربية.
2. فهرس فريد **جزئي**: خطة مفعّلة واحدة لكل مستخدم لكل نوع. القيد المشروط
   لا يُعبَّر عنه بـ UniqueConstraint فلا يراه التوليد التلقائي.
3. آلة حالات الخطة كـ trigger (ADR-006) — الحاجز الثاني بعد فحوص CHECK.
4. حذف أنواع ENUM في التراجع. التوليد التلقائي ينشئها ضمنًا مع الجداول ولا
   يحذفها، فيفشل الـ upgrade التالي بـ "type already exists".
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "7a574d0426b0"
down_revision: str | None = "9a2ca44f2bbb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# تُنشأ الأنواع مرة واحدة صراحةً. الإنشاء الضمني داخل create_table يحاول
# إنشاء النوع مع كل جدول يستخدمه، فيفشل الثاني بـ "type already exists".
EXERCISE_CATEGORY = postgresql.ENUM(
    "strength",
    "mobility",
    "stability",
    "balance",
    "cardio",
    "stretching",
    name="exercise_category",
    create_type=False,
)
EXERCISE_DIFFICULTY = postgresql.ENUM(
    "beginner", "intermediate", "advanced", name="exercise_difficulty", create_type=False
)
BODY_REGION = postgresql.ENUM(
    "shoulder",
    "elbow",
    "wrist",
    "neck",
    "upper_back",
    "lower_back",
    "hip",
    "knee",
    "ankle",
    "foot",
    "other",
    name="body_region",
    create_type=False,
)
FOOD_CATEGORY = postgresql.ENUM(
    "grains",
    "protein",
    "dairy",
    "vegetables",
    "fruits",
    "legumes",
    "fats",
    "beverages",
    "sweets",
    "other",
    name="food_category",
    create_type=False,
)
CONTRAINDICATION_SEVERITY = postgresql.ENUM(
    "absolute", "relative", name="contraindication_severity", create_type=False
)
ALLERGEN = postgresql.ENUM(
    "gluten",
    "dairy",
    "eggs",
    "peanuts",
    "tree_nuts",
    "soy",
    "fish",
    "shellfish",
    "sesame",
    name="allergen",
    create_type=False,
)
BODY_SIDE = postgresql.ENUM(
    "left", "right", "bilateral", "not_applicable", name="body_side", create_type=False
)
INJURY_STATUS = postgresql.ENUM(
    "acute", "subacute", "chronic", "recovered", name="injury_status", create_type=False
)
READING_SOURCE = postgresql.ENUM(
    "manual", "smartwatch", "device", name="reading_source", create_type=False
)
PLAN_TYPE = postgresql.ENUM(
    "rehab", "nutrition", "training", "combined", name="plan_type", create_type=False
)
PLAN_STATUS = postgresql.ENUM(
    "draft",
    "pending_review",
    "changes_requested",
    "approved",
    "active",
    "archived",
    name="plan_status",
    create_type=False,
)
GENDER = postgresql.ENUM("male", "female", name="gender", create_type=False)
ACTIVITY_LEVEL = postgresql.ENUM(
    "sedentary",
    "light",
    "moderate",
    "active",
    "very_active",
    name="activity_level",
    create_type=False,
)
GOAL = postgresql.ENUM(
    "weight_loss", "muscle_gain", "maintenance", "rehabilitation", name="goal", create_type=False
)
ATTACHMENT_TYPE = postgresql.ENUM(
    "xray",
    "mri",
    "ct_scan",
    "ultrasound",
    "report",
    "photo",
    "other",
    name="attachment_type",
    create_type=False,
)
MEAL_SLOT = postgresql.ENUM(
    "breakfast", "lunch", "dinner", "snack", name="meal_slot", create_type=False
)

NEW_ENUM_TYPES = (
    "exercise_category",
    "exercise_difficulty",
    "body_region",
    "food_category",
    "contraindication_severity",
    "allergen",
    "body_side",
    "injury_status",
    "reading_source",
    "plan_type",
    "plan_status",
    "gender",
    "activity_level",
    "goal",
    "attachment_type",
    "meal_slot",
)


def upgrade() -> None:
    # يلزم لفهرس gin_trgm_ops على الأسماء العربية في جدول الأغذية.
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    bind = op.get_bind()
    for enum_name in NEW_ENUM_TYPES:
        globals()[enum_name.upper()].create(bind, checkfirst=True)

    # هدف المفتاح الأجنبي المركّب في specialist_patients — لا بد أن
    # يوجد قبل إنشاء الجدول الذي يشير إليه.
    op.create_unique_constraint("id_role", "users", ["id", "role"])

    op.create_table(
        "exercises",
        sa.Column("name_ar", sa.String(length=200), nullable=False),
        sa.Column("name_en", sa.String(length=200), nullable=True),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column(
            "category",
            postgresql.ENUM(
                "strength",
                "mobility",
                "stability",
                "balance",
                "cardio",
                "stretching",
                name="exercise_category",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "difficulty",
            postgresql.ENUM(
                "beginner",
                "intermediate",
                "advanced",
                name="exercise_difficulty",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "primary_region",
            postgresql.ENUM(
                "shoulder",
                "elbow",
                "wrist",
                "neck",
                "upper_back",
                "lower_back",
                "hip",
                "knee",
                "ankle",
                "foot",
                "other",
                name="body_region",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "target_muscles",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "equipment",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("instructions_ar", sa.Text(), nullable=True),
        sa.Column("video_url", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("reviewed_by", sa.String(length=200), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_reference", sa.Text(), nullable=True),
        sa.Column("content_version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_exercises")),
        sa.UniqueConstraint("slug", name=op.f("uq_exercises_slug")),
    )
    op.create_index(
        "ix_exercises_category_difficulty", "exercises", ["category", "difficulty"], unique=False
    )
    op.create_index(
        "ix_exercises_region_active", "exercises", ["primary_region", "is_active"], unique=False
    )
    op.create_table(
        "foods",
        sa.Column("name_ar", sa.String(length=200), nullable=False),
        sa.Column("name_en", sa.String(length=200), nullable=True),
        sa.Column(
            "category",
            postgresql.ENUM(
                "grains",
                "protein",
                "dairy",
                "vegetables",
                "fruits",
                "legumes",
                "fats",
                "beverages",
                "sweets",
                "other",
                name="food_category",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("calories_per_100g", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column("protein_g", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("carbs_g", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("fat_g", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column(
            "fiber_g", sa.Numeric(precision=6, scale=2), server_default=sa.text("0"), nullable=False
        ),
        sa.Column(
            "source", sa.String(length=50), server_default=sa.text("'manual'"), nullable=False
        ),
        sa.Column("external_id", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "calories_per_100g BETWEEN 0 AND 950", name=op.f("ck_foods_calories_within_range")
        ),
        sa.CheckConstraint("carbs_g BETWEEN 0 AND 100", name=op.f("ck_foods_carbs_within_range")),
        sa.CheckConstraint("fat_g BETWEEN 0 AND 100", name=op.f("ck_foods_fat_within_range")),
        sa.CheckConstraint("fiber_g BETWEEN 0 AND 100", name=op.f("ck_foods_fiber_within_range")),
        sa.CheckConstraint(
            "protein_g + carbs_g + fat_g <= 100", name=op.f("ck_foods_macros_fit_in_100g")
        ),
        sa.CheckConstraint(
            "protein_g BETWEEN 0 AND 100", name=op.f("ck_foods_protein_within_range")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_foods")),
    )
    op.create_index("ix_foods_category_active", "foods", ["category", "is_active"], unique=False)
    op.create_index(
        "ix_foods_name_ar_trgm",
        "foods",
        ["name_ar"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"name_ar": "gin_trgm_ops"},
    )
    op.create_table(
        "injury_types",
        sa.Column("name_ar", sa.String(length=200), nullable=False),
        sa.Column("name_en", sa.String(length=200), nullable=True),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column(
            "body_region",
            postgresql.ENUM(
                "shoulder",
                "elbow",
                "wrist",
                "neck",
                "upper_back",
                "lower_back",
                "hip",
                "knee",
                "ankle",
                "foot",
                "other",
                name="body_region",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("description_ar", sa.Text(), nullable=True),
        sa.Column(
            "phases",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("reviewed_by", sa.String(length=200), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_reference", sa.Text(), nullable=True),
        sa.Column("content_version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.CheckConstraint(
            "jsonb_typeof(phases) = 'array'", name=op.f("ck_injury_types_phases_is_array")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_injury_types")),
        sa.UniqueConstraint("slug", name=op.f("uq_injury_types_slug")),
    )
    op.create_index(
        "ix_injury_types_region_active", "injury_types", ["body_region", "is_active"], unique=False
    )
    op.create_table(
        "daily_logs",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("weight_kg", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("pain_level", sa.Integer(), nullable=True),
        sa.Column("diet_adherence_pct", sa.Integer(), nullable=True),
        sa.Column("exercise_adherence_pct", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "diet_adherence_pct IS NULL OR diet_adherence_pct BETWEEN 0 AND 100",
            name=op.f("ck_daily_logs_diet_adherence_within_range"),
        ),
        sa.CheckConstraint(
            "exercise_adherence_pct IS NULL OR exercise_adherence_pct BETWEEN 0 AND 100",
            name=op.f("ck_daily_logs_exercise_adherence_within_range"),
        ),
        sa.CheckConstraint(
            "log_date <= CURRENT_DATE", name=op.f("ck_daily_logs_log_date_not_in_future")
        ),
        sa.CheckConstraint(
            "pain_level IS NULL OR pain_level BETWEEN 0 AND 10",
            name=op.f("ck_daily_logs_pain_level_within_scale"),
        ),
        sa.CheckConstraint(
            "weight_kg IS NULL OR weight_kg BETWEEN 20 AND 500",
            name=op.f("ck_daily_logs_weight_within_range"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_daily_logs_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_daily_logs")),
        sa.UniqueConstraint("user_id", "log_date", name="one_log_per_day"),
    )
    op.create_index("ix_daily_logs_user_date", "daily_logs", ["user_id", "log_date"], unique=False)
    op.create_table(
        "exercise_contraindications",
        sa.Column("exercise_id", sa.UUID(), nullable=False),
        sa.Column("injury_type_id", sa.UUID(), nullable=False),
        sa.Column(
            "severity",
            postgresql.ENUM(
                "absolute", "relative", name="contraindication_severity", create_type=False
            ),
            nullable=False,
        ),
        sa.Column("rationale_ar", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["exercise_id"],
            ["exercises.id"],
            name=op.f("fk_exercise_contraindications_exercise_id_exercises"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["injury_type_id"],
            ["injury_types.id"],
            name=op.f("fk_exercise_contraindications_injury_type_id_injury_types"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "exercise_id", "injury_type_id", name=op.f("pk_exercise_contraindications")
        ),
    )
    op.create_table(
        "food_allergens",
        sa.Column("food_id", sa.UUID(), nullable=False),
        sa.Column(
            "allergen",
            postgresql.ENUM(
                "gluten",
                "dairy",
                "eggs",
                "peanuts",
                "tree_nuts",
                "soy",
                "fish",
                "shellfish",
                "sesame",
                name="allergen",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["food_id"],
            ["foods.id"],
            name=op.f("fk_food_allergens_food_id_foods"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("food_id", "allergen", name=op.f("pk_food_allergens")),
    )
    op.create_table(
        "injuries",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("injury_type_id", sa.UUID(), nullable=False),
        sa.Column(
            "side",
            postgresql.ENUM(
                "left", "right", "bilateral", "not_applicable", name="body_side", create_type=False
            ),
            nullable=False,
        ),
        sa.Column("injury_date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "acute", "subacute", "chronic", "recovered", name="injury_status", create_type=False
            ),
            nullable=False,
        ),
        sa.Column("current_phase", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("pain_level", sa.Integer(), nullable=False),
        sa.Column(
            "range_of_motion",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("had_surgery", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("surgery_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(had_surgery AND surgery_date IS NOT NULL AND surgery_date >= injury_date) OR (NOT had_surgery AND surgery_date IS NULL)",
            name=op.f("ck_injuries_surgery_fields_are_consistent"),
        ),
        sa.CheckConstraint(
            "current_phase BETWEEN 1 AND 10", name=op.f("ck_injuries_current_phase_within_range")
        ),
        sa.CheckConstraint(
            "injury_date <= CURRENT_DATE", name=op.f("ck_injuries_injury_date_not_in_future")
        ),
        sa.CheckConstraint(
            "pain_level BETWEEN 0 AND 10", name=op.f("ck_injuries_pain_level_within_scale")
        ),
        sa.ForeignKeyConstraint(
            ["injury_type_id"],
            ["injury_types.id"],
            name=op.f("fk_injuries_injury_type_id_injury_types"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_injuries_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_injuries")),
    )
    op.create_index(
        op.f("ix_injuries_injury_type_id"), "injuries", ["injury_type_id"], unique=False
    )
    op.create_index(op.f("ix_injuries_status"), "injuries", ["status"], unique=False)
    op.create_index(op.f("ix_injuries_user_id"), "injuries", ["user_id"], unique=False)
    op.create_index("ix_injuries_user_status", "injuries", ["user_id", "status"], unique=False)
    op.create_table(
        "physiological_readings",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("reading_date", sa.Date(), nullable=False),
        sa.Column(
            "source",
            postgresql.ENUM(
                "manual", "smartwatch", "device", name="reading_source", create_type=False
            ),
            nullable=False,
        ),
        sa.Column("weight_kg", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("body_fat_pct", sa.Numeric(precision=4, scale=1), nullable=True),
        sa.Column("muscle_mass_kg", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("resting_hr", sa.Integer(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "body_fat_pct IS NULL OR body_fat_pct BETWEEN 1 AND 70",
            name=op.f("ck_physiological_readings_body_fat_within_range"),
        ),
        sa.CheckConstraint(
            "muscle_mass_kg IS NULL OR muscle_mass_kg BETWEEN 5 AND 150",
            name=op.f("ck_physiological_readings_muscle_mass_within_range"),
        ),
        sa.CheckConstraint(
            "reading_date <= CURRENT_DATE",
            name=op.f("ck_physiological_readings_reading_date_not_in_future"),
        ),
        sa.CheckConstraint(
            "resting_hr IS NULL OR resting_hr BETWEEN 25 AND 250",
            name=op.f("ck_physiological_readings_resting_hr_within_range"),
        ),
        sa.CheckConstraint(
            "weight_kg IS NULL OR weight_kg BETWEEN 20 AND 500",
            name=op.f("ck_physiological_readings_weight_within_range"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_physiological_readings_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_physiological_readings")),
        sa.UniqueConstraint("user_id", "reading_date", "source", name="one_reading_per_day_source"),
    )
    op.create_index(
        "ix_readings_user_date", "physiological_readings", ["user_id", "reading_date"], unique=False
    )
    op.create_table(
        "plans",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "plan_type",
            postgresql.ENUM(
                "rehab", "nutrition", "training", "combined", name="plan_type", create_type=False
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "draft",
                "pending_review",
                "changes_requested",
                "approved",
                "active",
                "archived",
                name="plan_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("rule_engine_version", sa.String(length=20), nullable=False),
        sa.Column("content_version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("approved_by_specialist_id", sa.UUID(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("active_from", sa.Date(), nullable=True),
        sa.Column("active_to", sa.Date(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status NOT IN ('approved', 'active') OR (approved_by_specialist_id IS NOT NULL AND approved_at IS NOT NULL)",
            name=op.f("ck_plans_approved_plan_has_approver"),
        ),
        sa.CheckConstraint(
            "status NOT IN ('draft', 'pending_review') OR (approved_by_specialist_id IS NULL AND approved_at IS NULL)",
            name=op.f("ck_plans_unapproved_plan_has_no_approver"),
        ),
        sa.CheckConstraint(
            "active_to IS NULL OR active_from IS NULL OR active_to >= active_from",
            name=op.f("ck_plans_active_period_is_ordered"),
        ),
        sa.ForeignKeyConstraint(
            ["approved_by_specialist_id"],
            ["users.id"],
            name=op.f("fk_plans_approved_by_specialist_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_plans_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_plans")),
    )
    op.create_index(op.f("ix_plans_status"), "plans", ["status"], unique=False)
    op.create_index("ix_plans_user_status", "plans", ["user_id", "status"], unique=False)
    op.create_table(
        "specialist_patients",
        sa.Column("specialist_id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column(
            "specialist_role",
            postgresql.ENUM("patient", "specialist", "admin", name="user_role", create_type=False),
            sa.Computed("'specialist'::user_role", persisted=True),
            nullable=False,
        ),
        sa.Column("assigned_by", sa.UUID(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "specialist_id <> patient_id",
            name=op.f("ck_specialist_patients_specialist_is_not_the_patient"),
        ),
        sa.ForeignKeyConstraint(
            ["assigned_by"],
            ["users.id"],
            name=op.f("fk_specialist_patients_assigned_by_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["users.id"],
            name=op.f("fk_specialist_patients_patient_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["specialist_id", "specialist_role"],
            ["users.id", "users.role"],
            name="fk_specialist_patients_specialist_is_specialist",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("specialist_id", "patient_id", name=op.f("pk_specialist_patients")),
    )
    op.create_index(
        "ix_specialist_patients_patient", "specialist_patients", ["patient_id"], unique=False
    )
    op.create_table(
        "user_food_allergies",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "allergen",
            postgresql.ENUM(
                "gluten",
                "dairy",
                "eggs",
                "peanuts",
                "tree_nuts",
                "soy",
                "fish",
                "shellfish",
                "sesame",
                name="allergen",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("severity_note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_food_allergies_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", "allergen", name=op.f("pk_user_food_allergies")),
    )
    op.create_table(
        "user_profiles",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=False),
        sa.Column(
            "gender",
            postgresql.ENUM("male", "female", name="gender", create_type=False),
            nullable=False,
        ),
        sa.Column("height_cm", sa.Numeric(precision=5, scale=1), nullable=False),
        sa.Column(
            "activity_level",
            postgresql.ENUM(
                "sedentary",
                "light",
                "moderate",
                "active",
                "very_active",
                name="activity_level",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "goal",
            postgresql.ENUM(
                "weight_loss",
                "muscle_gain",
                "maintenance",
                "rehabilitation",
                name="goal",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "medical_history",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "chronic_diseases",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "medications",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("consent_accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "birth_date >= CURRENT_DATE - INTERVAL '120 years'",
            name=op.f("ck_user_profiles_birth_date_within_120_years"),
        ),
        sa.CheckConstraint(
            "birth_date <= CURRENT_DATE", name=op.f("ck_user_profiles_birth_date_not_in_future")
        ),
        sa.CheckConstraint(
            "height_cm BETWEEN 50 AND 260", name=op.f("ck_user_profiles_height_within_human_range")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_profiles_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", name=op.f("pk_user_profiles")),
    )
    op.create_table(
        "injury_attachments",
        sa.Column("injury_id", sa.UUID(), nullable=False),
        sa.Column("storage_key", sa.String(length=500), nullable=False),
        sa.Column(
            "file_type",
            postgresql.ENUM(
                "xray",
                "mri",
                "ct_scan",
                "ultrasound",
                "report",
                "photo",
                "other",
                name="attachment_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("uploaded_by", sa.UUID(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "size_bytes > 0 AND size_bytes <= 52428800",
            name=op.f("ck_injury_attachments_size_within_50mb"),
        ),
        sa.ForeignKeyConstraint(
            ["injury_id"],
            ["injuries.id"],
            name=op.f("fk_injury_attachments_injury_id_injuries"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["uploaded_by"],
            ["users.id"],
            name=op.f("fk_injury_attachments_uploaded_by_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_injury_attachments")),
    )
    op.create_index(
        op.f("ix_injury_attachments_injury_id"), "injury_attachments", ["injury_id"], unique=False
    )
    op.create_table(
        "nutrition_plans",
        sa.Column("plan_id", sa.UUID(), nullable=False),
        sa.Column("daily_calories", sa.Integer(), nullable=False),
        sa.Column("protein_g", sa.Numeric(precision=6, scale=1), nullable=False),
        sa.Column("carbs_g", sa.Numeric(precision=6, scale=1), nullable=False),
        sa.Column("fat_g", sa.Numeric(precision=6, scale=1), nullable=False),
        sa.Column("notes_ar", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "daily_calories <= 6000", name=op.f("ck_nutrition_plans_calories_below_upper_bound")
        ),
        sa.CheckConstraint(
            "daily_calories >= 1200", name=op.f("ck_nutrition_plans_calories_above_safety_floor")
        ),
        sa.CheckConstraint(
            "protein_g >= 0 AND carbs_g >= 0 AND fat_g >= 0",
            name=op.f("ck_nutrition_plans_macros_positive"),
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["plans.id"],
            name=op.f("fk_nutrition_plans_plan_id_plans"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("plan_id", name=op.f("pk_nutrition_plans")),
    )
    op.create_table(
        "plan_exercises",
        sa.Column("plan_id", sa.UUID(), nullable=False),
        sa.Column("exercise_id", sa.UUID(), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=True),
        sa.Column("order_index", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("sets", sa.Integer(), nullable=False),
        sa.Column("reps", sa.Integer(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("intensity_pct", sa.Integer(), nullable=True),
        sa.Column("rest_seconds", sa.Integer(), nullable=True),
        sa.Column("notes_ar", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.CheckConstraint(
            "day_of_week IS NULL OR day_of_week BETWEEN 0 AND 6",
            name=op.f("ck_plan_exercises_day_of_week_valid"),
        ),
        sa.CheckConstraint(
            "intensity_pct IS NULL OR intensity_pct BETWEEN 1 AND 100",
            name=op.f("ck_plan_exercises_intensity_within_range"),
        ),
        sa.CheckConstraint(
            "reps IS NOT NULL OR duration_seconds IS NOT NULL",
            name=op.f("ck_plan_exercises_has_reps_or_duration"),
        ),
        sa.CheckConstraint(
            "reps IS NULL OR reps BETWEEN 1 AND 200",
            name=op.f("ck_plan_exercises_reps_within_range"),
        ),
        sa.CheckConstraint(
            "sets BETWEEN 1 AND 20", name=op.f("ck_plan_exercises_sets_within_range")
        ),
        sa.ForeignKeyConstraint(
            ["exercise_id"],
            ["exercises.id"],
            name=op.f("fk_plan_exercises_exercise_id_exercises"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["plans.id"],
            name=op.f("fk_plan_exercises_plan_id_plans"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_plan_exercises")),
    )
    op.create_index(op.f("ix_plan_exercises_plan_id"), "plan_exercises", ["plan_id"], unique=False)
    op.create_table(
        "plan_meals",
        sa.Column("plan_id", sa.UUID(), nullable=False),
        sa.Column(
            "slot",
            postgresql.ENUM(
                "breakfast", "lunch", "dinner", "snack", name="meal_slot", create_type=False
            ),
            nullable=False,
        ),
        sa.Column("order_index", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["plan_id"], ["plans.id"], name=op.f("fk_plan_meals_plan_id_plans"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_plan_meals")),
        sa.UniqueConstraint("plan_id", "slot", "order_index", name="unique_meal_slot"),
    )
    op.create_index(op.f("ix_plan_meals_plan_id"), "plan_meals", ["plan_id"], unique=False)
    op.create_table(
        "plan_status_transitions",
        sa.Column("plan_id", sa.UUID(), nullable=False),
        sa.Column(
            "from_status",
            postgresql.ENUM(
                "draft",
                "pending_review",
                "changes_requested",
                "approved",
                "active",
                "archived",
                name="plan_status",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column(
            "to_status",
            postgresql.ENUM(
                "draft",
                "pending_review",
                "changes_requested",
                "approved",
                "active",
                "archived",
                name="plan_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("actor_user_id", sa.UUID(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            name=op.f("fk_plan_status_transitions_actor_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["plans.id"],
            name=op.f("fk_plan_status_transitions_plan_id_plans"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_plan_status_transitions")),
    )
    op.create_index(
        op.f("ix_plan_status_transitions_plan_id"),
        "plan_status_transitions",
        ["plan_id"],
        unique=False,
    )
    op.create_table(
        "rehab_plans",
        sa.Column("plan_id", sa.UUID(), nullable=False),
        sa.Column("injury_id", sa.UUID(), nullable=False),
        sa.Column("phase", sa.Integer(), nullable=False),
        sa.Column(
            "goals",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "phase BETWEEN 1 AND 10", name=op.f("ck_rehab_plans_phase_within_range")
        ),
        sa.ForeignKeyConstraint(
            ["injury_id"],
            ["injuries.id"],
            name=op.f("fk_rehab_plans_injury_id_injuries"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"], ["plans.id"], name=op.f("fk_rehab_plans_plan_id_plans"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("plan_id", name=op.f("pk_rehab_plans")),
    )
    op.create_index(op.f("ix_rehab_plans_injury_id"), "rehab_plans", ["injury_id"], unique=False)
    op.create_table(
        "specialist_notes",
        sa.Column("specialist_id", sa.UUID(), nullable=True),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("plan_id", sa.UUID(), nullable=True),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("is_internal", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(trim(note)) > 0", name=op.f("ck_specialist_notes_note_is_not_blank")
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["users.id"],
            name=op.f("fk_specialist_notes_patient_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["plans.id"],
            name=op.f("fk_specialist_notes_plan_id_plans"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["specialist_id"],
            ["users.id"],
            name=op.f("fk_specialist_notes_specialist_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_specialist_notes")),
    )
    op.create_index(
        "ix_specialist_notes_patient_created",
        "specialist_notes",
        ["patient_id", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_specialist_notes_patient_id"), "specialist_notes", ["patient_id"], unique=False
    )
    op.create_index(
        op.f("ix_specialist_notes_specialist_id"),
        "specialist_notes",
        ["specialist_id"],
        unique=False,
    )
    op.create_table(
        "training_plans",
        sa.Column("plan_id", sa.UUID(), nullable=False),
        sa.Column("sessions_per_week", sa.Integer(), nullable=False),
        sa.Column("notes_ar", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "sessions_per_week BETWEEN 1 AND 14",
            name=op.f("ck_training_plans_sessions_within_range"),
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["plans.id"],
            name=op.f("fk_training_plans_plan_id_plans"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("plan_id", name=op.f("pk_training_plans")),
    )
    op.create_table(
        "plan_meal_items",
        sa.Column("meal_id", sa.UUID(), nullable=False),
        sa.Column("food_id", sa.UUID(), nullable=False),
        sa.Column("grams", sa.Numeric(precision=7, scale=1), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.CheckConstraint(
            "grams > 0 AND grams <= 5000", name=op.f("ck_plan_meal_items_grams_within_range")
        ),
        sa.ForeignKeyConstraint(
            ["food_id"],
            ["foods.id"],
            name=op.f("fk_plan_meal_items_food_id_foods"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["meal_id"],
            ["plan_meals.id"],
            name=op.f("fk_plan_meal_items_meal_id_plan_meals"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_plan_meal_items")),
    )
    op.create_index(
        op.f("ix_plan_meal_items_meal_id"), "plan_meal_items", ["meal_id"], unique=False
    )

    # ---------------------------------------------------- آلة حالات الخطة
    # خطة مفعّلة واحدة فقط لكل مستخدم لكل نوع. فهرس فريد جزئي لأن الشرط
    # يقتصر على الحالة 'active' — الأرشيف قد يحوي عشرات الخطط.
    op.execute("""
        CREATE UNIQUE INDEX uq_plans_single_active_per_user_type
            ON plans (user_id, plan_type)
            WHERE status = 'active'
        """)

    # الانتقالات المسموحة تُفرض هنا أيضًا، لا في التطبيق وحده (ADR-006).
    # أي مسار API جديد أو سكربت صيانة أو استعلام يدوي يمر من هذا الحاجز.
    # الجدول أدناه نسخة حرفية من ALLOWED_STATUS_TRANSITIONS في
    # app/models/plan.py، وهناك اختبار يقارن الاثنين حتى لا يتباعدا.
    op.execute("""
        CREATE OR REPLACE FUNCTION enforce_plan_status_transition()
        RETURNS trigger AS $$
        BEGIN
            IF OLD.status IS NOT DISTINCT FROM NEW.status THEN
                RETURN NEW;
            END IF;

            IF NOT (
                   (OLD.status = 'draft'
                        AND NEW.status IN ('pending_review', 'archived'))
                OR (OLD.status = 'pending_review'
                        AND NEW.status IN ('approved', 'changes_requested', 'archived'))
                OR (OLD.status = 'changes_requested'
                        AND NEW.status IN ('draft', 'archived'))
                OR (OLD.status = 'approved'
                        AND NEW.status IN ('active', 'archived'))
                OR (OLD.status = 'active'
                        AND NEW.status = 'archived')
            ) THEN
                RAISE EXCEPTION
                    'انتقال غير مسموح لحالة الخطة: % → %', OLD.status, NEW.status
                    USING ERRCODE = 'check_violation';
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """)
    op.execute("""
        CREATE TRIGGER trg_plans_status_transition
            BEFORE UPDATE OF status ON plans
            FOR EACH ROW
            EXECUTE FUNCTION enforce_plan_status_transition()
        """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_plans_status_transition ON plans")
    op.execute("DROP FUNCTION IF EXISTS enforce_plan_status_transition()")
    op.execute("DROP INDEX IF EXISTS uq_plans_single_active_per_user_type")

    op.drop_index(op.f("ix_plan_meal_items_meal_id"), table_name="plan_meal_items")
    op.drop_table("plan_meal_items")
    op.drop_table("training_plans")
    op.drop_index(op.f("ix_specialist_notes_specialist_id"), table_name="specialist_notes")
    op.drop_index(op.f("ix_specialist_notes_patient_id"), table_name="specialist_notes")
    op.drop_index("ix_specialist_notes_patient_created", table_name="specialist_notes")
    op.drop_table("specialist_notes")
    op.drop_index(op.f("ix_rehab_plans_injury_id"), table_name="rehab_plans")
    op.drop_table("rehab_plans")
    op.drop_index(op.f("ix_plan_status_transitions_plan_id"), table_name="plan_status_transitions")
    op.drop_table("plan_status_transitions")
    op.drop_index(op.f("ix_plan_meals_plan_id"), table_name="plan_meals")
    op.drop_table("plan_meals")
    op.drop_index(op.f("ix_plan_exercises_plan_id"), table_name="plan_exercises")
    op.drop_table("plan_exercises")
    op.drop_table("nutrition_plans")
    op.drop_index(op.f("ix_injury_attachments_injury_id"), table_name="injury_attachments")
    op.drop_table("injury_attachments")
    op.drop_table("user_profiles")
    op.drop_table("user_food_allergies")
    op.drop_index("ix_specialist_patients_patient", table_name="specialist_patients")
    op.drop_table("specialist_patients")
    op.drop_index("ix_plans_user_status", table_name="plans")
    op.drop_index(op.f("ix_plans_status"), table_name="plans")
    op.drop_table("plans")
    op.drop_index("ix_readings_user_date", table_name="physiological_readings")
    op.drop_table("physiological_readings")
    op.drop_index("ix_injuries_user_status", table_name="injuries")
    op.drop_index(op.f("ix_injuries_user_id"), table_name="injuries")
    op.drop_index(op.f("ix_injuries_status"), table_name="injuries")
    op.drop_index(op.f("ix_injuries_injury_type_id"), table_name="injuries")
    op.drop_table("injuries")
    op.drop_table("food_allergens")
    op.drop_table("exercise_contraindications")
    op.drop_index("ix_daily_logs_user_date", table_name="daily_logs")
    op.drop_table("daily_logs")
    op.drop_index("ix_injury_types_region_active", table_name="injury_types")
    op.drop_table("injury_types")
    op.drop_index(
        "ix_foods_name_ar_trgm",
        table_name="foods",
        postgresql_using="gin",
        postgresql_ops={"name_ar": "gin_trgm_ops"},
    )
    op.drop_index("ix_foods_category_active", table_name="foods")
    op.drop_table("foods")
    op.drop_index("ix_exercises_region_active", table_name="exercises")
    op.drop_index("ix_exercises_category_difficulty", table_name="exercises")
    op.drop_table("exercises")
    # أنواع ENUM لا تُحذف مع الجداول التي تستخدمها — لا بد من حذف صريح،
    # وإلا فشل الـ upgrade التالي بـ "type already exists".
    op.drop_constraint("id_role", "users", type_="unique")

    for enum_name in NEW_ENUM_TYPES:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
