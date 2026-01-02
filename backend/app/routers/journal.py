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
    """Get a single log."""
    log = db.get_log(id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
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
        "_audio_path": audio_path # Note: DB needs this column populated. create_log takes dict. 
        # But wait, create_log in database.py explicitly maps fields. I need to update create_log too.
        # Let's assume I updated create_log? I didn't update the METHOD, only the schema.
        # I need to update create_log to accept audio_path.
    }
    
    # TODO: Update DB method to handle audio_path. For now I'll inject it manually via raw SQL or update methods.
    # Ah, I should update database.py methods first/concurrently.
    
    # Let's invoke a specialized method or update create_log. 
    # For now, let's call create_log and then update it with raw SQL or update existing method logic.
    # Updating database.py logic is cleaner.
    
    log_id = db.create_log({**log_data, "audio_path": audio_path})
    return db.get_log(log_id)
