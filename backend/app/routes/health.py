"""
Health Check Route

Simple health check and readiness probe.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.redis import get_redis

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic liveness probe."""
    return {"status": "healthy", "service": "loan-operation-intelligence"}


@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Readiness probe — checks all infrastructure dependencies.
    Returns 200 only if PostgreSQL, Redis, and Pinecone are reachable.
    """
    checks = {}

    # PostgreSQL
    try:
        await db.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception as e:
        checks["postgres"] = f"error: {str(e)}"

    # Redis
    try:
        redis = get_redis()
        await redis.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {str(e)}"

    # Pinecone
    try:
        from app.core.pinecone_client import get_pinecone_index
        idx = get_pinecone_index()
        stats = idx.describe_index_stats()
        checks["pinecone"] = f"ok (vectors: {stats.total_vector_count})"
    except Exception as e:
        checks["pinecone"] = f"error: {str(e)}"

    all_ok = all("ok" in v for v in checks.values())
    return {
        "status": "ready" if all_ok else "degraded",
        "checks": checks,
    }
