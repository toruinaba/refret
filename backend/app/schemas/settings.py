from pydantic import BaseModel, Field
from typing import Optional

class SettingsUpdate(BaseModel):
    llm_provider: Optional[str] = Field(None, description="LLM Provider (openai, etc)")
    openai_api_key: Optional[str] = Field(None, description="OpenAI API Key")
    llm_model: Optional[str] = Field(None, description="Model name (e.g. gpt-4o)")
    system_prompt: Optional[str] = Field(None, description="System prompt for summarization")
    
    # Audio Processing
    demucs_model: Optional[str] = Field(None, description="Demucs model name (htdemucs, etc)")
    demucs_shifts: Optional[int] = Field(None, ge=0, description="Number of random shifts for separation")
    demucs_overlap: Optional[float] = Field(None, ge=0.0, le=0.99, description="Overlap between segments")
    
    # Whisper
    whisper_model: Optional[str] = Field(None, description="Whisper model size (tiny, base, small, medium, large)")
    whisper_beam_size: Optional[int] = Field(None, ge=1, description="Beam size for transcription")
    
    # Basic Pitch
    bp_onset_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Note onset detection sensitivity")
    bp_min_frequency: Optional[float] = Field(None, ge=0.0, description="Minimum allowed frequency (Hz)")
    bp_quantize_grid: Optional[int] = Field(None, ge=1, description="Music21 quantization quarter length divisor (4=16th)")
