"""
Memory Stack — 四层记忆栈
L0: Identity / L1: Critical Facts / L2: Room Recall / L3: Deep Search

Phase 1: L2 Room Recall 使用向量搜索
"""
from typing import Optional

from ..core.models import MemoryEntry
from ..core.store import MemoryStore
from ..search.engine import SearchEngine
from ..search.vector_index import VectorIndex


class MemoryStack:
    """
    四层记忆栈
    
    设计原则：
    - L0/L1 始终加载，保持轻量
    - L2/L3 按需加载，支持 token 预算控制
    - Verbatim 原文存储，不依赖 LLM 提取
    
    | Layer | 内容 | Token 估计 | 何时加载 |
    |-------|------|-----------|---------|
    | L0 | Identity | ~50 | 始终 |
    | L1 | Critical Facts | ~120 | 始终 |
    | L2 | Room Recall | ~200-500 | 按 wing/room |
    | L3 | Deep Search | 无上限 | 按需查询 |
    """
    
    # L0: Identity — 始终加载
    L0_CONTEXT = """## Identity (L0)
- Name: 百万 (Bai Wan)
- Type: AI Assistant
- Vibe: 简洁、实用、不废话
- Emoji: 🚀
"""
    
    def __init__(
        self,
        store: MemoryStore,
        search_engine: SearchEngine,
        vector_index: Optional[VectorIndex] = None,
    ):
        self.store = store
        self.search_engine = search_engine
        self.vector_index = vector_index
    
    def get_l0_identity(self) -> str:
        """L0: Identity — 始终加载"""
        return self.L0_CONTEXT
    
    def get_l1_critical(self, wing: str = "user") -> str:
        """
        L1: Critical Facts — 始终加载
        
        TODO: Phase 3 自动从记忆库提取关键事实
        目前返回空字符串，手动维护
        """
        # TODO: Phase 3 实现自动提取
        # 从记忆中提取：
        # - 用户偏好
        # - 关键项目
        # - 重要决策
        return ""
    
    def get_l2_room(
        self,
        wing: str,
        room: str,
        limit: int = 20,
    ) -> str:
        """
        L2: Room Recall — 按 wing/room 过滤加载
        
        Phase 1: 使用向量搜索（如果有向量索引）
        Phase 0: 使用 SQL 搜索
        """
        if self.vector_index is not None:
            # Phase 1: 向量语义搜索
            results = self.vector_index.search(
                query="",  # 空 query = 按 wing/room 过滤
                wing=wing,
                room=room,
                limit=limit,
            )
            
            if not results:
                return ""
            
            # 构建上下文
            lines = [f"## {room} memories:"]
            for r in results:
                ts = r.get("timestamp", "unknown")
                content = r.get("content", "")
                lines.append(f"- [{ts}] {content[:150]}")
            
            return "\n".join(lines)
        else:
            # Phase 0: SQL 搜索
            memories = self.search_engine.search(
                query="",
                wing=wing,
                room=room,
                limit=limit,
            )
            
            if not memories:
                return ""
            
            lines = [f"## {room} memories:"]
            for m in memories:
                lines.append(f"- [{m.timestamp}] {m.content[:150]}")
            
            return "\n".join(lines)
    
    def get_l3_deep_search(
        self,
        query: str,
        wing: Optional[str] = None,
        room: Optional[str] = None,
        limit: int = 10,
    ) -> list[MemoryEntry]:
        """
        L3: Deep Search — 全量语义搜索
        
        Phase 1: 向量搜索
        """
        return self.search_engine.search(
            query=query,
            wing=wing,
            room=room,
            limit=limit,
        )
    
    def build_context(
        self,
        wing: str = "user",
        room: Optional[str] = None,
        max_tokens: int = 500,
    ) -> str:
        """
        构建完整上下文（用于注入 Agent）
        
        Phase 1: L0 + L1 + L2（按 wing/room）
        """
        parts = [
            self.get_l0_identity(),
        ]
        
        l1 = self.get_l1_critical(wing)
        if l1:
            parts.append(f"## Critical Facts (L1)\n{l1}")
        
        if room:
            l2 = self.get_l2_room(wing, room)
            if l2:
                parts.append(l2)
        
        context = "\n\n".join(parts)
        
        # Token 预算控制（粗略：1 token ≈ 4 字符）
        max_chars = max_tokens * 4
        if len(context) > max_chars:
            context = context[:max_chars] + "\n...(truncated)"
        
        return context
