"""التعديل التلقائي: كشف الثبات وكشف الفقد المفرط.

الاتجاهان مقصودان. كشف الثبات وحده يجعل المحرك يدفع دائمًا نحو خفض
السعرات، فينتج انحدارًا لا يتوقف. الفقد الأسرع من الآمن مؤشر خطر يستدعي
**رفع** السعرات، لا إنجازًا يُكافأ.

كل مخرجات هذه الوحدة **اقتراحات** تُولَّد كمسودة وتحتاج اعتماد أخصائي
(ADR-006) — لا تُطبَّق تلقائيًا على خطة مفعّلة.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

from app.core.rule_engine.models import ProfileSnapshot, WeightPoint
from app.core.rule_engine.safety import (
    MAX_SAFE_WEEKLY_LOSS_RATIO,
    MIN_DAYS_FOR_TREND,
    PLATEAU_CALORIE_STEP,
    PLATEAU_THRESHOLD_KG,
    PLATEAU_WINDOW_DAYS,
    InsufficientDataError,
    calorie_floor,
)
from app.core.rule_engine.version import RULE_ENGINE_VERSION


class AdjustmentKind(enum.StrEnum):
    NONE = "none"
    PLATEAU = "plateau"
    LOSING_TOO_FAST = "losing_too_fast"
    FLOOR_REACHED = "floor_reached"


@dataclass(frozen=True, slots=True)
class WeightTrend:
    start: WeightPoint
    end: WeightPoint
    days: int

    @property
    def change_kg(self) -> float:
        """سالب = فقدان وزن."""
        return self.end.weight_kg - self.start.weight_kg

    @property
    def weekly_change_kg(self) -> float:
        return self.change_kg / self.days * 7


@dataclass(frozen=True, slots=True)
class PlanAdjustment:
    kind: AdjustmentKind
    current_calories: int
    suggested_calories: int
    reasons: tuple[str, ...] = field(default_factory=tuple)
    engine_version: str = RULE_ENGINE_VERSION

    @property
    def delta(self) -> int:
        return self.suggested_calories - self.current_calories

    @property
    def requires_specialist_review(self) -> bool:
        """كل تعديل يمر بالأخصائي — لا استثناء."""
        return self.kind is not AdjustmentKind.NONE


def summarize_trend(
    readings: tuple[WeightPoint, ...],
    window_days: int = PLATEAU_WINDOW_DAYS,
) -> WeightTrend:
    """يلخّص اتجاه الوزن داخل النافذة، أو يمتنع صراحةً لقلة البيانات."""
    if len(readings) < 2:
        raise InsufficientDataError("قياسان على الأقل مطلوبان لتحديد اتجاه الوزن")

    ordered = sorted(readings, key=lambda point: point.on)
    latest = ordered[-1]
    window_start = latest.on.toordinal() - window_days
    in_window = [point for point in ordered if point.on.toordinal() >= window_start]

    if len(in_window) < 2:
        raise InsufficientDataError(f"لا توجد قياسات كافية خلال آخر {window_days} يومًا")

    first = in_window[0]
    days = latest.on.toordinal() - first.on.toordinal()
    if days < MIN_DAYS_FOR_TREND:
        raise InsufficientDataError(
            f"المدة بين أول وآخر قياس {days} يومًا — أقل من {MIN_DAYS_FOR_TREND} "
            "لا تكفي لتمييز الاتجاه عن تذبذب الماء اليومي"
        )

    return WeightTrend(start=first, end=latest, days=days)


def evaluate_adjustment(
    profile: ProfileSnapshot,
    current_calories: int,
    readings: tuple[WeightPoint, ...],
    *,
    is_weight_loss_plan: bool = True,
) -> PlanAdjustment:
    """يقترح تعديلًا للسعرات — أو يؤكد بقاء الخطة كما هي."""
    trend = summarize_trend(readings)
    floor = calorie_floor(profile.gender)
    unchanged = PlanAdjustment(
        kind=AdjustmentKind.NONE,
        current_calories=current_calories,
        suggested_calories=current_calories,
        reasons=(f"تغيّر الوزن {trend.change_kg:+.2f} كجم خلال {trend.days} يومًا — ضمن المتوقع",),
    )

    if not is_weight_loss_plan:
        return unchanged

    # فقد أسرع من الآمن — يسبق فحص الثبات لأنه مخاطرة لا نجاح.
    max_weekly_loss = profile.weight_kg * MAX_SAFE_WEEKLY_LOSS_RATIO
    if trend.weekly_change_kg < -max_weekly_loss:
        return PlanAdjustment(
            kind=AdjustmentKind.LOSING_TOO_FAST,
            current_calories=current_calories,
            suggested_calories=current_calories + PLATEAU_CALORIE_STEP,
            reasons=(
                f"الفقد {abs(trend.weekly_change_kg):.2f} كجم أسبوعيًا يتجاوز الحد الآمن "
                f"({max_weekly_loss:.2f} كجم)",
                "الفقد السريع يستهلك الكتلة العضلية ويخفض الأيض — تُرفع السعرات",
            ),
        )

    if trend.change_kg > -PLATEAU_THRESHOLD_KG:
        suggested = current_calories - PLATEAU_CALORIE_STEP
        if suggested < floor:
            return PlanAdjustment(
                kind=AdjustmentKind.FLOOR_REACHED,
                current_calories=current_calories,
                suggested_calories=current_calories,
                reasons=(
                    f"الوزن ثابت ({trend.change_kg:+.2f} كجم في {trend.days} يومًا)",
                    f"خفض السعرات يتجاوز الحد الآمن ({floor}) — لا يُخفَّض",
                    "البديل: رفع النشاط أو مراجعة الالتزام مع الأخصائي",
                ),
            )
        return PlanAdjustment(
            kind=AdjustmentKind.PLATEAU,
            current_calories=current_calories,
            suggested_calories=suggested,
            reasons=(
                f"الوزن ثابت ({trend.change_kg:+.2f} كجم في {trend.days} يومًا)",
                f"خفض {PLATEAU_CALORIE_STEP} سعرة — أو رفع النشاط بما يعادلها",
            ),
        )

    return unchanged


__all__ = [
    "AdjustmentKind",
    "PlanAdjustment",
    "WeightTrend",
    "evaluate_adjustment",
    "summarize_trend",
]
