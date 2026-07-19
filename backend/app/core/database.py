"""
PostgreSQL Database — Async SQLAlchemy Engine

Provides:
- Async engine and session factory
- Dependency injection for FastAPI routes
- Base model for all ORM models
- Startup/shutdown lifecycle hooks
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


# --- Engine & Session Factory ---
database_url = settings.DATABASE_URL.replace(
    "postgresql://",
    "postgresql+asyncpg://",
    1,
)

print("DATABASE URL:", database_url)

engine = create_async_engine(
    database_url,
    echo=settings.APP_DEBUG,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# --- Lifecycle ---
async def init_db():
    """Initialize database and create tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connection pool. Called on app shutdown."""
    await engine.dispose()


# --- FastAPI Dependency ---
async def get_db() -> AsyncSession:
    """
    Dependency that provides an async database session.
    Usage in routes:
        async def my_route(db: AsyncSession = Depends(get_db)):
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
