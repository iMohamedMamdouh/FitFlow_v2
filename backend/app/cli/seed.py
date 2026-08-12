"""تهيئة أول حساب مدير.

    python -m app.cli.seed

آمن للتكرار: لو المدير موجود بالفعل لا يفعل شيئًا. لا يُنشئ أي بيانات
تجريبية أخرى — قاعدة بيانات فيها مستخدمون وهميون خطر في نظام طبي.
"""

from __future__ import annotations

import asyncio
import sys

from sqlalchemy import select

from app.core.config import get_settings
from app.core.db import SessionFactory, engine
from app.core.security import hash_password
from app.models.user import User, UserRole

_DEFAULT_PASSWORD = "ChangeMe_Admin_2026!"


async def seed_first_admin() -> int:
    settings = get_settings()
    email = settings.first_admin_email.strip().lower()
    password = settings.first_admin_password.get_secret_value()

    # حاجز صريح: كلمة السر الافتراضية للتطوير فقط.
    if settings.is_production and password == _DEFAULT_PASSWORD:
        print(
            "✗ رُفض التنفيذ: FIRST_ADMIN_PASSWORD ما زالت القيمة الافتراضية في بيئة إنتاج.",
            file=sys.stderr,
        )
        return 1

    async with SessionFactory() as session:
        existing_admin = await session.scalar(
            select(User.id).where(User.role == UserRole.ADMIN).limit(1)
        )
        if existing_admin is not None:
            print("• يوجد حساب مدير بالفعل — لا حاجة للتهيئة.")
            return 0

        session.add(
            User(
                email=email,
                password_hash=hash_password(password),
                full_name=settings.first_admin_name,
                role=UserRole.ADMIN,
            )
        )
        await session.commit()

    print(f"✓ تم إنشاء حساب المدير: {email}")
    if password == _DEFAULT_PASSWORD:
        print("⚠️  كلمة السر هي القيمة الافتراضية — غيّرها فورًا.")
    return 0


async def _main() -> int:
    try:
        return await seed_first_admin()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
