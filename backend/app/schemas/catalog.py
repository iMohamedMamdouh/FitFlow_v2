"""مخططات القاعدة العلمية المقروءة من الواجهة.

القراءة فقط: تعديل المحتوى العلمي يتم من لوحة المدير (المرحلة 10)، ولا
يوجد أي مسار يسمح لمريض بإضافة نوع إصابة أو صنف طعام.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict

from app.core.enums import BodyRegion


class InjuryTypeRead(BaseModel):
    """نوع إصابة كما يظهر في قائمة اختيار فورم التقييم.

    ``is_clinically_reviewed`` جزء من الرد لا تفصيلة داخلية: الواجهة
    مُلزَمة بتمييز المحتوى غير المراجَع أمام المستخدم (ADR-003).
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name_ar: str
    name_en: str | None
    body_region: BodyRegion
    description_ar: str | None
    is_clinically_reviewed: bool


__all__ = ["InjuryTypeRead"]
