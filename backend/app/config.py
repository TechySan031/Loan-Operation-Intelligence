"""
Application Configuration — Pydantic Settings

All configuration is loaded from environment variables / .env file.
Validates at startup so missing keys fail fast.
"""

from transformers.models.chameleon import image_processing_chameleon_fast
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_env_file() -> str:
    """Find .env file — checks backend/ first, then project root."""
    # When running from backend/
    if os.path.exists(".env"):
        return ".env"
    # Check project root (parent of backend/)
    parent = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", ".env")
    if os.path.exists(parent):
        return os.path.abspath(parent)
    return ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_find_env_file(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Application ---
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"

    # --- PostgreSQL ---
    # NOTE: .env uses ${VAR} shell interpolation which pydantic doesn't support.
    # This default is used when DATABASE_URL isn't resolved properly.
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "loi_user"
    POSTGRES_PASSWORD: str = "changeme"
    POSTGRES_DB: str = "loan_operation_intelligence"
    DATABASE_URL: str = ""

    # --- Redis ---
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = ""

    # --- OpenAI ---
    OPENAI_API_KEY: str = ""
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_LLM_MODEL: str = "gpt-4o"
    OPENAI_LLM_MODEL_MINI: str = "gpt-4o-mini"

    # --- Pinecone ---
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX_NAME: str = "loan-kb"
    PINECONE_ENVIRONMENT: str = "us-east-1"

    # --- Vapi.ai ---
    VAPI_API_KEY: str = ""
    VAPI_ASSISTANT_ID_EN: str = ""
    VAPI_ASSISTANT_ID_PH: str = ""
    VAPI_ASSISTANT_ID_ID: str = ""
    VAPI_PHONE_NUMBER_ID: str = ""
    VAPI_WEBHOOK_SECRET: str = ""
    VAPI_SERVER_URL: str = ""

    # --- Deepgram ---
    DEEPGRAM_API_KEY: str = ""

    # --- Langfuse ---
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    # --- PII ---
    PII_DETECTION_ENABLED: bool = True
    PII_DETECTION_THRESHOLD: float = 0.7

    def model_post_init(self, __context):
        # Convert Railway DATABASE_URL to asyncpg format
        if self.DATABASE_URL.startswith("postgresql://"):
            self.DATABASE_URL = self.DATABASE_URL.replace(
                "postgresql://",
                "postgresql+asyncpg://",
                1,
            )

        # Build Redis URL only if needed
        if not self.REDIS_URL or "${" in self.REDIS_URL:
            self.REDIS_URL = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"


settings = Settings()
