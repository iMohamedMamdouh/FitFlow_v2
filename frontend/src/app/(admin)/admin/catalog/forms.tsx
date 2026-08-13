"use client";

import { useActionState } from "react";
import { useTranslations } from "next-intl";

import { Alert } from "@/components/ui/alert";
import { CheckboxField, SelectField, TextAreaField, TextField } from "@/components/ui/field";
import { SubmitButton } from "@/components/ui/submit-button";
import {
  ALLERGENS,
  BODY_REGIONS,
  EXERCISE_CATEGORIES,
  EXERCISE_DIFFICULTIES,
  FOOD_CATEGORIES,
  type ExerciseRow,
  type FoodRow,
  type InjuryTypeRow,
} from "@/lib/api/schema";
import { EMPTY_ADMIN_STATE, checkedOf, listOf, textOf } from "../users/state";
import {
  recordReviewAction,
  saveExerciseAction,
  saveFoodAction,
  saveInjuryTypeAction,
} from "./actions";

/**
 * نماذج القاعدة العلمية.
 *
 * الإنشاء والتعديل نموذج واحد لكل كيان: الفرق معرّف موجود أو `null`،
 * ونسختان تعنيان حقلًا يُضاف في إحداهما ويُنسى في الأخرى.
 *
 * لا يوجد زر حذف في أي منها. التعطيل حقل داخل النموذج نفسه — الخطط
 * المولَّدة تشير إلى هذا المحتوى، والحذف يترك خطة مريض تشير إلى لا شيء.
 *
 * `key={state.attempt}` على كل نموذج ليس تفصيلة: React يُعيد ضبط النموذج
 * بعد انتهاء الـ Server Action، فرفضٌ من الخادم كان يمحو عشرين حقلًا
 * كتبها المدير. إعادة التركيب بمفتاح جديد تجعل القيم المعادة في الحالة
 * هي القيم الابتدائية — تغيير `defaultValue` وحده لا يمسّ حقلًا مركَّبًا.
 */

function useCatalog() {
  return useTranslations("admin.catalog");
}

// ----------------------------------------------------------------- الأغذية
export function FoodForm({ food }: { food?: FoodRow }) {
  const t = useCatalog();
  const enums = useTranslations("enums");
  const [state, submit] = useActionState(
    saveFoodAction.bind(null, food?.id ?? null),
    EMPTY_ADMIN_STATE,
  );

  return (
    <form key={state.attempt} action={submit} className="flex flex-col gap-4">
      {state.error !== null && <Alert tone="danger">{state.error}</Alert>}
      {state.message !== null && <Alert tone="success">{state.message}</Alert>}

      <div className="grid gap-4 sm:grid-cols-2">
        <TextField
          label={t("nameAr")}
          name="name_ar"
          defaultValue={textOf(state.values, "name_ar", food?.name_ar ?? "")}
          required
        />
        <TextField
          label={t("nameEn")}
          name="name_en"
          defaultValue={textOf(state.values, "name_en", food?.name_en ?? "")}
        />
        <SelectField
          label={t("category")}
          name="category"
          defaultValue={textOf(state.values, "category", food?.category ?? "other")}
        >
          {FOOD_CATEGORIES.map((value) => (
            <option key={value} value={value}>
              {enums(`foodCategory.${value}`)}
            </option>
          ))}
        </SelectField>
        <TextField
          label={t("calories")}
          name="calories_per_100g"
          type="number"
          step="0.1"
          min={0}
          max={950}
          defaultValue={textOf(state.values, "calories_per_100g", food?.calories_per_100g ?? "")}
          required
        />
        <TextField
          label={t("protein")}
          name="protein_g"
          type="number"
          step="0.1"
          min={0}
          max={100}
          defaultValue={textOf(state.values, "protein_g", food?.protein_g ?? "")}
          required
        />
        <TextField
          label={t("carbs")}
          name="carbs_g"
          type="number"
          step="0.1"
          min={0}
          max={100}
          defaultValue={textOf(state.values, "carbs_g", food?.carbs_g ?? "")}
          required
        />
        <TextField
          label={t("fat")}
          name="fat_g"
          type="number"
          step="0.1"
          min={0}
          max={100}
          defaultValue={textOf(state.values, "fat_g", food?.fat_g ?? "")}
          required
        />
        <TextField
          label={t("fiber")}
          name="fiber_g"
          type="number"
          step="0.1"
          min={0}
          max={100}
          defaultValue={textOf(state.values, "fiber_g", food?.fiber_g ?? "0")}
        />
      </div>

      <fieldset className="flex flex-col gap-2">
        <legend className="text-faint text-[0.7rem] font-semibold tracking-[0.1em] uppercase">
          {t("allergens")}
        </legend>
        <div className="flex flex-wrap gap-x-5 gap-y-2">
          {ALLERGENS.map((allergen) => (
            <label key={allergen} className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                name="allergens"
                value={allergen}
                defaultChecked={listOf(state.values, "allergens", food?.allergens ?? []).includes(
                  allergen,
                )}
                className="accent-accent size-4"
              />
              {enums(`allergen.${allergen}`)}
            </label>
          ))}
        </div>
      </fieldset>

      <CheckboxField
        label={t("isActive")}
        name="is_active"
        defaultChecked={checkedOf(state.values, "is_active", food?.is_active ?? true)}
      />

      <div>
        <SubmitButton pendingLabel={t("saving")}>{t("save")}</SubmitButton>
      </div>
    </form>
  );
}

