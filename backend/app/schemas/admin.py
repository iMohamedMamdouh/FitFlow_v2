"""مخططات لوحة المدير (المرحلة 10)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import PlanStatus
from app.models.user import UserRole


class AssignedSpecialist(BaseModel):
    """أخصائي مسنَد إلى مريض — بالمعرّف لا بالاسم وحده.

    الاسم كافٍ للعرض وحده، لكن الشاشة تبني عليه أفعالًا (إنهاء الإسناد،
    ترشيح من لم يُسنَد بعد)، والاسم قابل للتكرار بين أخصائيين.
    """

    id: uuid.UUID
    full_name: str


class AdminUserRow(BaseModel):
    """سطر واحد في قائمة المستخدمين.

    الأعداد المرفقة تجيب السؤال الذي يسبق كل قرار في هذه الشاشة: تعطيل
    أخصائي عنده مرضى مسنَدون ليس نفس تعطيل أخصائي بلا مرضى، وترقية مريض
    له سجل سريري ليست نفس ترقية حساب فارغ.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    # الحقلان بلا قيمة افتراضية عمدًا: الخادم يملؤهما دائمًا، والقيمة
    # الافتراضية كانت ستجعلهما اختياريين في العقد المولَّد فتضطر الواجهة
    # للتعامل مع "غير موجود" في حالة لا تحدث.
    #: للأخصائي: عدد مرضاه النشطين. لغيره: صفر.
    assigned_patients: int
    #: للمريض: أخصائيوه النشطون.
    specialists: list[AssignedSpecialist]


class UserUpdateRequest(BaseModel):
    """تعديل مستخدم من لوحة المدير.

    الحقول كلها اختيارية: الشاشة ترسل ما تغيّر فقط، فلا يُعاد إرسال الدور
    مع كل تفعيل/تعطيل — وإرسال قيمة لم تتغيّر هو أكثر ما يُنتج تعديلات
    عرضية في سجل التدقيق.

    كلمة السر ليست هنا عمدًا: تغييرها فعل منفصل له مساره الخاص، ووضعه في
    نفس الطلب يجعل تعديل اسم يحمل معه خطر إبطال جلسات المستخدم.
    """

    full_name: str | None = Field(default=None, min_length=2, max_length=200)
    role: UserRole | None = None
    is_active: bool | None = None

    @field_validator("full_name")
    @classmethod
    def _strip(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None


class AssignmentRequest(BaseModel):
    """إسناد مريض إلى أخصائي."""

    specialist_id: uuid.UUID
    patient_id: uuid.UUID


class RoleCount(BaseModel):
    role: UserRole
    total: int
    active: int


class PlanStatusCount(BaseModel):
    status: PlanStatus
    total: int


class PlatformStats(BaseModel):
    """أرقام المنصة.

    كلها من استعلامات مجمَّعة: العدّ في بايثون بعد جلب الصفوف يعني تحميل
    كل مستخدم وكل خطة في الذاكرة لعرض ستة أرقام.

    استهلاك الذكاء الاصطناعي وتكلفته (10.3) ينتظران المرحلة 6 — لا يوجد
    مزوّد بعد، ورقم مختلَق في لوحة إدارة أسوأ من رقم غائب.
    """

    users: list[RoleCount]
    plans: list[PlanStatusCount]
    plans_awaiting_review: int
    patients_without_specialist: int
    active_injuries: int
    acute_injuries: int
    logs_last_7_days: int
    catalog_foods: int
    catalog_exercises: int
    catalog_injury_types: int
    catalog_unreviewed: int


__all__ = [
    "AdminUserRow",
    "AssignedSpecialist",
    "AssignmentRequest",
    "PlanStatusCount",
    "PlatformStats",
    "RoleCount",
    "UserUpdateRequest",
]
