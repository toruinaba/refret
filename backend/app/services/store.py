import json
import uuid
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple

from app.core.config import get_settings
from app.services.database import DatabaseService

class StoreService:
    def __init__(self):
        self.settings = get_settings()
        self.data_dir = Path(self.settings.DATA_DIR)
        self.data_dir.mkdir(exist_ok=True)
        self.licks_file = self.data_dir / "licks.json"
        self.tags_file = self.data_dir / "tags.json"
        self.db = DatabaseService()

    # --- Lessons ---
    def list_lessons(
        self, 
        page: int = 1, 
        limit: int = 1000, 
        tags: List[str] = None, 
        date_from: str = None, 
        date_to: str = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        
        # Use DB
        return self.db.list_lessons(page, limit, tags, date_from, date_to)

    def get_lesson_metadata(self, lesson_id: str) -> Dict[str, Any]:
        # Get from DB first
        db_meta = self.db.get_lesson(lesson_id)
        if not db_meta:
            return {}
            
        folder = self.data_dir / lesson_id
        
        # Load Content Files if path is present, or fallback to default locations
        transcript = ""
        summary_data = {}
        
        # Transcript
        transcript_path = folder / "transcript.txt"
        if transcript_path.exists():
            try:
                with open(transcript_path, "r") as f:
                    transcript = f.read()
            except:
                pass
                
        # Summary
        summary_path = folder / "summary.json"
        if summary_path.exists():
             try:
                 with open(summary_path, "r") as f:
                     summary_data = json.load(f)
             except:
                 pass

        # Merge
        result = db_meta.copy()
        result["transcript"] = transcript
        if summary_data:
             result["summary"] = summary_data.get("summary", "")
             result["key_points"] = summary_data.get("key_points", [])
             result["chords"] = summary_data.get("chords", [])
             
        return result

    def save_lesson_metadata(self, lesson_id: str, metadata: Dict[str, Any]):
        # Update DB. If not exists, create? 
        # Usually save_lesson_metadata called after create or update.
        # Check if exists
        existing = self.db.get_lesson(lesson_id)
        if existing:
            self.db.update_lesson(lesson_id, metadata)
        else:
            # Creation scenario
            record = metadata.copy()
            record["id"] = lesson_id
            if "folder_path" not in record:
                record["folder_path"] = lesson_id # Relative
            
            # Ensure paths if generic
            if not record.get("vocals_path") and (self.data_dir / lesson_id / "vocals.mp3").exists():
                 record["vocals_path"] = f"{lesson_id}/vocals.mp3"
            
            self.db.create_lesson(record)
            
        # Update global tags
        if "tags" in metadata:
            for t in metadata["tags"]:
                self.db.add_tag(t)

    def create_lesson_folder(self, title: str) -> Path:
        # Sanitize title for folder name
        safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_')]).strip().replace(' ', '_')
        if not safe_title:
            safe_title = f"lesson_{uuid.uuid4().hex[:8]}"
            
        path = self.data_dir / safe_title
        if path.exists():
            # Append timestamp if exists
            path = self.data_dir / f"{safe_title}_{int(datetime.now().timestamp())}"
        
        path.mkdir(parents=True, exist_ok=True)
        return path

    def delete_lesson(self, lesson_id: str):
        # Delete from DB
        self.db.delete_lesson(lesson_id)
        
        # Delete files
        path = self.data_dir / lesson_id
        if path.exists():
            shutil.rmtree(path)

    # --- Licks ---
    # --- Licks ---
    def list_licks(
        self,
        page: int = 1,
        limit: int = 50,
        tags: List[str] = None,
        date_from: str = None,
        date_to: str = None,
        lesson_id: str = None,
        practice_log_id: int = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        return self.db.list_licks(page, limit, tags, lesson_id, practice_log_id, date_from, date_to)

    def save_lick(self, lick_data: Dict[str, Any]):
        # Ensure ID and timestamps
        if "id" not in lick_data:
            lick_data["id"] = str(uuid.uuid4())
        if "created_at" not in lick_data:
            lick_data["created_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
        self.db.create_lick(lick_data)
        
        # Update tags
        for t in lick_data.get("tags", []):
            self.db.add_tag(t)
            
        return lick_data
        
    def update_lick(self, lick_id: str, updates: Dict[str, Any]):
        self.db.update_lick(lick_id, updates)
        # return updated lick? 
        return self.db.get_lick(lick_id)

    def delete_lick(self, lick_id: str):
        self.db.delete_lick(lick_id)

    def get_lick(self, lick_id: str):
        return self.db.get_lick(lick_id)

    # --- Tags ---
    def get_all_tags(self) -> List[str]:
        return self.db.get_tags()

    # --- Settings ---
    def get_settings_override(self) -> Dict[str, Any]:
        """Load settings from DB."""
        return self.db.get_all_settings()

    def save_settings_override(self, settings: Dict[str, Any]):
        """Save settings to DB."""
        for k, v in settings.items():
            self.db.save_setting(k, v)