// ---------------------------------------------------------------- التمارين
export function ExerciseForm({ exercise }: { exercise?: ExerciseRow }) {
  const t = useCatalog();
  const enums = useTranslations("enums");
  const [state, submit] = useActionState(
    saveExerciseAction.bind(null, exercise?.id ?? null),
    EMPTY_ADMIN_STATE,
  );

  return (
    <form key={state.attempt} action={submit} className="flex flex-col gap-4">
      {state.error !== null && <Alert tone="danger">{state.error}</Alert>}
      {state.message !== null && <Alert tone="success">{state.message}</Alert>}

      <div className="grid gap-4 sm:grid-cols-2">
        <TextField
          label={t("nameAr")}
          name="name_ar"
          defaultValue={textOf(state.values, "name_ar", exercise?.name_ar ?? "")}
          required
        />
        <TextField
          label={t("nameEn")}
          name="name_en"
          defaultValue={textOf(state.values, "name_en", exercise?.name_en ?? "")}
        />
        <TextField
          label={t("slug")}
          hint={t("slugHint")}
          name="slug"
          defaultValue={textOf(state.values, "slug", exercise?.slug ?? "")}
          pattern="[a-z0-9\-]+"
          required
        />
        <SelectField
          label={t("category")}
          name="category"
          defaultValue={textOf(state.values, "category", exercise?.category ?? "strength")}
        >
          {EXERCISE_CATEGORIES.map((value) => (
            <option key={value} value={value}>
              {enums(`exerciseCategory.${value}`)}
            </option>
          ))}
        </SelectField>
        <SelectField
          label={t("difficulty")}
          name="difficulty"
          defaultValue={textOf(state.values, "difficulty", exercise?.difficulty ?? "beginner")}
        >
          {EXERCISE_DIFFICULTIES.map((value) => (
            <option key={value} value={value}>
              {enums(`exerciseDifficulty.${value}`)}
            </option>
          ))}
        </SelectField>
        <SelectField
          label={t("region")}
          name="primary_region"
          defaultValue={textOf(state.values, "primary_region", exercise?.primary_region ?? "knee")}
        >
          {BODY_REGIONS.map((value) => (
            <option key={value} value={value}>
              {enums(`bodyRegion.${value}`)}
            </option>
          ))}
        </SelectField>
        <TextField
          label={t("targetMuscles")}
          hint={t("listHint")}
          name="target_muscles"
          defaultValue={textOf(
            state.values,
            "target_muscles",
            exercise?.target_muscles.join("، ") ?? "",
          )}
        />
        <TextField
          label={t("equipment")}
          hint={t("listHint")}
          name="equipment"
          defaultValue={textOf(state.values, "equipment", exercise?.equipment.join("، ") ?? "")}
        />
      </div>

      <TextAreaField
        label={t("instructions")}
        name="instructions_ar"
        rows={3}
        defaultValue={textOf(state.values, "instructions_ar", exercise?.instructions_ar ?? "")}
      />
      <TextField
        label={t("videoUrl")}
        name="video_url"
        defaultValue={textOf(state.values, "video_url", exercise?.video_url ?? "")}
      />
      <CheckboxField
        label={t("isActive")}
        name="is_active"
        defaultChecked={checkedOf(state.values, "is_active", exercise?.is_active ?? true)}
      />

      <div>
        <SubmitButton pendingLabel={t("saving")}>{t("save")}</SubmitButton>
      </div>
    </form>
  );
}

