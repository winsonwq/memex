"""
Memory Revision 单元测试
"""
import pytest
import sys
sys.path.insert(0, 'src')

from memex._types import MemoryRecord, MemoryType
from memex._revision import (
    increase_stability,
    decrease_stability,
    revise_belief,
    detect_contradiction,
    RevisionResult,
)


class TestStabilityTransitions:
    """稳定性状态转换"""
    
    def test_increase_low_to_medium(self):
        assert increase_stability("low") == "medium"
    
    def test_increase_medium_to_high(self):
        assert increase_stability("medium") == "high"
    
    def test_increase_high_stays_high(self):
        assert increase_stability("high") == "high"
    
    def test_decrease_high_to_medium(self):
        assert decrease_stability("high") == "medium"
    
    def test_decrease_medium_to_low(self):
        assert decrease_stability("medium") == "low"
    
    def test_decrease_low_stays_low(self):
        assert decrease_stability("low") == "low"


class TestReviseBelief:
    """修订 BELIEF 记忆"""
    
    def _make_belief(self, stability="medium"):
        return MemoryRecord(
            type=MemoryType.BELIEF,
            content="Python 是最好的语言",
            raw_text="Python 是最好的语言",
            stability=stability,
            revision_count=0,
        )
    
    def test_confirm_low_belief(self):
        """确认证据提升 low → medium"""
        belief = self._make_belief("low")
        result = revise_belief(belief, "有人也这么认为", confirms=True)
        
        assert result.changed is True
        assert result.action == "confirmed"
        assert result.new_stability == "medium"
        assert result.record.stability == "medium"
        assert result.record.revision_count == 1
    
    def test_confirm_medium_belief(self):
        """确认证据提升 medium → high"""
        belief = self._make_belief("medium")
        result = revise_belief(belief, "更多证据支持", confirms=True)
        
        assert result.changed is True
        assert result.new_stability == "high"
    
    def test_confirm_high_belief(self):
        """确认证据 high → high（不变）"""
        belief = self._make_belief("high")
        result = revise_belief(belief, "更多证据支持", confirms=True)
        
        assert result.changed is False
        assert result.action == "unchanged"
    
    def test_weaken_high_belief(self):
        """矛盾证据降低 high → medium"""
        belief = self._make_belief("high")
        result = revise_belief(belief, "有人反对这个观点", confirms=False)
        
        assert result.changed is True
        assert result.action == "weakened"
        assert result.new_stability == "medium"
    
    def test_weaken_low_belief(self):
        """矛盾证据 low → low（不变）"""
        belief = self._make_belief("low")
        result = revise_belief(belief, "有证据反对", confirms=False)
        
        assert result.changed is False
        assert result.action == "unchanged"
    
    def test_non_belief_not_revised(self):
        """非 BELIEF 类型不修订"""
        record = MemoryRecord(
            type=MemoryType.CONSTRAINT,
            content="必须使用 Python",
            raw_text="必须使用 Python",
        )
        result = revise_belief(record, "新证据", confirms=True)
        
        assert result.changed is False
        assert result.action == "not_belief"


class TestContradictionDetection:
    """矛盾检测"""
    
    def test_detect_negation_contradiction(self):
        """检测否定式矛盾"""
        belief = MemoryRecord(
            type=MemoryType.BELIEF,
            content="这个项目使用 Python",
            raw_text="这个项目使用 Python",
        )
        
        assert detect_contradiction(belief, "不，这个项目不用 Python") is True
    
    def test_no_contradiction_different_topic(self):
        """不同话题不矛盾"""
        belief = MemoryRecord(
            type=MemoryType.BELIEF,
            content="Python 是最好的语言",
            raw_text="Python 是最好的语言",
        )
        
        assert detect_contradiction(belief, "JavaScript 也很好") is False
    
    def test_no_contradiction_same_negation(self):
        """原内容是否定，新内容也否定 → 不矛盾"""
        belief = MemoryRecord(
            type=MemoryType.BELIEF,
            content="这个项目不使用 Java",
            raw_text="这个项目不使用 Java",
        )
        
        assert detect_contradiction(belief, "对，确实不用 Java") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
