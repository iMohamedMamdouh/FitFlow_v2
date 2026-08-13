"""نقطة دخول التطبيق."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, auth, catalog, health, me, plans, specialist, users
from app.core.config import get_settings
from app.core.db import engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logger.info("بدء التشغيل — البيئة: %s", settings.environment)
    yield
    await engine.dispose()
    logger.info("إيقاف التشغيل — تم إغلاق اتصالات قاعدة البيانات")


def create_app() -> FastAPI:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)

    app = FastAPI(
        title=f"{settings.project_name} API",
        version="0.1.0",
        description="منصة ذكية للصحة والتأهيل الرياضي — أداة دعم قرار للأخصائيين.",
        # التوثيق التفاعلي متاح خارج بيئة الإنتاج فقط
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None if settings.is_production else "/redoc",
        openapi_url=None if settings.is_production else "/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(auth.router, prefix=settings.api_v1_prefix)
    app.include_router(users.router, prefix=settings.api_v1_prefix)
    app.include_router(admin.router, prefix=settings.api_v1_prefix)
    app.include_router(catalog.router, prefix=settings.api_v1_prefix)
    app.include_router(me.router, prefix=settings.api_v1_prefix)
    app.include_router(plans.router, prefix=settings.api_v1_prefix)
    app.include_router(specialist.router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
