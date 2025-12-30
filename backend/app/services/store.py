import json
import uuid
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from backend.app.core.config import get_settings

class StoreService:
    def __init__(self):
        self.settings = get_settings()
        self.data_dir = Path(self.settings.DATA_DIR)
        self.data_dir.mkdir(exist_ok=True)
        self.licks_file = self.data_dir / "licks.json"
        self.tags_file = self.data_dir / "tags.json"

    # --- Lessons ---
    def list_lessons(self) -> List[Dict[str, Any]]:
        lessons = []
        if not self.data_dir.exists():
            return []
            
        for d in self.data_dir.iterdir():
            if d.is_dir():
                meta = self.get_lesson_metadata(d.name)
                lessons.append({
                    "id": d.name,
                    "title": d.name, # Currently folder name is ID and title
                    "created_at": meta.get("created_at"),
                    "tags": meta.get("tags", []),
                    "memo": meta.get("memo", "")
                })
        
        # Sort by Date descending
        lessons.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return lessons

    def get_lesson_metadata(self, lesson_id: str) -> Dict[str, Any]:
        path = self.data_dir / lesson_id / "metadata.json"
        if path.exists():
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except:
                pass
        
        # Default
        # Try to infer creation time from folder
        folder = self.data_dir / lesson_id
        ctime = ""
        if folder.exists():
            ctime = datetime.fromtimestamp(folder.stat().st_ctime).strftime('%Y-%m-%d')
            
        return {"tags": [], "memo": "", "created_at": ctime}

    def save_lesson_metadata(self, lesson_id: str, metadata: Dict[str, Any]):
        folder = self.data_dir / lesson_id
        folder.mkdir(parents=True, exist_ok=True)
        
        with open(folder / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=4)
            
        # Update global tags
        if "tags" in metadata:
            self.add_global_tags(metadata["tags"])

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
        path = self.data_dir / lesson_id
        if path.exists():
            shutil.rmtree(path)

    # --- Licks ---
    def load_licks(self) -> List[Dict[str, Any]]:
        if not self.licks_file.exists():
            return []
        try:
            with open(self.licks_file, "r") as f:
                return json.load(f)
        except:
            return []

    def save_lick(self, lick_data: Dict[str, Any]):
        licks = self.load_licks()
        
        # Ensure ID and timestamps
        if "id" not in lick_data:
            lick_data["id"] = str(uuid.uuid4())
        if "created_at" not in lick_data:
            lick_data["created_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
        licks.append(lick_data)
        licks.sort(key=lambda x: x["created_at"], reverse=True)
        
        with open(self.licks_file, "w") as f:
            json.dump(licks, f, indent=4)
            
        return lick_data
        
    def update_lick(self, lick_id: str, updates: Dict[str, Any]):
        licks = self.load_licks()
        updated = False
        for lick in licks:
            if lick["id"] == lick_id:
                lick.update(updates)
                updated = True
                break
        
        if updated:
            with open(self.licks_file, "w") as f:
                json.dump(licks, f, indent=4)
        return updated

    def delete_lick(self, lick_id: str):
        licks = self.load_licks()
        licks = [l for l in licks if l["id"] != lick_id]
        with open(self.licks_file, "w") as f:
            json.dump(licks, f, indent=4)

    # --- Tags ---
    def load_global_tags(self):
        if self.tags_file.exists():
            try:
                with open(self.tags_file, "r") as f:
                    return set(json.load(f))
            except:
                pass
        return set()

    def add_global_tags(self, tags: List[str]):
        current = self.load_global_tags()
        current.update(tags)
        with open(self.tags_file, "w") as f:
            json.dump(list(current), f, indent=4)
            
    def get_all_tags(self) -> List[str]:
        # Combine global tags + tags found in lessons
        tags = self.load_global_tags()
        for lesson in self.list_lessons():
            for t in lesson.get("tags", []):
                tags.add(t)
        return sorted(list(tags))
