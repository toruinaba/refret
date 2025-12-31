import json
import uuid
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple

from app.core.config import get_settings

class StoreService:
    def __init__(self):
        self.settings = get_settings()
        self.data_dir = Path(self.settings.DATA_DIR)
        self.data_dir.mkdir(exist_ok=True)
        self.licks_file = self.data_dir / "licks.json"
        self.tags_file = self.data_dir / "tags.json"

    # --- Lessons ---
    def list_lessons(
        self, 
        page: int = 1, 
        limit: int = 1000, 
        tags: List[str] = None, 
        date_from: str = None, 
        date_to: str = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        
        all_lessons = []
        if not self.data_dir.exists():
            return [], 0
            
        for d in self.data_dir.iterdir():
            if d.is_dir():
                meta = self.get_lesson_metadata(d.name)
                
                # Filter by Tags (AND logic)
                if tags:
                    lesson_tags = set(meta.get("tags", []))
                    if not set(tags).issubset(lesson_tags):
                        continue
                
                # Filter by Date
                created_at = meta.get("created_at", "")
                if date_from and created_at < date_from:
                    continue
                if date_to and created_at > date_to:
                    continue

                all_lessons.append({
                    "id": d.name,
                    "title": meta.get("title", d.name),
                    "created_at": created_at,
                    "tags": meta.get("tags", []),
                    "memo": meta.get("memo", "")
                })
        
        # Sort by Date descending
        all_lessons.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        total = len(all_lessons)
        start = (page - 1) * limit
        end = start + limit
        
        return all_lessons[start:end], total

    def get_lesson_metadata(self, lesson_id: str) -> Dict[str, Any]:
        folder = self.data_dir / lesson_id
        meta_path = folder / "metadata.json"
        
        # Base metadata
        data = {"tags": [], "memo": "", "created_at": ""}
        if meta_path.exists():
            try:
                with open(meta_path, "r") as f:
                    data.update(json.load(f))
            except:
                pass
        else:
             # Try to infer creation time from folder if metadata missing
             if folder.exists():
                ctime = datetime.fromtimestamp(folder.stat().st_ctime).strftime('%Y-%m-%d')
                data["created_at"] = ctime

        # Load Transcript
        transcript_path = folder / "transcript.txt"
        if transcript_path.exists():
            with open(transcript_path, "r") as f:
                data["transcript"] = f.read()
        
        # Load Summary
        summary_path = folder / "summary.json"
        if summary_path.exists():
             try:
                 with open(summary_path, "r") as f:
                     summary_data = json.load(f)
                     data["summary"] = summary_data.get("summary", "")
                     data["key_points"] = summary_data.get("key_points", [])
                     data["chords"] = summary_data.get("chords", [])
             except:
                 pass
                 
        return data

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

    def list_licks(
        self,
        page: int = 1,
        limit: int = 50,
        tags: List[str] = None,
        date_from: str = None,
        date_to: str = None,
        lesson_id: str = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        
        all_licks = self.load_licks()
        filtered = []
        
        for lick in all_licks:
            # Filter by Lesson ID
            if lesson_id and lick.get("lesson_dir") != lesson_id:
                continue
                
            # Filter by Tags (AND logic)
            if tags:
                lick_tags = set(lick.get("tags", []))
                if not set(tags).issubset(lick_tags):
                    continue
            
            # Filter by Date
            created_at = lick.get("created_at", "")
            if date_from and created_at < date_from:
                continue
            if date_to and created_at > date_to:
                continue
                
            filtered.append(lick)
            
        total = len(filtered)
        start = (page - 1) * limit
        end = start + limit
        
        return filtered[start:end], total

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

    def get_settings_override(self) -> Dict[str, Any]:
        """Load settings from data/settings.json."""
        path = self.data_dir / "settings.json"
        if path.exists():
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except:
                 pass
        return {}

    def save_settings_override(self, settings: Dict[str, Any]):
        """Save settings to data/settings.json."""
        path = self.data_dir / "settings.json"
        with open(path, "w") as f:
            json.dump(settings, f, indent=2)
