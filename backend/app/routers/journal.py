from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional, Any
from app.services.database import DatabaseService

router = APIRouter()

def get_db():
    return DatabaseService()

# --- Models ---
class LogBase(BaseModel):
    date: str
    duration_minutes: int = 0
    notes: Optional[str] = ""
    tags: List[str] = []
    sentiment: Optional[str] = ""

class LogCreate(LogBase):
    pass

class LogUpdate(LogBase):
    pass

class LogResponse(LogBase):
    id: int
    audio_path: Optional[str] = None
    created_at: str
    analysis: Optional[dict] = None

class StatsResponse(BaseModel):
    heatmap: List[Any]
    total_minutes: int
    week_minutes: int

# --- Endpoints ---

@router.get("/", response_model=List[LogResponse])
async def get_logs(start: Optional[str] = None, end: Optional[str] = None, db: DatabaseService = Depends(get_db)):
    """Get list of logs, optionally filtered by date range."""
    return db.get_logs(start, end)

@router.post("/", response_model=LogResponse)
async def create_log(log: LogCreate, db: DatabaseService = Depends(get_db)):
    """Create a new practice log."""
    log_id = db.create_log(log.model_dump())
    new_log = db.get_log(log_id)
    if not new_log:
        raise HTTPException(status_code=500, detail="Failed to create log")
    return new_log

@router.get("/stats", response_model=StatsResponse)
async def get_stats(db: DatabaseService = Depends(get_db)):
    """Get statistics for dashboard."""
    return db.get_stats()

@router.get("/{id}", response_model=LogResponse)
async def get_log(id: int, db: DatabaseService = Depends(get_db)):
    """Get a single log with analysis data."""
    log = db.get_log(id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
        
    # Inject Analysis if available
    if log.get("audio_path"):
        from app.core.config import get_settings
        from pathlib import Path
        import json
        
        data_dir = Path(get_settings().DATA_DIR)
        # audio_path is "practice/{file_id}.mp3"
        # Analysis is "practice/{file_id}_analysis.json"
        
        try:
            audio_p = Path(log["audio_path"])
            stem = audio_p.stem # file_id
            analysis_path = data_dir / "practice" / f"{stem}_analysis.json"
            
            if analysis_path.exists():
                with open(analysis_path, "r") as f:
                   log["analysis"] = json.load(f)
        except Exception as e:
            print(f"Failed to load analysis for log {id}: {e}")
            
    return log

@router.put("/{id}", response_model=LogResponse)
async def update_log(id: int, log: LogUpdate, db: DatabaseService = Depends(get_db)):
    """Update a log."""
    success = db.update_log(id, log.model_dump())
    if not success:
        raise HTTPException(status_code=404, detail="Log not found")
    return db.get_log(id)

@router.delete("/{id}")
async def delete_log(id: int, db: DatabaseService = Depends(get_db)):
    """Delete a log."""
    success = db.delete_log(id)
    if not success:
        raise HTTPException(status_code=404, detail="Log not found")
    return {"status": "deleted", "id": id}

@router.get("/{id}/audio")
async def get_practice_audio(id: int, db: DatabaseService = Depends(get_db)):
    """Stream practice log audio."""
    from fastapi.responses import FileResponse
    from pathlib import Path

    log = db.get_log(id)
    if not log or not log.get("audio_path"):
        raise HTTPException(status_code=404, detail="Audio not found")
        
    store_dir = db.get_connection().execute("SELECT value FROM settings WHERE key='DATA_DIR'").fetchone() 
    # Wait, DatabaseService doesn't expose data_dir easily?
    # Actually DatabaseService in line 14 initializes self.db_path from settings.DATA_DIR.
    # The `audio_path` saved in DB is relative: `practice/{file_id}.mp3`.
    # I need absolute path.
    # I can use `app.core.config.get_settings().DATA_DIR`.
    
    from app.core.config import get_settings
    data_dir = Path(get_settings().DATA_DIR)
    
    file_path = data_dir / log["audio_path"]
    
    if not file_path.exists():
         raise HTTPException(status_code=404, detail="Audio file missing")
         
    return FileResponse(
        path=file_path,
        media_type="audio/mpeg",
        filename=f"practice_{id}.mp3"
    )

@router.post("/upload", response_model=LogResponse)
async def upload_practice_log(
    file: UploadFile = File(...),
    date: str = Form(...),
    notes: str = Form(None),
    duration_minutes: int = Form(0),
    sentiment: str = Form(None),
    tags: str = Form(None), # JSON string or comma list
    db: DatabaseService = Depends(get_db)
):
    """Upload audio for a practice log."""
    from app.services.audio import AudioProcessor
    from app.services.store import StoreService
    import shutil
    import json
    from pathlib import Path
    import uuid
    from datetime import datetime

    store = StoreService()
    # Path strategy: data/practice/{date}_{uuid}
    # Create practice folder if not exists? Current logs are just DB entries.
    # Let's create a dedicated folder for practice audio: data/practice
    practice_dir = store.data_dir / "practice"
    practice_dir.mkdir(exist_ok=True)
    
    file_id = f"{date}_{uuid.uuid4().hex[:8]}"
    
    # Save Raw
    ext = Path(file.filename).suffix
    if not ext: ext = ".m4a"
    raw_path = practice_dir / f"{file_id}_raw{ext}"
    
    with open(raw_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Convert to MP3
    final_path = practice_dir / f"{file_id}.mp3"
    try:
        processor = AudioProcessor()
        processor.convert_to_mp3(raw_path, final_path)
    except Exception as e:
        if raw_path.exists(): raw_path.unlink()
        raise HTTPException(status_code=500, detail=f"Audio normalization failed: {str(e)}")
        
    if raw_path.exists():
        raw_path.unlink()
        
    # Relative path for DB
    audio_path = f"practice/{file_id}.mp3"
    
    # Parse Tags
    parsed_tags = []
    if tags:
        try:
            parsed_tags = json.loads(tags)
        except:
            parsed_tags = [t.strip() for t in tags.split(",") if t.strip()]

    # Create Log
    log_data = {
        "date": date,
        "duration_minutes": duration_minutes,
        "notes": notes,
        "tags": parsed_tags,
        "sentiment": sentiment,
        "_audio_path": audio_path 
    }
    
    log_id = db.create_log({**log_data, "audio_path": audio_path})

    # Run Analysis (Inline for now - could be background task)
    try:
        analysis = processor.analyze_audio(final_path)
        with open(practice_dir / f"{file_id}_analysis.json", "w") as f:
            json.dump(analysis, f)
    except Exception as e:
        print(f"Analysis failed during upload: {e}")

    return db.get_log(log_id)
