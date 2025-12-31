from fastapi import APIRouter, Depends
from typing import Optional
from app.services.store import StoreService
from app.core.config import get_settings
from app.schemas.settings import SettingsUpdate

router = APIRouter(tags=["settings"])

def get_store():
    return StoreService()

@router.get("")
async def get_current_settings(store: StoreService = Depends(get_store)):
    """Get current effective settings (defaults + override)."""
    defaults = get_settings()
    overrides = store.get_settings_override()
    
    # Mask API Key partially if exists
    api_key = overrides.get("openai_api_key") or defaults.OPENAI_API_KEY
    masked_key = None
    if api_key and len(api_key) > 8:
        masked_key = f"{api_key[:3]}...{api_key[-4:]}"
    elif api_key:
        masked_key = "***"

    return {
        "llm_provider": overrides.get("llm_provider", defaults.LLM_PROVIDER),
        "llm_model": overrides.get("llm_model", defaults.LLM_MODEL),
        "system_prompt": overrides.get("system_prompt", defaults.SYSTEM_PROMPT),
        "openai_api_key_masked": masked_key,
        "openai_api_key_is_set": bool(api_key)
    }

@router.post("")
async def update_settings(update: SettingsUpdate, store: StoreService = Depends(get_store)):
    """Update settings (saves to settings.json)."""
    current = store.get_settings_override()
    
    updates_dict = update.model_dump(exclude_unset=True)
    
    # If API key is empty string, maybe clear it? For now assume valid input.
    # If masked key was sent back (e.g. ***), ignore it.
    if updates_dict.get("openai_api_key") and "***" in updates_dict["openai_api_key"]:
        del updates_dict["openai_api_key"]
        
    current.update(updates_dict)
    store.save_settings_override(current)
    
    return {"message": "Settings saved successfully", "settings": current}
