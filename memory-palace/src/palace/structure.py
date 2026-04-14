"""
Palace — 宫殿结构管理
Wing / Room / Closet / Drawer
"""
from typing import Optional

from ..core.models import MemoryEntry, Wing
from ..core.store import MemoryStore
from ..search.engine import SearchEngine
from ..search.vector_index import VectorIndex


class Palace:
    """
    宫殿结构管理器
    
    层级结构：
    - Wing（翅膀）= 人 / 项目 ← 顶层隔离
    - Room（房间）= 具体话题
    - Closet（衣柜）= AAAK 压缩摘要（可选）
    - Drawer（抽屉）= 原始 verbatim 内容
    """
    
    def __init__(
        self,
        store: MemoryStore,
        vector_index: Optional[VectorIndex] = None,
    ):
        self.store = store
        self.vector_index = vector_index
        self.search_engine = SearchEngine(store, vector_index)
    
    def create_wing(
        self,
        name: str,
        wing_type: str,
        description: str = "",
    ) -> Wing:
        """创建 Wing（顶层隔离）"""
        wing = Wing(name=name, wing_type=wing_type, description=description)
        return self.store.add_wing(wing)
    
    def add_memory(
        self,
        content: str,
        wing: str,
        room: str,
        hall: str = "none",
        tags: list[str] = None,
        source: str = "manual",
    ) -> MemoryEntry:
        """
        添加记忆到指定 wing/room
        
        设计原则：Verbatim 存储，不做 LLM 摘要
        """
        entry = MemoryEntry(
            content=content,
            wing=wing,
            room=room,
            hall=hall,
            tags=tags or [],
            source=source,
        )
        
        # SQLite 存储
        self.store.add_entry(entry)
        
        # 向量索引（Phase 1）
        if self.vector_index is not None:
            self.vector_index.add(entry)
        
        return entry
    
    def get_room_memories(
        self,
        wing: str,
        room: str,
        limit: int = 50,
    ) -> list[MemoryEntry]:
        """获取指定 Room 的所有记忆"""
        return self.store.search(wing=wing, room=room, limit=limit)
    
    def get_wing_memories(
        self,
        wing: str,
        limit: int = 100,
    ) -> list[MemoryEntry]:
        """获取指定 Wing 的所有记忆"""
        return self.store.search(wing=wing, limit=limit)
    
    def search_memories(
        self,
        query: str,
        wing: Optional[str] = None,
        room: Optional[str] = None,
        limit: int = 10,
    ) -> list[MemoryEntry]:
        """
        搜索记忆
        
        - 有向量索引 → 语义搜索
        - 无向量索引 → SQL LIKE
        """
        return self.search_engine.search(
            query=query,
            wing=wing,
            room=room,
            limit=limit,
        )
