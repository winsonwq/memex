"""
Hybrid Retrieval — 混合检索评分

final_score = 0.55×相似度 + 0.20×重要性 + 0.15×新鲜度 + 0.10×频率

新鲜度：用 last_updated 计算，指数衰减
频率：用 access_count 字段
"""

import math
from dataclasses import dataclass
from datetime import datetime
from typing import List

from ._types import MemoryRecord


# 混合评分权重
HYBRID_WEIGHTS = {
    "similarity": 0.55,
    "importance": 0.20,
    "recency": 0.15,
    "frequency": 0.10,
}

# 频率归一化：假设最多访问 100 次
MAX_FREQUENCY = 100.0


def calc_recency_score(last_updated: int, decay_rate: float = 0.001) -> float:
    """
    计算新鲜度分数（指数衰减）
    
    Args:
        last_updated: 毫秒时间戳
        decay_rate: 衰减率，越大衰减越快
    Returns:
        0-1 之间的分数，越新越高
    """
    now_ms = datetime.now().timestamp() * 1000
    age_days = (now_ms - last_updated) / (1000 * 60 * 60 * 24)
    return math.exp(-decay_rate * age_days)


def calc_frequency_score(access_count: int) -> float:
    """计算频率分数（线性归一化）"""
    return min(access_count / MAX_FREQUENCY, 1.0)


def hybrid_score(
    similarity: float,        # 0-1，向量相似度
    importance: float,        # 0-1，记忆重要性
    last_updated: int,       # 毫秒时间戳
    access_count: int = 0,   # 访问次数
) -> float:
    """
    计算混合检索分数
    
    Returns:
        0-1 之间的加权分数
    """
    recency = calc_recency_score(last_updated)
    frequency = calc_frequency_score(access_count)
    
    return (
        HYBRID_WEIGHTS["similarity"] * similarity +
        HYBRID_WEIGHTS["importance"] * importance +
        HYBRID_WEIGHTS["recency"] * recency +
        HYBRID_WEIGHTS["frequency"] * frequency
    )


def rerank_hybrid(
    records: List[MemoryRecord],
    similarities: List[float],
    limit: int = 10,
) -> List[tuple[MemoryRecord, float]]:
    """
    对检索结果进行混合重排
    
    Args:
        records: 记忆记录列表
        similarities: 对应的向量相似度分数
        limit: 返回数量
    Returns:
        (record, hybrid_score) 列表，按分数降序
    """
    if len(records) != len(similarities):
        raise ValueError("records and similarities must have same length")
    
    scored = []
    for record, sim in zip(records, similarities):
        access_count = record.metadata.get("access_count", 0)
        score = hybrid_score(
            similarity=sim,
            importance=record.importance,
            last_updated=record.last_updated,
            access_count=access_count,
        )
        scored.append((record, score))
    
    # 按分数降序
    scored.sort(key=lambda x: x[1], reverse=True)
    
    return scored[:limit]
