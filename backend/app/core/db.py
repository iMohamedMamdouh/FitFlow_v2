"""الاتصال بقاعدة البيانات.

في المرحلة 0 نكتفي بإنشاء المحرك والتحقق من الجاهزية.
النماذج (models) والجلسات تُبنى في المرحلة 1.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

_settings = get_settings()

engine: AsyncEngine = create_async_engine(
    _settings.database_url,
    echo=_settings.debug,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: جلسة قاعدة بيانات لكل طلب."""
    async with SessionFactory() as session:
        yield session


__all__ = ["SessionFactory", "engine", "get_session"]
