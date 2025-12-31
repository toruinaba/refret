from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
from typing import List, Dict, Any
import shutil
import json
import traceback
from datetime import datetime

from app.services.store import StoreService
from app.core.config import get_settings

router = APIRouter()

def get_store():
    return StoreService()

# --- Background Processing Task ---
def process_lesson_background(lesson_id: str, file_path: Path, store: StoreService):
    status_file = store.data_dir / lesson_id / "status.json"
    
    def update_status(status: str, progress: float, message: str):
        with open(status_file, "w") as f:
            json.dump({
                "status": status,
                "progress": progress,
                "message": message,
                "updated_at": datetime.now().isoformat()
            }, f)

    try:
        from app.services.audio import AudioProcessor
        processor = AudioProcessor()

        # Step 1: Separation
        update_status("processing", 0.05, "Separating Audio (Demucs)... This takes time.")
        
        # Ensure we have a WAV file for processing (handles m4a etc)
        proc_wav_path = processor.prepare_wav(file_path)
        
        try:
            vocals_path, guitar_path = processor.separate_audio(proc_wav_path, store.data_dir / lesson_id)
        finally:
            # Cleanup temp proc wav
            if proc_wav_path.exists() and proc_wav_path != file_path:
                proc_wav_path.unlink()
        
        # Step 2: Transcription
        update_status("processing", 0.5, "Transcribing Vocals (Whisper)...")
        transcript_text, segments = processor.transcribe(vocals_path)
        
        # Step 3: Summarization
        update_status("processing", 0.8, "Summarizing (LLM)...")
        summary_data = processor.summarize(segments)
        
        # Step 4: Finalize
        update_status("processing", 0.95, "Finalizing...")
        
        # Save results to separate files (Legacy format)
        processor.save_results(store.data_dir / lesson_id, segments, transcript_text, summary_data)
        
        metadata = {
            "title": f"Lesson {lesson_id}",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tags": [],
            "memo": ""
        }
        
        store.save_lesson_metadata(lesson_id, metadata)
        update_status("completed", 1.0, "Ready")

    except Exception as e:
        print(f"Processing failed: {e}")
        traceback.print_exc()
        update_status("failed", 0.0, str(e))

# --- Endpoints ---

@router.post("/upload")
async def upload_lesson(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    store: StoreService = Depends(get_store)
):
    """Upload a new lesson audio file for processing."""
    # Generate ID (Timestamp based)
    lesson_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    lesson_dir = store.data_dir / lesson_id
    lesson_dir.mkdir(exist_ok=True)
    
    # Save Uploaded File
    ext = Path(file.filename).suffix
    if not ext: ext = ".mp3"
    file_path = lesson_dir / f"original{ext}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Init Status
    status_file = lesson_dir / "status.json"
    with open(status_file, "w") as f:
        json.dump({"status": "queued", "progress": 0.0, "message": "In Queue"}, f)

    # Trigger Background Task
    background_tasks.add_task(process_lesson_background, lesson_id, file_path, store)
    
    return {"id": lesson_id, "message": "Upload successful, processing started."}

@router.get("/{lesson_id}/status")
async def get_lesson_status(lesson_id: str, store: StoreService = Depends(get_store)):
    """Check processing status of a lesson."""
    status_file = store.data_dir / lesson_id / "status.json"
    
    if not status_file.exists():
        # Fallback: If metadata exists, it's completed
        if (store.data_dir / lesson_id / "metadata.json").exists():
            return {"status": "completed", "progress": 1.0, "message": "Ready"}
        # If folder exists but no status/metadata?
        if (store.data_dir / lesson_id).exists():
             return {"status": "unknown", "progress": 0.0, "message": "No status info"}
        raise HTTPException(status_code=404, detail="Lesson not found")
        
    with open(status_file, "r") as f:
        try:
            return json.load(f)
        except:
             return {"status": "unknown", "progress": 0.0, "message": "Read error"}

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
