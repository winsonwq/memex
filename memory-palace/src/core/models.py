"""
Memory Entry — 记忆条目
Verbatim 存储，不依赖 LLM 提取
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import uuid4


@dataclass
class MemoryEntry:
    """记忆条目 — 原文存储"""
    
    content: str  # verbatim 原文
    wing: str  # 顶层：user | project_name
    room: str  # 话题：topic_name
    hall: str = "none"  # facts | events | discoveries | preferences | none
    closet: Optional[str] = None  # AAAK 压缩摘要（可选）
    drawer_id: Optional[str] = None  # 父抽屉 ID
    tags: list[str] = field(default_factory=list)
    source: str = "manual"  # session | file | manual
    
    # 自动生成
    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "wing": self.wing,
            "room": self.room,
            "hall": self.hall,
            "closet": self.closet,
            "drawer_id": self.drawer_id,
            "tags": self.tags,
            "source": self.source,
            "timestamp": self.timestamp,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        return cls(
            id=data["id"],
            content=data["content"],
            wing=data["wing"],
            room=data["room"],
            hall=data.get("hall", "none"),
            closet=data.get("closet"),
            drawer_id=data.get("drawer_id"),
            tags=data.get("tags", []),
            source=data.get("source", "manual"),
            timestamp=data["timestamp"],
        )


@dataclass
class Wing:
    """Wing — 顶层隔离（人/项目）"""
    
    name: str
    wing_type: str  # user | project
    description: str = ""
    
    id: str = field(default_factory=lambda: str(uuid4()))
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.wing_type,
            "description": self.description,
        }
