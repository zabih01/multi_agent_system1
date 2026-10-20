from functools import lru_cache
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field


class Settings(BaseModel):
    llm_provider: str = "gemini"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    database_path: Path = Path("./multi_agent.db")
    max_concurrency: int = Field(default=4, ge=1, le=64)
    max_retries: int = Field(default=2, ge=0, le=8)
    task_timeout_seconds: float = Field(default=30.0, gt=0, le=3600)
    log_level: str = "INFO"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    load_dotenv()
    return Settings(
        llm_provider=os.getenv("LLM_PROVIDER", "gemini"),
        gemini_api_key=os.getenv("GEMINI_API_KEY") or None,
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        database_path=Path(os.getenv("DATABASE_PATH", "./multi_agent.db")),
        max_concurrency=int(os.getenv("MAX_CONCURRENCY", "4")),
        max_retries=int(os.getenv("MAX_RETRIES", "2")),
        task_timeout_seconds=float(os.getenv("TASK_TIMEOUT_SECONDS", "30")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
