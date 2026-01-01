
import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.services.store import StoreService

def verify():
    store = StoreService()
    print("StoreService initialized.")
    
    # List
    lessons, total = store.list_lessons(limit=5)
    print(f"Total lessons in DB: {total}")
    for l in lessons:
        print(f"- {l['id']}: {l['title']}")
        
    if not lessons:
        print("No lessons found. Setup might be empty.")
        return

    # Get Metadata
    lid = lessons[0]["id"]
    print(f"\nFetching metadata for {lid}...")
    meta = store.get_lesson_metadata(lid)
    print(f"Title: {meta.get('title')}")
    print(f"Tags: {meta.get('tags')}")
    print(f"Memo: {meta.get('memo')}")
    print(f"Transcript Length: {len(meta.get('transcript', ''))}")
    print(f"Summary keys: {meta.keys()}")

    # --- Licks ---
    print("\n--- Verifying Licks ---")
    licks, l_total = store.list_licks(limit=5)
    print(f"Total licks in DB: {l_total}")
    for l in licks:
        print(f"- {l['title']} (Lesson: {l.get('lesson_id')})")
        
    if licks:
        print(f"Fetching lick {licks[0]['id']}...")
        lick = store.get_lick(licks[0]['id'])
        print(f"Lick Memo: {lick.get('memo')}")

    # --- Settings ---
    print("\n--- Verifying Settings ---")
    settings = store.get_settings_override()
    print(f"Settings keys: {list(settings.keys())}")
    
    # --- Tags ---
    print("\n--- Verifying Tags ---")
    tags = store.get_all_tags()
    print(f"Total Tags: {len(tags)}")
    print(f"Tags: {tags}")

if __name__ == "__main__":
    verify()
