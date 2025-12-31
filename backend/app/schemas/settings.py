from pydantic import BaseModel, Field
from typing import Optional

class SettingsUpdate(BaseModel):
    llm_provider: Optional[str] = Field(None, description="LLM Provider (openai, etc)")
    openai_api_key: Optional[str] = Field(None, description="OpenAI API Key")
    llm_model: Optional[str] = Field(None, description="Model name (e.g. gpt-4o)")
    system_prompt: Optional[str] = Field(None, description="System prompt for summarization")
