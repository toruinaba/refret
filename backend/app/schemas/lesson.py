from pydantic import BaseModel, Field
from typing import List, Optional

class KeyPoint(BaseModel):
    point: str = Field(description="The key learning point or topic content in Japanese")
    timestamp: str = Field(description="The closest timestamp in MM:SS format from the source text")

class LessonSummary(BaseModel):
    summary: str = Field(description="Concise summary of the lesson content in Japanese")
    key_points: List[KeyPoint] = Field(description="List of key learning points with timestamps")
    chords: List[str] = Field(description="List of chord names mentioned (e.g. Am7, G)")
