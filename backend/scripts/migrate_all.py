
import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.services.database import DatabaseService
from app.core.config import get_settings

def migrate():
    settings = get_settings()
    data_dir = Path(settings.DATA_DIR)
    db = DatabaseService()
    db.init_db()  # Ensure tables exist

    print(f"Starting Full Migration from {data_dir}...")
    
    # --- 1. Lessons ---
    print("\n--- Migrating Lessons ---")
    count = 0
    skipped = 0
    
    for lesson_dir in data_dir.iterdir():
        if not lesson_dir.is_dir():
            continue
        lesson_id = lesson_dir.name
        metadata_path = lesson_dir / "metadata.json"
        
        metadata = {}
        if metadata_path.exists():
            try:
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
            except Exception as e:
                print(f"Error reading metadata for {lesson_id}: {e}")
                
        if not metadata and not list(lesson_dir.glob("*.mp3")):
            skipped += 1
            continue

        title = metadata.get("title", lesson_id)
        created_at = metadata.get("created_at")
        if not created_at:
            created_at = datetime.fromtimestamp(lesson_dir.stat().st_ctime).strftime('%Y-%m-%d %H:%M:%S')

        folder_rel = lesson_id 
        vocals_rel = f"{lesson_id}/vocals.mp3" if (lesson_dir / "vocals.mp3").exists() else None
        guitar_rel = f"{lesson_id}/guitar.mp3" if (lesson_dir / "guitar.mp3").exists() else None
        
        original_rel = None
        originals = list(lesson_dir.glob("original.*"))
        if originals:
             original_rel = f"{lesson_id}/{originals[0].name}"

        transcript_path_rel = f"{lesson_id}/transcript.txt" if (lesson_dir / "transcript.txt").exists() else None
        summary_path_rel = f"{lesson_id}/summary.json" if (lesson_dir / "summary.json").exists() else None

        record = {
            "id": lesson_id,
            "title": title,
            "duration": 0, 
            "date": created_at[:10] if created_at else None,
            "status": "completed",
            "folder_path": folder_rel,
            "original_path": original_rel,
            "vocals_path": vocals_rel,
            "guitar_path": guitar_rel,
            "transcript_path": transcript_path_rel,
            "summary_path": summary_path_rel,
            "tags": metadata.get("tags", []),
            "memo": metadata.get("memo", ""),
            "created_at": created_at
        }
        
        db.create_lesson(record)
        count += 1
        
        # Populate Tags from Lessons
        for t in record["tags"]:
            db.add_tag(t)

    print(f"Lessons migrated: {count}")

    # --- 2. Licks ---
    print("\n--- Migrating Licks ---")
    licks_file = data_dir / "licks.json"
    licks_count = 0
    if licks_file.exists():
        try:
            with open(licks_file, "r") as f:
                licks = json.load(f)
            for lick in licks:
                # Map old keys if necessary. Assuming structure matches implementation plan.
                # Lick structure: id, title, start, end, tags, memo, created_at, lesson_dir (-> lesson_id), abc_score
                
                # Fix legacy `lesson_dir` key to `lesson_id`
                lid = lick.get("lesson_dir")
                if not lid and "lesson_id" in lick:
                    lid = lick["lesson_id"]
                
                lick_record = {
                    "id": lick.get("id"),
                    "lesson_id": lid,
                    "title": lick.get("title"),
                    "start": lick.get("start"),
                    "end": lick.get("end"),
                    "tags": lick.get("tags", []),
                    "memo": lick.get("memo", ""),
                    "abc_score": lick.get("abc_score", ""),
                    "created_at": lick.get("created_at")
                }
                
                db.create_lick(lick_record)
                licks_count += 1
                
                # Populate Tags from Licks
                for t in lick_record["tags"]:
                    db.add_tag(t)
        except Exception as e:
            print(f"Error migrating licks: {e}")
    else:
        print("No licks.json found.")
    print(f"Licks migrated: {licks_count}")

    # --- 3. Settings ---
    print("\n--- Migrating Settings ---")
    settings_file = data_dir / "settings.json"
    settings_count = 0
    if settings_file.exists():
        try:
            with open(settings_file, "r") as f:
                settings_data = json.load(f)
            for k, v in settings_data.items():
                db.save_setting(k, v)
                settings_count += 1
        except Exception as e:
            print(f"Error migrating settings: {e}")
    else:
        print("No settings.json found.")
    print(f"Settings migrated: {settings_count}")

    # --- 4. Tags (Global File) ---
    print("\n--- Migrating Tags (tags.json) ---")
    tags_file = data_dir / "tags.json"
    tags_count = 0
    if tags_file.exists():
        try:
            with open(tags_file, "r") as f:
                tags_list = json.load(f)
            for t in tags_list:
                db.add_tag(t)
                tags_count += 1
        except Exception as e:
            print(f"Error migrating tags.json: {e}")
    print(f"Global tags migrated: {tags_count}")
    
    print("\nFull Migration Complete.")

if __name__ == "__main__":
    migrate()
