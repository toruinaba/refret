
import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple

from app.core.config import get_settings

class DatabaseService:
    def __init__(self):
        settings = get_settings()
        self.db_path = Path(settings.DATA_DIR) / "practice.db"
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            # Practice Logs
            conn.execute("""
                CREATE TABLE IF NOT EXISTS practice_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    duration_minutes INTEGER DEFAULT 0,
                    notes TEXT,
                    tags TEXT,
                    sentiment TEXT,
                    audio_path TEXT,
                    created_at TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_date ON practice_logs (date)")

            # Lessons Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS lessons (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    duration INTEGER DEFAULT 0,
                    date TEXT,
                    status TEXT DEFAULT 'completed',
                    folder_path TEXT,
                    original_path TEXT,
                    vocals_path TEXT,
                    guitar_path TEXT,
                    transcript_path TEXT,
                    summary_path TEXT,
                    tags TEXT,
                    memo TEXT,
                    created_at TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_lessons_date ON lessons (date)")

            # Licks Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS licks (
                    id TEXT PRIMARY KEY,
                    lesson_id TEXT,
                    title TEXT,
                    start REAL,
                    end REAL,
                    tags TEXT,
                    memo TEXT,
                    abc_score TEXT,
                    created_at TEXT,
                    FOREIGN KEY(lesson_id) REFERENCES lessons(id)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_licks_lesson ON licks (lesson_id)")

            # Settings Table (Key-Value)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            # Tags Table (for global tag management)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tags (
                    name TEXT PRIMARY KEY,
                    count INTEGER DEFAULT 0
                )
            """)

            conn.commit()

    # --- Practice Logs ---
    def get_logs(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM practice_logs"
        params = []
        
        if start_date and end_date:
            query += " WHERE date BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        elif start_date:
            query += " WHERE date >= ?"
            params.append(start_date)
        
        query += " ORDER BY date DESC, created_at DESC"
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
        results = []
        for row in rows:
            d = dict(row)
            if d.get("tags"):
                try:
                    d["tags"] = json.loads(d["tags"])
                except:
                    d["tags"] = []
            else:
                d["tags"] = []
            results.append(d)
        return results

    def get_log(self, log_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM practice_logs WHERE id = ?", (log_id,))
            row = cursor.fetchone()
            if not row:
                return None
            d = dict(row)
            if d.get("tags"):
                try:
                    d["tags"] = json.loads(d["tags"])
                except:
                    d["tags"] = []
            else:
                d["tags"] = []
            return d

    def create_log(self, data: Dict[str, Any]) -> int:
        tags_json = json.dumps(data.get("tags", []))
        created_at = datetime.now().isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO practice_logs (date, duration_minutes, notes, tags, sentiment, audio_path, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get("date"),
                data.get("duration_minutes", 0),
                data.get("notes", ""),
                tags_json,
                data.get("sentiment", ""),
                data.get("audio_path", ""),
                created_at
            ))
            conn.commit()
            return cursor.lastrowid

    def update_log(self, log_id: int, data: Dict[str, Any]) -> bool:
        fields = []
        params = []
        
        if "date" in data:
            fields.append("date = ?")
            params.append(data["date"])
        if "duration_minutes" in data:
            fields.append("duration_minutes = ?")
            params.append(data["duration_minutes"])
        if "notes" in data:
            fields.append("notes = ?")
            params.append(data["notes"])
        if "tags" in data:
            fields.append("tags = ?")
            params.append(json.dumps(data["tags"]))
        if "sentiment" in data:
            fields.append("sentiment = ?")
            params.append(data["sentiment"])
            
        if not fields:
            return False
            
        params.append(log_id)
        query = f"UPDATE practice_logs SET {', '.join(fields)} WHERE id = ?"
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0

    def delete_log(self, log_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.execute("DELETE FROM practice_logs WHERE id = ?", (log_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_stats(self) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT date, COUNT(*) as count, SUM(duration_minutes) as duration
                FROM practice_logs
                GROUP BY date
                ORDER BY date ASC
            """)
            heatmap_rows = cursor.fetchall()
            
            cursor = conn.execute("SELECT SUM(duration_minutes) FROM practice_logs")
            total_duration = cursor.fetchone()[0] or 0
            
            cursor = conn.execute("""
                SELECT SUM(duration_minutes) 
                FROM practice_logs 
                WHERE date >= date('now', 'weekday 0', '-7 days')
            """)
            week_duration = cursor.fetchone()[0] or 0

        heatmap = [dict(r) for r in heatmap_rows]
        return {
            "heatmap": heatmap,
            "total_minutes": total_duration,
            "week_minutes": week_duration
        }

    # --- Lessons ---
    def create_lesson(self, data: Dict[str, Any]):
        tags_json = json.dumps(data.get("tags", []))
        
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO lessons (
                    id, title, duration, date, status, folder_path,
                    original_path, vocals_path, guitar_path, transcript_path, summary_path,
                    tags, memo, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["id"],
                data.get("title"),
                data.get("duration", 0),
                data.get("date"),
                data.get("status", "completed"),
                data.get("folder_path"),
                data.get("original_path"),
                data.get("vocals_path"),
                data.get("guitar_path"),
                data.get("transcript_path"),
                data.get("summary_path"),
                tags_json,
                data.get("memo", ""),
                data.get("created_at")
            ))
            conn.commit()

    def get_lesson(self, lesson_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,))
            row = cursor.fetchone()
            if not row:
                return None
            d = dict(row)
            d["tags"] = json.loads(d["tags"]) if d["tags"] else []
            return d

    def list_lessons(
        self, 
        page: int = 1, 
        limit: int = 50, 
        tags: List[str] = None, 
        date_from: str = None, 
        date_to: str = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        
        query = "SELECT * FROM lessons"
        params = []
        conditions = []
        
        if tags:
            for tag in tags:
                conditions.append(f"tags LIKE ?")
                params.append(f'%"{tag}"%')

        if date_from:
            conditions.append("created_at >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("created_at <= ?")
            params.append(date_to)
            
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        query += " ORDER BY created_at DESC"
        
        with self.get_connection() as conn:
            cursor = conn.execute(f"SELECT COUNT(*) FROM ({query})", params)
            total = cursor.fetchone()[0]
            
            # Paging
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, (page - 1) * limit])
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
        results = []
        for row in rows:
            d = dict(row)
            d["tags"] = json.loads(d["tags"]) if d["tags"] else []
            results.append(d)
        return results, total

    def update_lesson(self, lesson_id: str, data: Dict[str, Any]):
        fields = []
        params = []
        
        for k in ["title", "duration", "date", "status", "memo", "created_at", "folder_path", "vocals_path", "guitar_path", "transcript_path", "summary_path", "original_path"]:
            if k in data:
                fields.append(f"{k} = ?")
                params.append(data[k])
                
        if "tags" in data:
            fields.append("tags = ?")
            params.append(json.dumps(data["tags"]))
            
        if not fields:
            return
            
        params.append(lesson_id)
        query = f"UPDATE lessons SET {', '.join(fields)} WHERE id = ?"
        
        with self.get_connection() as conn:
            conn.execute(query, params)
            conn.commit()

    def delete_lesson(self, lesson_id: str):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM lessons WHERE id = ?", (lesson_id,))
            conn.commit()

    # --- Licks ---
    def create_lick(self, data: Dict[str, Any]):
        tags_json = json.dumps(data.get("tags", []))
        
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO licks (
                    id, lesson_id, title, start, end, tags, memo, abc_score, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["id"],
                data.get("lesson_id"),
                data.get("title"),
                data.get("start", 0.0),
                data.get("end", 0.0),
                tags_json,
                data.get("memo", ""),
                data.get("abc_score", ""),
                data.get("created_at")
            ))
            conn.commit()
            
    def get_lick(self, lick_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM licks WHERE id = ?", (lick_id,))
            row = cursor.fetchone()
            if not row:
                return None
            d = dict(row)
            d["tags"] = json.loads(d["tags"]) if d["tags"] else []
            return d

    def list_licks(
        self, 
        page: int = 1, 
        limit: int = 50, 
        tags: List[str] = None, 
        lesson_id: str = None,
        date_from: str = None, 
        date_to: str = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        
        query = "SELECT * FROM licks"
        params = []
        conditions = []
        
        if lesson_id:
            conditions.append("lesson_id = ?")
            params.append(lesson_id)
            
        if tags:
            for tag in tags:
                conditions.append(f"tags LIKE ?")
                params.append(f'%"{tag}"%')

        if date_from:
            conditions.append("created_at >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("created_at <= ?")
            params.append(date_to)
            
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        query += " ORDER BY created_at DESC"
        
        with self.get_connection() as conn:
            cursor = conn.execute(f"SELECT COUNT(*) FROM ({query})", params)
            total = cursor.fetchone()[0]
            
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, (page - 1) * limit])
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
        results = []
        for row in rows:
            d = dict(row)
            d["tags"] = json.loads(d["tags"]) if d["tags"] else []
            results.append(d)
        return results, total

    def update_lick(self, lick_id: str, data: Dict[str, Any]):
        fields = []
        params = []
        
        for k in ["title", "start", "end", "memo", "abc_score", "created_at", "lesson_id"]:
            if k in data:
                fields.append(f"{k} = ?")
                params.append(data[k])
                
        if "tags" in data:
            fields.append("tags = ?")
            params.append(json.dumps(data["tags"]))
            
        if not fields:
            return
            
        params.append(lick_id)
        query = f"UPDATE licks SET {', '.join(fields)} WHERE id = ?"
        
        with self.get_connection() as conn:
            conn.execute(query, params)
            conn.commit()

    def delete_lick(self, lick_id: str):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM licks WHERE id = ?", (lick_id,))
            conn.commit()

    # --- Settings ---
    def get_setting(self, key: str) -> Any:
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                try:
                    return json.loads(row[0])
                except:
                    return row[0]
            return None

    def get_all_settings(self) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT key, value FROM settings")
            rows = cursor.fetchall()
            
        settings = {}
        for row in rows:
            key = row["key"]
            val = row["value"]
            try:
                settings[key] = json.loads(val)
            except:
                settings[key] = val
        return settings

    def save_setting(self, key: str, value: Any):
        if not isinstance(value, str):
            val_str = json.dumps(value)
        else:
            val_str = value
            
        with self.get_connection() as conn:
            conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, val_str))
            conn.commit()

    # --- Tags ---
    def get_tags(self) -> List[str]:
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT name FROM tags ORDER BY name ASC")
            rows = cursor.fetchall()
            return [r["name"] for r in rows]

    def add_tag(self, name: str):
        with self.get_connection() as conn:
            conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (name,))
            conn.commit()
