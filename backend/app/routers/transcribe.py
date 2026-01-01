from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import logging
from app.services.transcription import TranscriptionService

router = APIRouter()
logger = logging.getLogger(__name__)

class TranscriptionRequest(BaseModel):
    lesson_id: str
    start_time: float
    end_time: float

@router.post("/")
async def transcribe_audio(req: TranscriptionRequest):
    service = TranscriptionService()
    try:
        abc_notation = service.transcribe_segment(
            req.lesson_id, 
            req.start_time, 
            req.end_time
        )
        return {"abc": abc_notation}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Audio file not found")
    except Exception as e:
        logger.error(f"Transcription failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
