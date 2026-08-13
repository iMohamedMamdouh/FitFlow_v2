"""قراءة القاعدة العلمية — مسارات عرض فقط.

الواجهة تحتاج أنواع الإصابات لتبني قائمة الاختيار في فورم التقييم
(الخطوة 7.5). بدون هذا المسار كان المستخدم سيُطالَب بكتابة معرّف نوع
الإصابة يدويًا، وهو ما ينتهي دائمًا بمعرّف خاطئ.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.deps import CurrentUser
from app.core.enums import BodyRegion
from app.models.catalog import InjuryType
from app.schemas.catalog import InjuryTypeRead

router = APIRouter(prefix="/catalog", tags=["catalog"])

Session = Annotated[AsyncSession, Depends(get_session)]


@router.get("/injury-types", response_model=list[InjuryTypeRead])
async def list_injury_types(
    user: CurrentUser,
    session: Session,
    body_region: Annotated[BodyRegion | None, Query()] = None,
) -> list[InjuryType]:
    """أنواع الإصابات المفعّلة، مرتّبة بالمنطقة ثم الاسم."""
    statement = select(InjuryType).where(InjuryType.is_active.is_(True))
    if body_region is not None:
        statement = statement.where(InjuryType.body_region == body_region)

    result = await session.scalars(statement.order_by(InjuryType.body_region, InjuryType.name_ar))
    return list(result)


__all__ = ["router"]
