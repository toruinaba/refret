
import sys
import os
import json
from pathlib import Path

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.services.database import DatabaseService
from app.core.config import get_settings

def migrate():
    settings = get_settings()
    data_dir = Path(settings.DATA_DIR)
    db = DatabaseService()
    db.init_db()  # Ensure tables exist

    print(f"Scanning {data_dir}...")
    
    count = 0
    skipped = 0
    
    for lesson_dir in data_dir.iterdir():
        if not lesson_dir.is_dir():
            continue
            
        lesson_id = lesson_dir.name
        
        # Check if it's likely a lesson folder (has metadata or audio)
        metadata_path = lesson_dir / "metadata.json"
        
        # Load Metadata
        metadata = {}
        if metadata_path.exists():
            try:
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
            except Exception as e:
                print(f"Error reading metadata for {lesson_id}: {e}")
                
        # If no metadata and no audio, probably not a lesson (e.g. 'practice.db' dir if any, or 'licks.json')
        if not metadata and not list(lesson_dir.glob("*.mp3")) and not list(lesson_dir.glob("*.wav")):
            print(f"Skipping non-lesson folder: {lesson_id}")
            skipped += 1
            continue

        # Prepare DB Record
        title = metadata.get("title", lesson_id)
        created_at = metadata.get("created_at")
        
        # If created_at missing, try to infer from folder name (YYYYMMDD_HHMMSS) or stat
        if not created_at:
            if "_" in lesson_id and len(lesson_id) >= 15: # heuristic
                try:
                    # Try 20240101_120000 format
                     # Not strictly parsing, just assuming it's sortable string
                     pass
                except:
                    pass
            # Fallback to file mtime
            created_at = datetime.fromtimestamp(lesson_dir.stat().st_ctime).strftime('%Y-%m-%d %H:%M:%S')

        # Paths (Relative to data_dir is safer for portability, but absolute is easier for FileResponse)
        # However, database usually stores relative or consistent ID. 
        # API constructs path from ID usually. 
        # But our DB schema has `folder_path`, `vocals_path` etc.
        # Let's store relative path to data_dir.
        
        folder_rel = lesson_id 
        vocals_rel = f"{lesson_id}/vocals.mp3" if (lesson_dir / "vocals.mp3").exists() else None
        guitar_rel = f"{lesson_id}/guitar.mp3" if (lesson_dir / "guitar.mp3").exists() else None
        original_rel = None
        # Find original
        originals = list(lesson_dir.glob("original.*"))
        if originals:
             original_rel = f"{lesson_id}/{originals[0].name}"

        # Transcript
        transcript_path_rel = f"{lesson_id}/transcript.txt" if (lesson_dir / "transcript.txt").exists() else None
        
        # Summary
        summary_path_rel = f"{lesson_id}/summary.json" if (lesson_dir / "summary.json").exists() else None

        record = {
            "id": lesson_id,
            "title": title,
            "duration": 0, # We don't have duration metadata usually?
            "date": created_at[:10] if created_at else None,
            "status": "completed", # Assume migrated ones are done
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
        
        print(f"Migrating {lesson_id} - {title}")
        db.create_lesson(record)
        count += 1

    print(f"Migration complete. Migrated {count} lessons. Skipped {skipped}.")

if __name__ == "__main__":
    from datetime import datetime
    migrate()
