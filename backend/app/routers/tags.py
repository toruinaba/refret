from fastapi import APIRouter, Depends
from typing import List

from app.services.store import StoreService

router = APIRouter()

def get_store():
    return StoreService()

@router.get("/", response_model=List[str])
async def get_all_tags(store: StoreService = Depends(get_store)):
    """Get all unique tags used across lessons and global tags."""
    return store.get_all_tags()
