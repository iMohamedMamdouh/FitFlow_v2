import { getTranslations } from "next-intl/server";

import { Badge } from "@/components/ui/alert";
import type { PatientFlag } from "@/lib/api/schema";

/**
 * لون المؤشر يحمل معناه.
 *
 * "تحتاج مراجعة" بالطيني لا بالأحمر: إنه عمل منتظر لا خطر. الأحمر محجوز
 * للإصابة الحادة وحدها، فلا تفقد الشاشة قدرتها على التمييز حين يكون كل
 * شيء ملوّنًا بالإنذار.
 */
const TONES = {
  needs_review: "clay",
  acute_injury: "danger",
  stalled: "warning",
  not_started: "neutral",
  on_track: "success",
} as const satisfies Record<PatientFlag, "clay" | "danger" | "warning" | "neutral" | "success">;

export async function PatientFlagBadge({ flag }: { flag: PatientFlag }) {
  const t = await getTranslations("specialist.flags");
  return <Badge tone={TONES[flag]}>{t(flag)}</Badge>;
}

export { TONES as PATIENT_FLAG_TONES };
