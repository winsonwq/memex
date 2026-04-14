"""
Memory Store — 内存实现（测试用）
"""
from typing import Optional, List

from .._types import MemoryRecord
from .interface import VectorStore


class MemoryStore(VectorStore):
    """内存向量存储（测试用）"""
    
    def __init__(self):
        self.records: dict[str, MemoryRecord] = {}
        self.vectors: dict[str, List[float]] = {}
    
    def add(self, record: MemoryRecord, vector: List[float]) -> None:
        self.records[record.id] = record
        self.vectors[record.id] = vector
    
    def search(
        self,
        query_vector: List[float],
        repo: Optional[str] = None,
        limit: int = 10,
    ) -> list[tuple[MemoryRecord, float]]:
        # 简单余弦相似度
        results = []
        for record_id, vector in self.vectors.items():
            if repo and self.records[record_id].repo != repo:
                continue
            
            record = self.records[record_id]
            
            # 简化：计算简单相似度
            score = self._cosine_similarity(query_vector, vector)
            results.append((record, score))
        
        # 排序
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]
    
    def search_by_content(
        self,
        content: str,
        repo: Optional[str] = None,
        limit: int = 10,
    ) -> list[tuple[MemoryRecord, float]]:
        # 简单的关键词匹配
        results = []
        for record in self.records.values():
            if repo and record.repo != repo:
                continue
            if content.lower() in record.content.lower():
                results.append((record, 0.5))
        return results[:limit]
    
    def get(self, record_id: str) -> Optional[MemoryRecord]:
        return self.records.get(record_id)
    
    def list(
        self,
        repo: Optional[str] = None,
        type: Optional[str] = None,
        limit: int = 100,
    ) -> list[MemoryRecord]:
        results = list(self.records.values())
        
        if repo:
            results = [r for r in results if r.repo == repo]
        if type:
            results = [r for r in results if r.type.value == type]
        
        return results[:limit]
    
    def update(self, record: MemoryRecord) -> None:
        self.records[record.id] = record
    
    def delete(self, record_id: str) -> None:
        self.records.pop(record_id, None)
        self.vectors.pop(record_id, None)
    
    def count(self, repo: Optional[str] = None) -> int:
        if repo is None:
            return len(self.records)
        return len([r for r in self.records.values() if r.repo == repo])
    
    def close(self) -> None:
        pass
    
    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        """计算余弦相似度"""
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
