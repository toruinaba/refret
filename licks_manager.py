import json
import uuid
from pathlib import Path
from datetime import datetime

LICKS_FILE = Path("data/licks.json")

def load_licks():
    """Load all licks from json file."""
    if not LICKS_FILE.exists():
        return []
    try:
        with open(LICKS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_lick(lesson_dir_name, title, tags, start_time, end_time, memo=""):
    """
    Save a new lick to the database.
    
    Args:
        lesson_dir_name (str): The folder name of the source lesson
        title (str): Title of the lick
        tags (list): List of tags
        start_time (float): Start time in seconds
        end_time (float): End time in seconds
        memo (str): Optional memo/notes
    """
    licks = load_licks()
    
    new_lick = {
        "id": str(uuid.uuid4()),
        "lesson_dir": lesson_dir_name,
        "title": title,
        "tags": tags,
        "start": float(start_time),
        "end": float(end_time),
        "memo": memo,
        "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    licks.append(new_lick)
    
    # Sort by creation date desc
    licks.sort(key=lambda x: x["created_at"], reverse=True)
    
    with open(LICKS_FILE, "w") as f:
        json.dump(licks, f, indent=4)
        
    return new_lick

def update_lick(lick_id, updates):
    """
    Update an existing lick with a dictionary of changes.
    Args:
        lick_id (str): ID of the lick to update
        updates (dict): Dictionary of keys/values to update (e.g., {"memo": "new text"})
    """
    licks = load_licks()
    updated = False
    for lick in licks:
        if lick["id"] == lick_id:
            lick.update(updates)
            updated = True
            break
            
    if updated:
        with open(LICKS_FILE, "w") as f:
            json.dump(licks, f, indent=4)
    return updated

def delete_lick(lick_id):
    """Delete a lick by ID."""
    licks = load_licks()
    licks = [lick for lick in licks if lick["id"] != lick_id]
    
    with open(LICKS_FILE, "w") as f:
        json.dump(licks, f, indent=4)
