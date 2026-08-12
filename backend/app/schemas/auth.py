"""مخططات المصادقة (Contract-First — تُعرَّف قبل المنطق)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.user import UserRole

# 12 حرفًا حد أدنى. البيانات صحية، والحد الشائع (8) لم يعد كافيًا.
Password = Annotated[str, Field(min_length=12, max_length=128)]
FullName = Annotated[str, Field(min_length=2, max_length=200)]


class _EmailNormalizingModel(BaseModel):
    """يوحّد صيغة البريد قبل أي مقارنة أو تخزين."""

    email: EmailStr

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class RegisterRequest(_EmailNormalizingModel):
    """التسجيل العام — يُنشئ حساب مريض دائمًا.

    لا يوجد حقل ``role`` عمدًا: وجوده يعني أن أي شخص يستطيع طلب صلاحيات
    أعلى، وأن أمان النظام يعتمد على تذكّر تجاهله في كل مسار.
    """

    password: Password
    full_name: FullName


class LoginRequest(_EmailNormalizingModel):
    password: Annotated[str, Field(min_length=1, max_length=128)]


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_at: datetime


class UserPublic(BaseModel):
    """التمثيل الوحيد المسموح بإرجاعه للمستخدم — بدون تجزئة كلمة السر."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class CreateStaffRequest(_EmailNormalizingModel):
    """إنشاء حساب أخصائي أو مدير — متاح للمدير فقط."""

    password: Password
    full_name: FullName
    role: Literal[UserRole.SPECIALIST, UserRole.ADMIN]


__all__ = [
    "CreateStaffRequest",
    "LoginRequest",
    "RefreshRequest",
    "RegisterRequest",
    "TokenPair",
    "UserPublic",
]
