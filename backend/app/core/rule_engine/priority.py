"""قرار الأولوية — أول قرار في المحرك وأكثرها أثرًا.

يحدد ما الذي يُبنى للمستخدم أصلًا. الترتيب هنا ليس تفضيلًا بل قاعدة سريرية:
**الإصابة الحادة تسبق كل شيء**. مريض بإصابة حادة وسمنة يحتاج تهدئة الإصابة
أولًا؛ إخضاعه لعجز حراري وتمارين في آن واحد يؤخر الالتئام.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

from app.core.enums import Goal
from app.core.rule_engine.models import InjurySnapshot, ProfileSnapshot
from app.core.rule_engine.version import RULE_ENGINE_VERSION

OBESITY_BMI_THRESHOLD = 30.0
OVERWEIGHT_BMI_THRESHOLD = 25.0


class Priority(enum.StrEnum):
    REHAB_ONLY = "REHAB_ONLY"
    REHAB_PLUS_DIET = "REHAB_PLUS_DIET"
    WEIGHT_LOSS = "WEIGHT_LOSS"
    FITNESS = "FITNESS"


@dataclass(frozen=True, slots=True)
class PriorityDecision:
    priority: Priority
    reasons: tuple[str, ...] = field(default_factory=tuple)
    engine_version: str = RULE_ENGINE_VERSION

    @property
    def includes_rehabilitation(self) -> bool:
        return self.priority in {Priority.REHAB_ONLY, Priority.REHAB_PLUS_DIET}

    @property
    def includes_nutrition(self) -> bool:
        """التغذية جزء من كل مسار عدا التأهيل الخالص."""
        return self.priority is not Priority.REHAB_ONLY


def decide_priority(
    profile: ProfileSnapshot,
    injuries: tuple[InjurySnapshot, ...] = (),
) -> PriorityDecision:
    """يختار المسار العلاجي بناءً على الإصابات ومؤشر كتلة الجسم والهدف."""
    active = tuple(injury for injury in injuries if injury.is_active)
    acute = tuple(injury for injury in active if injury.is_acute)
    bmi = profile.bmi

    if acute:
        return PriorityDecision(
            priority=Priority.REHAB_ONLY,
            reasons=(
                f"إصابة حادة ({acute[0].injury_type_slug}) — التأهيل يسبق أي هدف آخر",
                "لا عجز حراري أثناء المرحلة الحادة حتى لا يتأخر الالتئام",
            ),
        )

    if active:
        if bmi >= OBESITY_BMI_THRESHOLD:
            return PriorityDecision(
                priority=Priority.REHAB_PLUS_DIET,
                reasons=(
                    f"إصابة نشطة ({active[0].injury_type_slug}) مع مؤشر كتلة {bmi:.1f}",
                    "الوزن الزائد يبطئ التأهيل، فيمشي المساران معًا",
                    "تخفيف الحمل يأتي من العجز الحراري لا من تمارين مجهدة",
                ),
            )
        return PriorityDecision(
            priority=Priority.REHAB_ONLY,
            reasons=(f"إصابة نشطة ({active[0].injury_type_slug}) بلا وزن زائد يعيق التأهيل",),
        )

    if bmi >= OBESITY_BMI_THRESHOLD:
        return PriorityDecision(
            priority=Priority.WEIGHT_LOSS,
            reasons=(f"مؤشر كتلة الجسم {bmi:.1f} في نطاق السمنة",),
        )

    if profile.goal is Goal.WEIGHT_LOSS and bmi >= OVERWEIGHT_BMI_THRESHOLD:
        return PriorityDecision(
            priority=Priority.WEIGHT_LOSS,
            reasons=(f"هدف إنقاص الوزن مع مؤشر كتلة {bmi:.1f} فوق الطبيعي",),
        )

    return PriorityDecision(
        priority=Priority.FITNESS,
        reasons=("لا إصابة نشطة ومؤشر كتلة الجسم ضمن النطاق الصحي",),
    )


__all__ = ["Priority", "PriorityDecision", "decide_priority"]
