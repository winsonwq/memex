"""
Search — 向量搜索召回层
TODO: LanceDB 集成（Phase 1）
"""
from typing import Optional

from ..core.models import MemoryEntry
from ..core.store import MemoryStore


class SearchEngine:
    """搜索召回引擎"""
    
    def __init__(self, store: MemoryStore):
        self.store = store
    
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
        
        1. 精确匹配（wing + room + hall）
        2. 向量语义搜索（LanceDB，Phase 1）
        3. 全文搜索（SQLite FTS，Phase 1）
        """
        # Phase 0: 基础 SQL 搜索
        results = self.store.search(
            wing=wing,
            room=room,
            hall=hall,
            limit=limit,
        )
        
        # TODO: Phase 1 加入向量搜索
        # TODO: Phase 1 加入 FTS 搜索
        
        return results
    
    def search_by_content(
        self,
        content_query: str,
        wing: Optional[str] = None,
        limit: int = 10,
    ) -> list[MemoryEntry]:
        """
        按内容搜索（Phase 1 实现）
        目前是 SQL LIKE 近似
        """
        # TODO: Phase 1 替换为向量搜索
        with self.store.db_path as db:
            # 临时实现
            pass
        return []