// ----------------------------------------------------------- أنواع الإصابات
export function InjuryTypeForm({ injuryType }: { injuryType?: InjuryTypeRow }) {
  const t = useCatalog();
  const enums = useTranslations("enums");
  const [state, submit] = useActionState(
    saveInjuryTypeAction.bind(null, injuryType?.id ?? null),
    EMPTY_ADMIN_STATE,
  );

  return (
    <form key={state.attempt} action={submit} className="flex flex-col gap-4">
      {state.error !== null && <Alert tone="danger">{state.error}</Alert>}
      {state.message !== null && <Alert tone="success">{state.message}</Alert>}

      <div className="grid gap-4 sm:grid-cols-2">
        <TextField
          label={t("nameAr")}
          name="name_ar"
          defaultValue={textOf(state.values, "name_ar", injuryType?.name_ar ?? "")}
          required
        />
        <TextField
          label={t("nameEn")}
          name="name_en"
          defaultValue={textOf(state.values, "name_en", injuryType?.name_en ?? "")}
        />
        <TextField
          label={t("slug")}
          hint={t("slugHint")}
          name="slug"
          defaultValue={textOf(state.values, "slug", injuryType?.slug ?? "")}
          pattern="[a-z0-9\-]+"
          required
        />
        <SelectField
          label={t("region")}
          name="body_region"
          defaultValue={textOf(state.values, "body_region", injuryType?.body_region ?? "knee")}
        >
          {BODY_REGIONS.map((value) => (
            <option key={value} value={value}>
              {enums(`bodyRegion.${value}`)}
            </option>
          ))}
        </SelectField>
      </div>

      <TextAreaField
        label={t("description")}
        name="description_ar"
        rows={2}
        defaultValue={textOf(state.values, "description_ar", injuryType?.description_ar ?? "")}
      />
      <TextAreaField
        label={t("phases")}
        hint={t("phasesHint")}
        name="phases"
        rows={6}
        className="font-mono text-xs"
        defaultValue={textOf(
          state.values,
          "phases",
          JSON.stringify(injuryType?.phases ?? [], null, 2),
        )}
      />
      <CheckboxField
        label={t("isActive")}
        name="is_active"
        defaultChecked={checkedOf(state.values, "is_active", injuryType?.is_active ?? true)}
      />

      <div>
        <SubmitButton pendingLabel={t("saving")}>{t("save")}</SubmitButton>
      </div>
    </form>
  );
}

// ---------------------------------------------------------------- المراجعة
export function ReviewForm({
  kind,
  id,
  review,
}: {
  kind: "exercises" | "injury-types";
  id: string;
  review: ExerciseRow["review"];
}) {
  const t = useCatalog();
  const [state, submit] = useActionState(
    recordReviewAction.bind(null, kind, id),
    EMPTY_ADMIN_STATE,
  );

  return (
    <form
      key={state.attempt}
      action={submit}
      className="border-line flex flex-col gap-4 border-t pt-5"
    >
      <div className="flex flex-col gap-1">
        <h4 className="font-display text-sm font-semibold tracking-tight">{t("reviewTitle")}</h4>
        <p className="text-subtle text-xs leading-6">{t("reviewHint")}</p>
      </div>

      {state.error !== null && <Alert tone="danger">{state.error}</Alert>}
      {state.message !== null && <Alert tone="success">{state.message}</Alert>}

      <div className="grid gap-4 sm:grid-cols-2">
        <TextField
          label={t("reviewedBy")}
          name="reviewed_by"
          placeholder={t("reviewedByPlaceholder")}
          defaultValue={textOf(state.values, "reviewed_by", review.reviewed_by ?? "")}
          required
          minLength={2}
        />
        <TextField
          label={t("sourceReference")}
          name="source_reference"
          placeholder={t("sourceReferencePlaceholder")}
          defaultValue={textOf(state.values, "source_reference", review.source_reference ?? "")}
          required
          minLength={3}
        />
      </div>

      <div>
        <SubmitButton variant="outline" pendingLabel={t("recording")}>
          {t("recordReview")}
        </SubmitButton>
      </div>
    </form>
  );
}
