"""
Consolidation — 记忆合并

当两条记忆相似度 > 阈值时，合并为一条，保留信息更丰富的内容。
阈值：0.85（向量相似度）
"""

from typing import List, Tuple, Optional
import math

from ._types import MemoryRecord, MemoryType


# 合并阈值
SIMILARITY_THRESHOLD = 0.85


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """计算两个向量的余弦相似度"""
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return dot_product / (norm_a * norm_b)


def find_similar_pairs(
    records: List[MemoryRecord],
    vectors: List[List[float]],
    threshold: float = SIMILARITY_THRESHOLD,
) -> List[Tuple[int, int, float]]:
    """
    找出所有相似度 > threshold 的记忆对
    
    Returns:
        [(idx_a, idx_b, similarity), ...]
    """
    if len(records) != len(vectors):
        raise ValueError("records and vectors must have same length")
    
    pairs = []
    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            sim = cosine_similarity(vectors[i], vectors[j])
            if sim >= threshold:
                pairs.append((i, j, sim))
    
    # 按相似度降序
    pairs.sort(key=lambda x: x[2], reverse=True)
    return pairs


def consolidate_pair(
    record_a: MemoryRecord,
    record_b: MemoryRecord,
) -> MemoryRecord:
    """
    合并两条记忆
    
    策略：
    - 保留 content 更长/更详细的那条
    - importance 取两者较高
    - confidence 取两者平均
    - revision_count 取两者较大
    - 更新 last_updated
    - 记录合并来源
    """
    # 选择更好的内容（更长更详细）
    if len(record_b.content) > len(record_a.content):
        primary, secondary = record_b, record_a
    else:
        primary, secondary = record_a, record_b
    
    import time
    
    merged = MemoryRecord.from_dict(primary.to_dict())
    merged.importance = max(primary.importance, secondary.importance)
    merged.confidence = (primary.confidence + secondary.confidence) / 2
    merged.revision_count = max(primary.revision_count, secondary.revision_count) + 1
    merged.last_updated = int(time.time() * 1000)
    merged.metadata["consolidated"] = True
    merged.metadata["consolidated_from"] = [primary.id, secondary.id]
    merged.metadata["consolidated_at"] = int(time.time() * 1000)
    
    return merged


def consolidate_all(
    records: List[MemoryRecord],
    vectors: List[List[float]],
    threshold: float = SIMILARITY_THRESHOLD,
) -> List[Tuple[List[MemoryRecord], List[List[float]]]]:
    """
    合并所有相似的记忆
    
    Returns:
        每次合并的结果 [(remaining_records, remaining_vectors), ...]
        最终返回所有合并轮次的结果
    """
    import copy
    
    remaining_records = list(records)
    remaining_vectors = list(vectors)
    history = []
    
    while True:
        pairs = find_similar_pairs(remaining_records, remaining_vectors, threshold)
        if not pairs:
            break
        
        # 合并第一对（最高相似度）
        idx_a, idx_b, sim = pairs[0]
        
        merged = consolidate_pair(remaining_records[idx_a], remaining_records[idx_b])
        
        # 移除被合并的两个，插入合并结果
        # 先处理索引较大的，再处理索引小的
        max_idx = max(idx_a, idx_b)
        min_idx = min(idx_a, idx_b)
        
        new_records = remaining_records.copy()
        new_vectors = remaining_vectors.copy()
        
        del new_records[max_idx]
        del new_vectors[max_idx]
        del new_records[min_idx]
        del new_vectors[min_idx]
        
        new_records.insert(min_idx, merged)
        # 用被合并的两个向量的平均作为新向量
        avg_vector = [(v1 + v2) / 2 for v1, v2 in zip(remaining_vectors[idx_a], remaining_vectors[idx_b])]
        new_vectors.insert(min_idx, avg_vector)
        
        history.append((list(remaining_records), list(remaining_vectors)))
        
        remaining_records = new_records
        remaining_vectors = new_vectors
    
    return history
