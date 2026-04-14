"""
Types — 核心类型定义
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4


class MemoryType(Enum):
    """记忆类型"""
    CONSTRAINT = "constraint"       # 约束/禁令 (importance: 0.9)
    USER_MODEL = "user_model"       # 用户偏好 (importance: 0.85)
    STRATEGY = "strategy"           # 策略方法 (importance: 0.8)
    SYSTEM_PATTERN = "system_pattern" # 系统模式 (importance: 0.75)
    BELIEF = "belief"               # 验证结论 (importance: 0.7)
    JOURNAL = "journal"             # 工作日志 (importance: 0.4)


# 默认 importance 映射
DEFAULT_IMPORTANCE = {
    MemoryType.CONSTRAINT: 0.9,
    MemoryType.USER_MODEL: 0.85,
    MemoryType.STRATEGY: 0.8,
    MemoryType.SYSTEM_PATTERN: 0.75,
    MemoryType.BELIEF: 0.7,
    MemoryType.JOURNAL: 0.4,
}


@dataclass
class MemoryRecord:
    """记忆记录"""
    type: MemoryType
    content: str                    # 规范化后的语义陈述
    raw_text: str                   # 原始文本，用于模型升级后重建索引
    
    # PRD v2.0 核心字段
    importance: float = 0.7         # 0-1，对推理的影响程度
    confidence: float = 0.8         # 0-1，确定性
    stability: str = "medium"       # 'low' | 'medium' | 'high'
    revision_count: int = 0
    
    # 关系
    contradicts: list[str] = field(default_factory=list)
    supports: list[str] = field(default_factory=list)
    derived_from: str = ""
    
    # 时间
    created_at: int = field(default_factory=lambda: int(datetime.now().timestamp() * 1000))
    last_updated: int = field(default_factory=lambda: int(datetime.now().timestamp() * 1000))
    last_accessed: int = field(default_factory=lambda: int(datetime.now().timestamp() * 1000))
    expires_at: int = field(default_factory=lambda: 9999999999999)  # 永久
    
    # 元数据
    repo: str = "default"
    title: str = ""
    metadata: dict = field(default_factory=dict)
    trust: float = 1.0
    
    # 自动生成
    id: str = field(default_factory=lambda: str(uuid4()))
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "raw_text": self.raw_text,
            "importance": self.importance,
            "confidence": self.confidence,
            "stability": self.stability,
            "revision_count": self.revision_count,
            "contradicts": self.contradicts,
            "supports": self.supports,
            "derived_from": self.derived_from,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "last_accessed": self.last_accessed,
            "expires_at": self.expires_at,
            "repo": self.repo,
            "title": self.title,
            "metadata": self.metadata,
            "trust": self.trust,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "MemoryRecord":
        data = dict(data)
        data["type"] = MemoryType(data.get("type", "belief"))
        return cls(**data)
