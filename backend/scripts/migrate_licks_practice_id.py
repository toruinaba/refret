import sqlite3
import os
from pathlib import Path

# Adjust path to your data directory
DATA_DIR = os.getenv("DATA_DIR", "/app/data")
DB_PATH = Path(DATA_DIR) / "practice.db"

def migrate():
    print(f"Migrating database at {DB_PATH}")
    if not DB_PATH.exists():
        print("Database not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        # Check if column exists
        cursor = conn.execute("PRAGMA table_info(licks)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "practice_log_id" in columns:
            print("Column 'practice_log_id' already exists in 'licks'.")
        else:
            print("Adding 'practice_log_id' column to 'licks'...")
            conn.execute("ALTER TABLE licks ADD COLUMN practice_log_id INTEGER")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_licks_practice ON licks (practice_log_id)")
            conn.commit()
            print("Migration successful.")
            
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
