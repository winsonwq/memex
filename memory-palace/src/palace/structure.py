"""
Palace — 宫殿结构管理
Wing / Room / Closet / Drawer
"""
from typing import Optional

from ..core.models import MemoryEntry, Wing
from ..core.store import MemoryStore


class Palace:
    """宫殿结构管理器"""
    
    def __init__(self, store: MemoryStore):
        self.store = store
    
    def create_wing(self, name: str, wing_type: str, description: str = "") -> Wing:
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
        """添加记忆到指定 wing/room"""
        entry = MemoryEntry(
            content=content,
            wing=wing,
            room=room,
            hall=hall,
            tags=tags or [],
            source=source,
        )
        return self.store.add_entry(entry)
    
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
