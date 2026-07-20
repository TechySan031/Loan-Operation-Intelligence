"""
Loan Operation Intelligence — FastAPI Application Factory

Main entry point. Initializes the FastAPI app, registers routers,
sets up middleware, and manages application lifecycle (startup/shutdown).
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import tools

from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown hooks."""
    # --- Startup ---
    # We offload service checks and client initializations to a background task
    # so Uvicorn can immediately bind to $PORT and start accepting connections.
    async def initialize_services():
        # Database
        try:
            from app.core.database import init_db
            await init_db()
            logger.info("✅ PostgreSQL connection verified")
        except Exception as e:
            logger.error(f"❌ PostgreSQL connection failed: {e}")

        # Redis — required for nudges, optional otherwise
        try:
            from app.core.redis import init_redis
            await init_redis()
            logger.info("✅ Redis connected")
        except Exception as e:
            logger.warning(f"⚠️  Redis unavailable: {e} — nudge streaming disabled")

        # Pinecone — optional (RAG won't work without it)
        try:
            from app.core.pinecone_client import init_pinecone
            # Pinecone list_indexes() performs blocking network DNS lookups.
            # Run in executor to prevent freezing the ASGI loop thread.
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, init_pinecone)
            logger.info("✅ Pinecone connected")
        except Exception as e:
            logger.warning(f"⚠️  Pinecone unavailable: {e} — RAG disabled")

        # Langfuse — optional (observability)
        try:
            from app.core.langfuse_client import init_langfuse
            init_langfuse()
            logger.info("✅ Langfuse initialized")
        except Exception as e:
            logger.warning(f"⚠️  Langfuse unavailable: {e}")

        logger.info("🚀 All external services initialization checks completed")

    # Launch initialization concurrently
    asyncio.create_task(initialize_services())
    logger.info("🚀 Startup lifecycle initialized. Port binding in progress.")

    yield

   
    # --- Shutdown ---
    try:
        from app.core.redis import close_redis
        await close_redis()
    except Exception:
        pass

    logger.info("👋 Application shutdown complete")

def create_app() -> FastAPI:
    """Factory function to create and configure the FastAPI application."""
    from app.routes import voice, knowledge, calls, nudges, evaluation, health

    app = FastAPI(
        title="Loan Operation Intelligence",
        description="AI platform for intelligent loan pre-due reminders with voice agents, knowledge base, and real-time nudges",
        version="1.0.0",
        lifespan=lifespan,
    )

    # --- CORS Middleware ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://loan-operation-intelligence.vercel.app",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # --- Register Routers ---
    app.include_router(health.router, prefix="/api", tags=["Health"])
    app.include_router(
        tools.router,
        prefix="/api/tools",
        tags=["Tools"]
    )
    
    app.include_router(voice.router, prefix="/api/voice", tags=["Voice Agent"])
    app.include_router(knowledge.router, prefix="/api/knowledge", tags=["Knowledge Base"])
    app.include_router(calls.router, prefix="/api/calls", tags=["Calls"])
    app.include_router(nudges.router, prefix="/api/nudges", tags=["Nudges"])
    app.include_router(evaluation.router, prefix="/api/eval", tags=["Evaluation"])

    return app


app = create_app()
