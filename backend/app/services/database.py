import sqlite3
import json
import os
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional, Any

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
            conn.execute("""
                CREATE TABLE IF NOT EXISTS practice_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    duration_minutes INTEGER DEFAULT 0,
                    notes TEXT,
                    tags TEXT,
                    sentiment TEXT,
                    created_at TEXT
                )
            """)
            # Index on date for faster range queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_date ON practice_logs (date)")
            conn.commit()

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
            pass
            
        results = []
        for row in rows:
            d = dict(row)
            # Parse tags from JSON string to list
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
                INSERT INTO practice_logs (date, duration_minutes, notes, tags, sentiment, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                data.get("date"),
                data.get("duration_minutes", 0),
                data.get("notes", ""),
                tags_json,
                data.get("sentiment", ""),
                created_at
            ))
            conn.commit()
            return cursor.lastrowid

    def update_log(self, log_id: int, data: Dict[str, Any]) -> bool:
        # Construct update query dynamically
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
        # Heatmap data: date + count + duration
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT date, COUNT(*) as count, SUM(duration_minutes) as duration
                FROM practice_logs
                GROUP BY date
                ORDER BY date ASC
            """)
            heatmap_rows = cursor.fetchall()
            
            # Totals
            cursor = conn.execute("SELECT SUM(duration_minutes) FROM practice_logs")
            total_duration = cursor.fetchone()[0] or 0
            
            # This week (approx implementation, SQLite date functions can be tricky)
            # Use 'now' modifier
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
