
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

if __name__ == "__main__":
    verify()
