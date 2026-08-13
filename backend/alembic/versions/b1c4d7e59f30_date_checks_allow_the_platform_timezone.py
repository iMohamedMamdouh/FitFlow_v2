"""قيود التواريخ تتّسع لتوقيت المنصة

القيود كانت ``<= CURRENT_DATE``، و``CURRENT_DATE`` تاريخ **خادم قاعدة
البيانات** (UTC في النشر وفي التكامل المستمر). المنصة تعمل بتوقيت
``Africa/Cairo``، فبين 21:00 و24:00 بتوقيت UTC يكون اليوم عند المستخدم قد
بدأ فعلًا، وترفض قاعدة البيانات تسجيله كأنه في المستقبل — ثلاث ساعات كل
ليلة.

الحل ليس إلغاء الحارس: القيد هنا **سياج ضد القيم العبثية** (تاريخ في 2050)
لا القاعدة الدقيقة، والقاعدة الدقيقة في طبقة التطبيق حيث يُعرف توقيت
المنصة (``app/core/clock.py``). فرق اليوم الواحد يكفي لأي منطقة زمنية على
الأرض (‎-12 إلى ‎+14).

Revision ID: b1c4d7e59f30
Revises: 7a574d0426b0
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "b1c4d7e59f30"
down_revision: str | None = "7a574d0426b0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (الجدول، العمود، الاسم المجرَّد للقيد)
# الاسم مجرَّد لأن اصطلاح التسمية في `alembic/env.py` يضيف `ck_<جدول>_`
# تلقائيًا عند الإنشاء — وتمريره كاملًا يُنتج بادئة مكرَّرة.
_DATE_CHECKS = [
    ("daily_logs", "log_date", "log_date_not_in_future"),
    ("injuries", "injury_date", "injury_date_not_in_future"),
    ("physiological_readings", "reading_date", "reading_date_not_in_future"),
    ("user_profiles", "birth_date", "birth_date_not_in_future"),
]


def _rebuild(expression: str) -> None:
    for table, column, name in _DATE_CHECKS:
        op.drop_constraint(op.f(f"ck_{table}_{name}"), table, type_="check")
        op.create_check_constraint(name, table, expression.format(column=column))


def upgrade() -> None:
    _rebuild("{column} <= CURRENT_DATE + 1")


def downgrade() -> None:
    _rebuild("{column} <= CURRENT_DATE")
