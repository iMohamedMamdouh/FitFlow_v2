import type { components } from "./generated";

/**
 * أسماء مختصرة للأنواع المولَّدة من مواصفة OpenAPI.
 *
 * الملف `generated.ts` يُولَّد آليًا (`npm run gen:api`) ولا يُعدَّل يدويًا،
 * ومساراته الطويلة (`components["schemas"][...]`) تجعل الكود غير مقروء.
 * هذا الملف هو نقطة الاستيراد الوحيدة لبقية الواجهة: لو تغيّر شكل التوليد
 * يتغيّر ملف واحد.
 *
 * ملاحظة مهمة: كل الحقول العشرية (وزن، طول، سعرات ماكرو) تصل **كنص** لأن
 * الخادم يرسل `Decimal` كسلسلة. لا تعاملها كأرقام قبل تمريرها على
 * `toNumber` في `@/lib/format`.
 */

type Schemas = components["schemas"];

export type ActivityLevel = Schemas["ActivityLevel"];
export type AdminUserRow = Schemas["AdminUserRow"];
export type ExerciseCategory = Schemas["ExerciseCategory"];
export type ExerciseDifficulty = Schemas["ExerciseDifficulty"];
export type ExerciseRow = Schemas["ExerciseRow"];
export type FoodCategory = Schemas["FoodCategory"];
export type FoodRow = Schemas["FoodRow"];
export type InjuryTypeRow = Schemas["InjuryTypeRow"];
export type AuditEntryRead = Schemas["AuditEntryRead"];
export type Allergen = Schemas["Allergen"];
export type AttachmentRead = Schemas["AttachmentRead"];
export type BodyRegion = Schemas["InjuryTypeRead"]["body_region"];
export type BodySide = Schemas["BodySide"];
export type DailyLogCreate = Schemas["DailyLogCreate"];
export type DailyLogRead = Schemas["DailyLogRead"];
export type Gender = Schemas["Gender"];
export type Goal = Schemas["Goal"];
export type InjuryCreate = Schemas["InjuryCreate"];
export type InjuryRead = Schemas["InjuryRead"];
export type InjuryStatus = Schemas["InjuryStatus"];
export type InjuryTypeRead = Schemas["InjuryTypeRead"];
export type MealRead = Schemas["MealRead"];
export type MealSlot = Schemas["MealSlot"];
export type PlanRead = Schemas["PlanRead"];
export type PlanStatus = Schemas["PlanStatus"];
export type PlanSummary = Schemas["PlanSummary"];
export type PlanTransitionRead = Schemas["PlanTransitionRead"];
export type PatientFlag = Schemas["PatientFlag"];
export type PatientSummary = Schemas["PatientSummary"];
export type PlanType = Schemas["PlanType"];
export type PlatformStats = Schemas["PlatformStats"];
export type ProfileRead = Schemas["ProfileRead"];
export type ProfileUpsert = Schemas["ProfileUpsert"];
export type ReadingCreate = Schemas["ReadingCreate"];
export type ReadingRead = Schemas["ReadingRead"];
export type SpecialistNoteRead = Schemas["SpecialistNoteRead"];
export type TokenPair = Schemas["TokenPair"];
export type UserPublic = Schemas["UserPublic"];
export type UserRole = Schemas["UserRole"];

/** الحالات التي يُسمح للمريض برؤيتها — مطابقة لـ `PlanStatus.is_visible_to_patient`. */
export const PATIENT_VISIBLE_STATUSES = [
  "approved",
  "active",
  "archived",
] as const satisfies readonly PlanStatus[];

export const USER_ROLES = ["patient", "specialist", "admin"] as const satisfies readonly UserRole[];

export const ACTIVITY_LEVELS = [
  "sedentary",
  "light",
  "moderate",
  "active",
  "very_active",
] as const satisfies readonly ActivityLevel[];

export const GOALS = [
  "weight_loss",
  "muscle_gain",
  "maintenance",
  "rehabilitation",
] as const satisfies readonly Goal[];

export const GENDERS = ["male", "female"] as const satisfies readonly Gender[];

export const ALLERGENS = [
  "gluten",
  "dairy",
  "eggs",
  "peanuts",
  "tree_nuts",
  "soy",
  "fish",
  "shellfish",
  "sesame",
] as const satisfies readonly Allergen[];

export const INJURY_STATUSES = [
  "acute",
  "subacute",
  "chronic",
  "recovered",
] as const satisfies readonly InjuryStatus[];

export const BODY_SIDES = [
  "not_applicable",
  "left",
  "right",
  "bilateral",
] as const satisfies readonly BodySide[];

/** ترتيب الإلحاح — نفس ترتيب `PatientFlag` في الخادم. */
export const PATIENT_FLAGS = [
  "needs_review",
  "acute_injury",
  "stalled",
  "not_started",
  "on_track",
] as const satisfies readonly PatientFlag[];

export const FOOD_CATEGORIES = [
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
] as const satisfies readonly FoodCategory[];

export const EXERCISE_CATEGORIES = [
  "strength",
  "mobility",
  "stability",
  "balance",
  "cardio",
  "stretching",
] as const satisfies readonly ExerciseCategory[];

export const EXERCISE_DIFFICULTIES = [
  "beginner",
  "intermediate",
  "advanced",
] as const satisfies readonly ExerciseDifficulty[];

export const BODY_REGIONS = [
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
] as const satisfies readonly BodyRegion[];

export const MEAL_ORDER = [
  "breakfast",
  "lunch",
  "dinner",
  "snack",
] as const satisfies readonly MealSlot[];
