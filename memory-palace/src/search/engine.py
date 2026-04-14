"""
Search — 搜索召回引擎
Phase 1: SQLite SQL 搜索 + LanceDB 向量搜索
"""
from typing import Optional

from ..core.models import MemoryEntry
from ..core.store import MemoryStore
from .vector_index import VectorIndex


class SearchEngine:
    """
    搜索召回引擎
    
    搜索层次（Phase 1 实现）：
    1. 精确匹配（wing + room + hall）— SQL
    2. 向量语义搜索 — LanceDB
    3. 全文搜索 — Phase 2
    
    设计原则：简单方法优先，不过度工程
    """
    
    def __init__(
        self,
        store: MemoryStore,
        vector_index: Optional[VectorIndex] = None,
    ):
        self.store = store
        self.vector_index = vector_index
    
    def search(
        self,
        query: str,
        wing: Optional[str] = None,
        room: Optional[str] = None,
        hall: Optional[str] = None,
        limit: int = 10,
    ) -> list[MemoryEntry]:
        """
        多层次搜索召回
        
        - 无 query → SQL 精确匹配
        - 有 query → 向量语义搜索
        """
        if not query:
            # Phase 0: 纯 SQL 搜索
            return self.store.search(
                wing=wing,
                room=room,
                hall=hall,
                limit=limit,
            )
        
        if self.vector_index is None:
            # 没有向量索引，降级到 SQL LIKE
            return self._search_sql_like(query, wing, room, limit)
        
        # Phase 1: 向量搜索
        return self._search_vector(query, wing, room, limit)
    
    def _search_vector(
        self,
        query: str,
        wing: Optional[str] = None,
        room: Optional[str] = None,
        limit: int = 10,
    ) -> list[MemoryEntry]:
        """向量语义搜索"""
        results = self.vector_index.search(
            query=query,
            wing=wing,
            room=room,
            limit=limit,
        )
        
        # 转换为 MemoryEntry
        entries = []
        for r in results:
            entry = self.store.get_entry(r["id"])
            if entry:
                entries.append(entry)
        
        return entries
    
    def _search_sql_like(
        self,
        query: str,
        wing: Optional[str] = None,
        room: Optional[str] = None,
        limit: int = 10,
    ) -> list[MemoryEntry]:
        """SQL LIKE 近似搜索（降级方案）"""
        import sqlite3
        
        sql = "SELECT * FROM entries WHERE content LIKE ?"
        params = [f"%{query}%"]
        
        if wing:
            sql += " AND wing = ?"
            params.append(wing)
        
        if room:
            sql += " AND room = ?"
            params.append(room)
        
        sql += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.store.db_path) as conn:
            rows = conn.execute(sql, params).fetchall()
            return [self.store._row_to_entry(row) for row in rows]
    
    def search_by_content(
        self,
        content_query: str,
        wing: Optional[str] = None,
        limit: int = 10,
    ) -> list[MemoryEntry]:
        """按内容搜索"""
        return self.search(
            query=content_query,
            wing=wing,
            limit=limit,
        )
