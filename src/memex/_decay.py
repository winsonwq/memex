"""
Decay & Forgetting — 衰减与遗忘

基于访问频率和新鲜度计算 decay 分数。
decay ≥ 0.7 → 归档（importance → 0.05）

归档策略：
- 低价值记忆在存储中降级（降低 importance）
- 高价值记忆（CONSTRAINT）永不归档
"""

import time
from dataclasses import dataclass
from typing import List, Tuple

from ._types import MemoryRecord, MemoryType


# Decay 阈值
DECAY_THRESHOLD = 0.7

# 归档后的 importance
ARCHIVED_IMPORTANCE = 0.05


def calc_decay_score(
    last_accessed: int,      # 上次访问时间（毫秒）
    access_count: int,       # 访问次数
    importance: float,        # 当前重要性
    created_at: int,         # 创建时间（毫秒）
) -> float:
    """
    计算 decay 分数（0-1，越高越需要归档）
    
    衰减因素：
    - 新鲜度：越久没更新越高
    - 访问频率：越少访问越高
    - 年龄：越老越高
    """
    now_ms = time.time() * 1000
    
    # 年龄因子（每年衰减 0.1）
    age_days = (now_ms - created_at) / (1000 * 60 * 60 * 24)
    age_factor = min(age_days / (365 * 5), 1.0) * 0.3  # 最多 0.3
    
    # 新鲜度因子（越久没访问越高）
    days_since_access = (now_ms - last_accessed) / (1000 * 60 * 60 * 24)
    recency_factor = min(days_since_access / 90, 1.0) * 0.4  # 90 天封顶，0.4
    
    # 访问频率因子（越少访问越高）
    freq_factor = max(0, 1.0 - (access_count / 50)) * 0.3  # 50 次以上饱和，0.3
    
    return age_factor + recency_factor + freq_factor


def should_archive(
    record: MemoryRecord,
    decay_threshold: float = DECAY_THRESHOLD,
) -> bool:
    """
    判断记忆是否应该归档
    """
    # CONSTRAINT 和 USER_MODEL 永不归档
    if record.type in (MemoryType.CONSTRAINT, MemoryType.USER_MODEL):
        return False
    
    # 从 metadata 获取访问统计
    access_count = record.metadata.get("access_count", 0)
    
    decay = calc_decay_score(
        last_accessed=record.last_accessed,
        access_count=access_count,
        importance=record.importance,
        created_at=record.created_at,
    )
    
    return decay >= decay_threshold


def archive_record(record: MemoryRecord) -> MemoryRecord:
    """
    归档一条记忆（降低 importance 到 0.05）
    """
    archived = MemoryRecord.from_dict(record.to_dict())
    archived.importance = ARCHIVED_IMPORTANCE
    archived.metadata["archived"] = True
    archived.metadata["archived_at"] = int(time.time() * 1000)
    return archived


def find_records_to_archive(
    records: List[MemoryRecord],
) -> List[Tuple[MemoryRecord, float]]:
    """
    找出所有需要归档的记忆
    
    Returns:
        [(record, decay_score), ...] 按 decay 降序
    """
    candidates = []
    for r in records:
        if should_archive(r):
            access_count = r.metadata.get("access_count", 0)
            decay = calc_decay_score(
                last_accessed=r.last_accessed,
                access_count=access_count,
                importance=r.importance,
                created_at=r.created_at,
            )
            candidates.append((r, decay))
    
    # 按 decay 降序
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates
