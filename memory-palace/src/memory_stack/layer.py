"""
Memory Stack — 四层记忆栈
L0: Identity / L1: Critical Facts / L2: Room Recall / L3: Deep Search
"""
from typing import Optional

from ..core.models import MemoryEntry
from ..core.store import MemoryStore
from ..search.engine import SearchEngine


class MemoryStack:
    """
    四层记忆栈
    
    L0: Identity — 始终加载 (~50 tokens)
    L1: Critical Facts — 始终加载 (~120 tokens)
    L2: Room Recall — 按 wing/room 加载 (~200-500 tokens)
    L3: Deep Search — 全量语义搜索 (无上限)
    """
    
    L0_CONTEXT = """
## Identity (L0)
- Name: 百万 (Bai Wan)
- Type: AI Assistant
- Vibe: 简洁、实用、不废话
- Emoji: 🚀
"""

    def __init__(self, store: MemoryStore, engine: SearchEngine):
        self.store = store
        self.engine = engine
    
    def get_l0_identity(self) -> str:
        """L0: Identity — 始终加载"""
        return self.L0_CONTEXT
    
    def get_l1_critical(self, wing: str = "user") -> str:
        """
        L1: Critical Facts — 始终加载
        TODO: 自动从记忆库提取关键事实
        """
        # TODO: Phase 3 实现自动提取
        return ""
    
    def get_l2_room(
        self,
        wing: str,
        room: str,
        limit: int = 20,
    ) -> str:
        """
        L2: Room Recall — 按 wing/room 过滤加载
        """
        memories = self.engine.search(
            query="",
            wing=wing,
            room=room,
            limit=limit,
        )
        
        if not memories:
            return ""
        
        lines = [f"## {room} memories:"]
        for m in memories:
            lines.append(f"- [{m.timestamp}] {m.content[:100]}")
        
        return "\n".join(lines)
    
    def get_l3_deep_search(
        self,
        query: str,
        wing: Optional[str] = None,
        limit: int = 10,
    ) -> list[MemoryEntry]:
        """
        L3: Deep Search — 全量语义搜索
        """
        # TODO: Phase 1 实现向量搜索
        return []
    
    def build_context(
        self,
        wing: str = "user",
        room: Optional[str] = None,
    ) -> str:
        """
        构建完整上下文（用于注入 Agent）
        """
        parts = [
            self.get_l0_identity(),
            self.get_l1_critical(wing),
        ]
        
        if room:
            l2 = self.get_l2_room(wing, room)
            if l2:
                parts.append(l2)
        
        return "\n\n".join(parts)
