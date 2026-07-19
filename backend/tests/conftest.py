"""Pytest configuration and PostgreSQL-backed fixtures."""

import os

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import app


TEST_DATABASE_URL = os.getenv(
    "LOI_TEST_DATABASE_URL",
    "postgresql+asyncpg://loi_user:changeme@localhost:5432/loan_operation_intelligence_test",
)


@pytest_asyncio.fixture
async def db_session():
    """Provide an isolated PostgreSQL session for each test."""
    if "/loan_operation_intelligence_test" not in TEST_DATABASE_URL:
        raise RuntimeError("LOI_TEST_DATABASE_URL must target loan_operation_intelligence_test")

    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session):
    """Create a FastAPI client with the PostgreSQL test session injected."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client
    app.dependency_overrides.clear()