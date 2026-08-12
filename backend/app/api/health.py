"""مسارات فحص الصحة.

- ``/health/live``  : هل العملية تعمل؟ (لا تلمس أي خدمة خارجية)
- ``/health/ready`` : هل التطبيق جاهز لخدمة الطلبات؟ (Postgres + Redis)

الفصل بين الاثنين مقصود: منسّق الحاويات يعيد تشغيل الحاوية عند فشل
``live`` فقط، ويوقف توجيه الطلبات إليها عند فشل ``ready``.
"""

from __future__ import annotations

from typing import Literal

import redis.asyncio as aioredis
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text

from app.core.config import get_settings
from app.core.db import engine

router = APIRouter(tags=["health"])


class LivenessResponse(BaseModel):
    status: Literal["ok"]
    service: str


class DependencyStatus(BaseModel):
    postgres: Literal["ok", "error"]
    redis: Literal["ok", "error"]


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    dependencies: DependencyStatus


@router.get("/health/live", response_model=LivenessResponse)
async def liveness() -> LivenessResponse:
    return LivenessResponse(status="ok", service=get_settings().project_name)


async def _check_postgres() -> bool:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        return False
    return True


async def _check_redis() -> bool:
    client = aioredis.from_url(get_settings().redis_url)
    try:
        await client.ping()
    except Exception:
        return False
    finally:
        await client.aclose()
    return True


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness() -> JSONResponse:
    postgres_ok = await _check_postgres()
    redis_ok = await _check_redis()
    all_ok = postgres_ok and redis_ok

    body = ReadinessResponse(
        status="ready" if all_ok else "not_ready",
        dependencies=DependencyStatus(
            postgres="ok" if postgres_ok else "error",
            redis="ok" if redis_ok else "error",
        ),
    )
    return JSONResponse(
        content=body.model_dump(),
        status_code=status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE,
    )
