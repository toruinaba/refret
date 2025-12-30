from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
from typing import List, Dict, Any

from backend.app.services.store import StoreService
from backend.app.core.config import get_settings

router = APIRouter()

def get_store():
    return StoreService()

@router.get("/", response_model=List[Dict[str, Any]])
async def list_lessons(store: StoreService = Depends(get_store)):
    """List all available lessons."""
    return store.list_lessons()

@router.get("/{lesson_id}", response_model=Dict[str, Any])
async def get_lesson(lesson_id: str, store: StoreService = Depends(get_store)):
    """Get metadata for a specific lesson."""
    meta = store.get_lesson_metadata(lesson_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Return basic info plus IDs to help frontend construct audio URLs
    return {
        "id": lesson_id,
        "title": lesson_id,
        **meta
    }

@router.put("/{lesson_id}")
async def update_lesson(lesson_id: str, updates: Dict[str, Any], store: StoreService = Depends(get_store)):
    """Update lesson metadata (memo, tags)."""
    current = store.get_lesson_metadata(lesson_id)
    if not current and not (store.data_dir / lesson_id).exists():
         raise HTTPException(status_code=404, detail="Lesson not found")
         
    # Merge updates
    current.update(updates)
    store.save_lesson_metadata(lesson_id, current)
    return current

@router.get("/{lesson_id}/audio/{track_type}")
async def get_audio_stream(lesson_id: str, track_type: str, store: StoreService = Depends(get_store)):
    """
    Stream audio file.
    track_type: 'vocals' or 'guitar'
    """
    if track_type not in ["vocals", "guitar"]:
        raise HTTPException(status_code=400, detail="Invalid track type")
        
    file_name = f"{track_type}.mp3"
    file_path = store.data_dir / lesson_id / file_name
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
        
    return FileResponse(
        path=file_path,
        media_type="audio/mpeg",
        filename=f"{lesson_id}_{track_type}.mp3"
    )

@router.get("/{lesson_id}/transcript")
async def get_transcript(lesson_id: str, store: StoreService = Depends(get_store)):
    """Get transcript text if available."""
    # Assuming transcript is saved in metadata or a separate file?
    # Original app saved to metadata['transcript'] in some versions or transcript.txt
    # Let's check session_state in app.py logic. 
    # For now, let's look for transcript.txt or metadata.
    
    # Check metadata first
    meta = store.get_lesson_metadata(lesson_id)
    if "transcript" in meta: # If we start saving it there
        return {"transcript": meta["transcript"]}
        
    # Fallback/Migration: Check if transcript.txt exists (if we change storage strategy)
    # The current streamlit app stores it in `st.session_state` but seemingly doesn't persist it plainly 
    # except potentially in `metadata.json` if we modified processor.
    
    # Re-reading processor.py logic: processor returns it, but app.py decides where to save.
    # In `app.py`, save logic is not explicitly dumping transcript to file other than maybe `summary`.
    # Let's assume for now we just return what's in metadata or empty.
    
    return {"transcript": meta.get("transcript", "")}
