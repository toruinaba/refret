from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from backend.app.services.store import StoreService

router = APIRouter()

def get_store():
    return StoreService()

# --- Pydantic Models for Validation ---
class LickCreate(BaseModel):
    lesson_dir: str # Maps to lesson directory name (ID)
    title: str
    tags: List[str] = []
    start: float
    end: float
    memo: str = ""

class LickUpdate(BaseModel):
    title: Optional[str] = None
    tags: Optional[List[str]] = None
    memo: Optional[str] = None
    start: Optional[float] = None
    end: Optional[float] = None

@router.get("/", response_model=List[Dict[str, Any]])
async def list_licks(store: StoreService = Depends(get_store)):
    """List all saved licks."""
    return store.load_licks()

@router.post("/", response_model=Dict[str, Any])
async def create_lick(lick: LickCreate, store: StoreService = Depends(get_store)):
    """Create a new lick."""
    # Convert Pydantic model to dict
    data = lick.model_dump()
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
    if not success:
        raise HTTPException(status_code=404, detail="Lick not found")
        
    # In a real DB we'd fetch the updated obj, here we just return success or load all
    # Let's find and return the updated lick
    licks = store.load_licks()
    for l in licks:
        if l["id"] == lick_id:
            return l
    
    raise HTTPException(status_code=404, detail="Lick not found after update")

@router.delete("/{lick_id}")
async def delete_lick(lick_id: str, store: StoreService = Depends(get_store)):
    """Delete a lick."""
    store.delete_lick(lick_id)
    return {"status": "deleted", "id": lick_id}

@router.get("/{lick_id}", response_model=Dict[str, Any])
async def get_lick(lick_id: str, store: StoreService = Depends(get_store)):
    """Get a specific lick."""
    licks = store.load_licks()
    for l in licks:
        if l["id"] == lick_id:
            return l
    raise HTTPException(status_code=404, detail="Lick not found")

