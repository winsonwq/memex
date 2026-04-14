"""
Hybrid Retrieval 单元测试
"""
import pytest
import sys
import time
sys.path.insert(0, 'src')

from memex._hybrid import (
    calc_recency_score,
    calc_frequency_score,
    hybrid_score,
    rerank_hybrid,
    HYBRID_WEIGHTS,
)
from memex._types import MemoryRecord, MemoryType


class TestHybridWeights:
    """权重验证"""
    
    def test_weights_sum_to_one(self):
        total = sum(HYBRID_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001


class TestRecencyScore:
    """新鲜度分数"""
    
    def test_new_record_score_high(self):
        """刚创建的记录新鲜度接近 1"""
        now_ms = int(time.time() * 1000)
        score = calc_recency_score(now_ms)
        assert score > 0.99
    
    def test_old_record_score_lower_than_new(self):
        """旧记录新鲜度低于新记录"""
        old_ms = int((time.time() - 30 * 24 * 3600) * 1000)
        new_ms = int(time.time() * 1000)
        
        score_new = calc_recency_score(new_ms)
        score_old = calc_recency_score(old_ms)
        
        assert score_new > score_old
        # 30 天后仍然有 ~0.97（因为 recency 权重只有 15%，衰减慢是合理的）
        assert score_old > 0.9
    
    def test_decay_rate(self):
        """更高的衰减率导致更低的分数"""
        now_ms = int(time.time() * 1000)
        score_slow = calc_recency_score(now_ms, decay_rate=0.001)
        score_fast = calc_recency_score(now_ms, decay_rate=0.01)
        assert score_fast < score_slow


class TestFrequencyScore:
    """频率分数"""
    
    def test_zero_access(self):
        assert calc_frequency_score(0) == 0.0
    
    def test_max_frequency(self):
        assert calc_frequency_score(100) == 1.0
    
    def test_capped_at_one(self):
        assert calc_frequency_score(200) == 1.0


class TestHybridScore:
    """混合评分"""
    
    def test_high_similarity_wins(self):
        """相似度权重最高，高相似度应该得高分"""
        now_ms = int(time.time() * 1000)
        
        # 纯相似度 1.0
        score_sim_only = hybrid_score(
            similarity=1.0,
            importance=0.0,
            last_updated=now_ms,
            access_count=0,
        )
        
        # 纯重要性 1.0
        score_imp_only = hybrid_score(
            similarity=0.0,
            importance=1.0,
            last_updated=now_ms,
            access_count=0,
        )
        
        assert score_sim_only > score_imp_only
        assert score_sim_only > 0.5  # 至少 0.55 × 1.0
    
    def test_combination(self):
        """组合分数在合理范围"""
        now_ms = int(time.time() * 1000)
        score = hybrid_score(
            similarity=0.8,
            importance=0.7,
            last_updated=now_ms,
            access_count=50,
        )
        assert 0.0 <= score <= 1.0


class TestRerank:
    """重排"""
    
    def test_rerank_preserves_count(self):
        """重排不改变结果数量（不超过 limit）"""
        records = [
            MemoryRecord(
                type=MemoryType.BELIEF,
                content=f"test {i}",
                raw_text=f"raw {i}",
                importance=0.5,
            )
            for i in range(20)
        ]
        similarities = [0.5 + i * 0.01 for i in range(20)]
        
        result = rerank_hybrid(records, similarities, limit=10)
        assert len(result) == 10
    
    def test_rerank_sorts_by_score(self):
        """重排后按分数降序"""
        records = [
            MemoryRecord(
                type=MemoryType.BELIEF,
                content=f"test {i}",
                raw_text=f"raw {i}",
                importance=0.5,
            )
            for i in range(5)
        ]
        # 故意乱序的相似度
        similarities = [0.1, 0.9, 0.3, 0.7, 0.5]
        
        result = rerank_hybrid(records, similarities)
        scores = [s for _, s in result]
        assert scores == sorted(scores, reverse=True)
    
    def test_rerank_uses_importance(self):
        """重要性高的记录应该排得更前"""
        now_ms = int(time.time() * 1000)
        
        records = [
            MemoryRecord(
                type=MemoryType.BELIEF,
                content="low importance",
                raw_text="raw",
                importance=0.1,
            ),
            MemoryRecord(
                type=MemoryType.CONSTRAINT,
                content="high importance",
                raw_text="raw",
                importance=0.9,
            ),
        ]
        # 两者相似度相同
        similarities = [0.8, 0.8]
        
        result = rerank_hybrid(records, similarities)
        # 高重要性的应该排第一
        assert result[0][0].importance > result[1][0].importance
    
    def test_rerank_empty(self):
        result = rerank_hybrid([], [])
        assert result == []


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
