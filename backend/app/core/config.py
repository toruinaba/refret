from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache

# Resolve project root from this file: backend/app/core/config.py -> refret/
# parent=core, parent.parent=app, parent.parent.parent=backend, parent.parent.parent.parent=refret
PROJECT_ROOT = Path(__file__).resolve().parents[3]

class Settings(BaseSettings):
    APP_NAME: str = "Refret Backend"
    DATA_DIR: str = str(PROJECT_ROOT / "data")
    
    # AI Settings
    LLM_PROVIDER: str = "openai"
    OPENAI_API_KEY: str | None = None
    LLM_MODEL: str = "gpt-3.5-turbo"
    
    # Defaults
    SYSTEM_PROMPT: str = (
        "You are a helpful assistant summarizing a guitar lesson. "
        "Extract key points, chords mentioned, and techniques practiced. "
        "Return a JSON object with keys: 'summary', 'key_points' (list), 'chords' (list). "
        "IMPORTANT: Please write the summary and key points in Japanese."
    )

    class Config:
        env_file = str(PROJECT_ROOT / ".env")

@lru_cache()
def get_settings():
    return Settings()
