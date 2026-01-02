from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import math

from app.services.store import StoreService

router = APIRouter()

def get_store():
    return StoreService()

# --- Pydantic Models for Validation ---
class LickCreate(BaseModel):
    lesson_id: Optional[str] = None # Was lesson_dir
    practice_log_id: Optional[int] = None
    title: str
    tags: List[str] = []
    start: float
    end: float
    memo: str = ""
    abc_score: str = ""
    
    # Backward compatibility for frontend still sending lesson_dir
    lesson_dir: Optional[str] = None 

class LickUpdate(BaseModel):
    title: Optional[str] = None
    tags: Optional[List[str]] = None
    memo: Optional[str] = None
    start: Optional[float] = None
    end: Optional[float] = None
    abc_score: Optional[str] = None

@router.get("/", response_model=Dict[str, Any])
async def list_licks(
    page: int = 1,
    limit: int = 50,
    tags: str = None,
    lesson_id: str = None,
    practice_log_id: int = None,
    date_from: str = None,
    date_to: str = None,
    store: StoreService = Depends(get_store)
):
    """List licks with filtering and pagination."""
    tag_list = None
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    items, total = store.list_licks(
        page=page,
        limit=limit,
        tags=tag_list,
        date_from=date_from,
        date_to=date_to,
        lesson_id=lesson_id,
        practice_log_id=practice_log_id
    )

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": math.ceil(total / limit) if limit > 0 else 1
    }

@router.post("/", response_model=Dict[str, Any])
async def create_lick(lick: LickCreate, store: StoreService = Depends(get_store)):
    """Create a new lick."""
    # Convert Pydantic model to dict
    data = lick.model_dump()
    
    # Handle legacy lesson_dir -> lesson_id mapping if lesson_id missing
    if data.get("lesson_dir") and not data.get("lesson_id"):
        data["lesson_id"] = data.pop("lesson_dir")
    else:
        # Just remove legacy field if it exists
        data.pop("lesson_dir", None)
        
    # Validation: Must have either lesson_id or practice_log_id
    if not data.get("lesson_id") and not data.get("practice_log_id"):
        raise HTTPException(status_code=400, detail="Must provide either lesson_id or practice_log_id")
        
    # Save (store service handles ID generation)
    saved = store.save_lick(data)
    return saved

@router.put("/{lick_id}", response_model=Dict[str, Any])
async def update_lick(lick_id: str, updates: LickUpdate, store: StoreService = Depends(get_store)):
    """Update an existing lick."""
    # Filter out None values
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    
    if not update_data:
         raise HTTPException(status_code=400, detail="No updates provided")

    success = store.update_lick(lick_id, update_data)
    # Store.update_lick returns the updated object or None (if I changed logic)
    # Actually current StoreService.update_lick returns the object.
    
    if not success:
        raise HTTPException(status_code=404, detail="Lick not found or update failed")
        
    return success

@router.delete("/{lick_id}")
async def delete_lick(lick_id: str, store: StoreService = Depends(get_store)):
    """Delete a lick."""
    store.delete_lick(lick_id)
    return {"status": "deleted", "id": lick_id}

@router.get("/{lick_id}", response_model=Dict[str, Any])
async def get_lick(lick_id: str, store: StoreService = Depends(get_store)):
    """Get a specific lick."""
    lick = store.get_lick(lick_id)
    if not lick:
        raise HTTPException(status_code=404, detail="Lick not found")
    return lick

