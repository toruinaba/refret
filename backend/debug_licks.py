import json
import os
from pathlib import Path

DATA_DIR = Path("../data")
LICKS_FILE = DATA_DIR / "licks.json"

if not LICKS_FILE.exists():
    print("No licks.json found")
    exit()

with open(LICKS_FILE) as f:
    licks = json.load(f)

print(f"Found {len(licks)} licks.")
for i, lick in enumerate(licks[:5]):
    print(f"Lick {i}: Keys={list(lick.keys())}")
    lesson_dir = lick.get('lesson_dir')
    lesson_id = lick.get('lesson_id')
    print(f"  lesson_dir: {lesson_dir}")
    print(f"  lesson_id: {lesson_id}")
    
    if lesson_dir:
        path = DATA_DIR / lesson_dir
        print(f"  Lesson Folder Exists: {path.exists()}")
    else:
        print("  WARNING: No lesson_dir")
