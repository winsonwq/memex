"""
Storage — SQLite + LanceDB 存储层
Verbatim 原文存储，不做 LLM 提取
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import MemoryEntry, Wing


class MemoryStore:
    """记忆存储层 — SQLite"""
    
    def __init__(self, db_path: str = "data/memory.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """初始化数据库 schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS entries (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    wing TEXT NOT NULL,
                    room TEXT NOT NULL,
                    hall TEXT DEFAULT 'none',
                    closet TEXT,
                    drawer_id TEXT,
                    tags TEXT DEFAULT '[]',
                    source TEXT DEFAULT 'manual',
                    timestamp TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS wings (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    type TEXT NOT NULL,
                    description TEXT DEFAULT ''
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_entries_wing_room 
                ON entries(wing, room)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_entries_hall 
                ON entries(hall)
            """)
    
    def add_entry(self, entry: MemoryEntry) -> MemoryEntry:
        """添加记忆条目"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO entries 
                   (id, content, wing, room, hall, closet, drawer_id, tags, source, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    entry.id,
                    entry.content,
                    entry.wing,
                    entry.room,
                    entry.hall,
                    entry.closet,
                    entry.drawer_id,
                    json.dumps(entry.tags),
                    entry.source,
                    entry.timestamp,
                )
            )
        return entry
    
    def get_entry(self, entry_id: str) -> Optional[MemoryEntry]:
        """获取单条记忆"""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM entries WHERE id = ?", (entry_id,)
            ).fetchone()
            
            if not row:
                return None
            
            return self._row_to_entry(row)
    
    def search(
        self,
        wing: Optional[str] = None,
        room: Optional[str] = None,
        hall: Optional[str] = None,
        limit: int = 10,
    ) -> list[MemoryEntry]:
        """基础搜索（SQL 层面）"""
        query = "SELECT * FROM entries WHERE 1=1"
        params = []
        
        if wing:
            query += " AND wing = ?"
            params.append(wing)
        
        if room:
            query += " AND room = ?"
            params.append(room)
        
        if hall and hall != "none":
            query += " AND hall = ?"
            params.append(hall)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_entry(row) for row in rows]
    
    def _row_to_entry(self, row: sqlite3.Row) -> MemoryEntry:
        """Row -> MemoryEntry"""
        return MemoryEntry(
            id=row[0],
            content=row[1],
            wing=row[2],
            room=row[3],
            hall=row[4],
            closet=row[5],
            drawer_id=row[6],
            tags=json.loads(row[7]),
            source=row[8],
            timestamp=row[9],
        )
    
    # --- Wing 管理 ---
    
    def add_wing(self, wing: Wing) -> Wing:
        """添加 Wing"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO wings (id, name, type, description) VALUES (?, ?, ?, ?)",
                (wing.id, wing.name, wing.wing_type, wing.description),
            )
        return wing
    
    def get_wings(self) -> list[Wing]:
        """获取所有 Wings"""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT * FROM wings").fetchall()
            return [
                Wing(id=r[0], name=r[1], wing_type=r[2], description=r[3])
                for r in rows
            ]
