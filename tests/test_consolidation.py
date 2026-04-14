"""
Consolidation 单元测试
"""
import pytest
import sys
sys.path.insert(0, 'src')

from memex._consolidation import (
    cosine_similarity,
    find_similar_pairs,
    consolidate_pair,
    SIMILARITY_THRESHOLD,
)
from memex._types import MemoryRecord, MemoryType


class TestCosineSimilarity:
    """余弦相似度"""
    
    def test_identical_vectors(self):
        v = [0.1, 0.2, 0.3, 0.4]
        assert abs(cosine_similarity(v, v) - 1.0) < 0.0001
    
    def test_orthogonal_vectors(self):
        v1 = [1.0, 0.0, 0.0]
        v2 = [0.0, 1.0, 0.0]
        assert abs(cosine_similarity(v1, v2)) < 0.0001
    
    def test_opposite_vectors(self):
        v1 = [1.0, 0.0]
        v2 = [-1.0, 0.0]
        assert abs(cosine_similarity(v1, v2) + 1.0) < 0.0001
    
    def test_partial_similarity(self):
        v1 = [1.0, 0.0]
        v2 = [0.5, 0.5]
        sim = cosine_similarity(v1, v2)
        assert 0 < sim < 1


class TestFindSimilarPairs:
    """查找相似对"""
    
    def test_no_pairs_below_threshold(self):
        records = [
            MemoryRecord(type=MemoryType.BELIEF, content="Python 很好", raw_text="Python 很好"),
            MemoryRecord(type=MemoryType.BELIEF, content="JavaScript 很好", raw_text="JavaScript 很好"),
        ]
        vectors = [[1.0, 0.0], [0.0, 1.0]]  # 正交向量
        
        pairs = find_similar_pairs(records, vectors)
        assert len(pairs) == 0
    
    def test_finds_pair_above_threshold(self):
        records = [
            MemoryRecord(type=MemoryType.BELIEF, content="Python 很好", raw_text="Python 很好"),
            MemoryRecord(type=MemoryType.BELIEF, content="Python 很好用", raw_text="Python 很好用"),
        ]
        vectors = [[1.0, 0.0], [1.0, 0.1]]  # 高度相似
        
        pairs = find_similar_pairs(records, vectors)
        assert len(pairs) == 1
    
    def test_threshold_is_inclusive(self):
        """阈值是 inclusive: >= threshold"""
        records = [
            MemoryRecord(type=MemoryType.BELIEF, content="test", raw_text="test"),
            MemoryRecord(type=MemoryType.BELIEF, content="test", raw_text="test"),
        ]
        vectors = [[1.0, 0.0], [1.0, 0.0]]  # 完全相同
        
        pairs = find_similar_pairs(records, vectors)
        assert len(pairs) == 1


class TestConsolidatePair:
    """合并两条记忆"""
    
    def test_longer_content_preserved(self):
        a = MemoryRecord(
            type=MemoryType.BELIEF,
            content="Python 很好",
            raw_text="Python 很好",
        )
        b = MemoryRecord(
            type=MemoryType.BELIEF,
            content="Python 是一门很棒的编程语言，特别适合数据科学",
            raw_text="Python 是一门很棒的编程语言，特别适合数据科学",
        )
        
        merged = consolidate_pair(a, b)
        assert merged.content == b.content
        assert merged.metadata.get("consolidated") is True
    
    def test_higher_importance_preserved(self):
        a = MemoryRecord(
            type=MemoryType.BELIEF,
            content="Python 很好",
            raw_text="Python 很好",
            importance=0.5,
        )
        b = MemoryRecord(
            type=MemoryType.BELIEF,
            content="Java 也不错",
            raw_text="Java 也不错",
            importance=0.9,
        )
        
        merged = consolidate_pair(a, b)
        assert merged.importance == 0.9
    
    def test_revision_count_increments(self):
        a = MemoryRecord(
            type=MemoryType.BELIEF,
            content="Python 很好",
            raw_text="Python 很好",
            revision_count=2,
        )
        b = MemoryRecord(
            type=MemoryType.BELIEF,
            content="Java 也不错",
            raw_text="Java 也不错",
            revision_count=5,
        )
        
        merged = consolidate_pair(a, b)
        assert merged.revision_count > max(2, 5)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
