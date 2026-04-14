"""
Contradiction Detection 单元测试
"""
import pytest
import sys
sys.path.insert(0, 'src')

from memex._types import MemoryRecord, MemoryType
from memex._contradiction import (
    detect_record_pair_contradiction,
    find_contradictions,
    apply_contradiction_penalty,
    ContradictionResult,
)


class TestDetectPairContradiction:
    """检测两条记忆之间的矛盾"""
    
    def test_no_contradiction_different_topics(self):
        """不同话题无矛盾"""
        a = MemoryRecord(type=MemoryType.BELIEF, content="Python 是最好的语言", raw_text="Python 是最好的语言")
        b = MemoryRecord(type=MemoryType.BELIEF, content="JavaScript 也很流行", raw_text="JavaScript 也很流行")
        
        result = detect_record_pair_contradiction(a, b)
        assert result.has_contradiction is False
    
    def test_negation_contradiction_chinese(self):
        """中文否定矛盾"""
        a = MemoryRecord(type=MemoryType.BELIEF, content="这个项目使用 Python", raw_text="这个项目使用 Python")
        b = MemoryRecord(type=MemoryType.BELIEF, content="这个项目不使用 Python", raw_text="这个项目不使用 Python")
        
        result = detect_record_pair_contradiction(a, b)
        assert result.has_contradiction is True
        assert result.pattern == "negation"
    
    def test_negation_contradiction_english(self):
        """英文否定矛盾"""
        a = MemoryRecord(type=MemoryType.BELIEF, content="We use Python for this project", raw_text="We use Python for this project")
        b = MemoryRecord(type=MemoryType.BELIEF, content="We do not use Python for this project", raw_text="We do not use Python for this project")
        
        result = detect_record_pair_contradiction(a, b)
        assert result.has_contradiction is True
    
    def test_action_conflict(self):
        """行为冲突"""
        a = MemoryRecord(type=MemoryType.BELIEF, content="推荐使用分治法", raw_text="推荐使用分治法")
        b = MemoryRecord(type=MemoryType.BELIEF, content="不建议使用分治法", raw_text="不建议使用分治法")
        
        result = detect_record_pair_contradiction(a, b)
        assert result.has_contradiction is True
        assert result.pattern in ("negation", "action_conflict")
    
    def test_same_content_no_contradiction(self):
        """相同内容无矛盾"""
        a = MemoryRecord(type=MemoryType.BELIEF, content="Python 是最好的语言", raw_text="Python 是最好的语言")
        b = MemoryRecord(type=MemoryType.BELIEF, content="Python 是最好的语言", raw_text="Python 是最好的语言")
        
        result = detect_record_pair_contradiction(a, b)
        assert result.has_contradiction is False


class TestFindContradictions:
    """批量查找矛盾"""
    
    def test_finds_one_contradiction(self):
        records = [
            MemoryRecord(type=MemoryType.BELIEF, content="这个项目使用 Python", raw_text="这个项目使用 Python"),
            MemoryRecord(type=MemoryType.BELIEF, content="这个项目不使用 Python", raw_text="这个项目不使用 Python"),
            MemoryRecord(type=MemoryType.BELIEF, content="JavaScript 也很流行", raw_text="JavaScript 也很流行"),
        ]
        
        contradictions = find_contradictions(records)
        assert len(contradictions) == 1  # 只有前两条矛盾
    
    def test_no_contradictions(self):
        records = [
            MemoryRecord(type=MemoryType.BELIEF, content="Python 是最好的语言", raw_text="Python 是最好的语言"),
            MemoryRecord(type=MemoryType.BELIEF, content="JavaScript 也很流行", raw_text="JavaScript 也很流行"),
        ]
        
        contradictions = find_contradictions(records)
        assert len(contradictions) == 0


class TestApplyContradictionPenalty:
    """矛盾惩罚"""
    
    def test_penalty_reduces_importance(self):
        """检测到矛盾后降低 importance"""
        a = MemoryRecord(type=MemoryType.BELIEF, content="这个项目使用 Python", raw_text="这个项目使用 Python", importance=0.8)
        b = MemoryRecord(type=MemoryType.BELIEF, content="这个项目不使用 Python", raw_text="这个项目不使用 Python", importance=0.8)
        
        updated_a, updated_b = apply_contradiction_penalty(a, b)
        
        assert updated_a.importance < 0.8
        assert updated_b.importance < 0.8
        assert updated_a.metadata.get("contradiction_penalty") is True
    
    def test_no_penalty_when_no_contradiction(self):
        """无矛盾时不降低 importance"""
        a = MemoryRecord(type=MemoryType.BELIEF, content="Python 是最好的语言", raw_text="Python 是最好的语言", importance=0.8)
        b = MemoryRecord(type=MemoryType.BELIEF, content="JavaScript 也很流行", raw_text="JavaScript 也很流行", importance=0.8)
        
        updated_a, updated_b = apply_contradiction_penalty(a, b)
        
        assert updated_a.importance == 0.8
        assert updated_b.importance == 0.8


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
