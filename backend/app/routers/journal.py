from fastapi import APIRouter, HTTPException, Depends
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
