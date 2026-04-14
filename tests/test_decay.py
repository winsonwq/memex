"""
Decay & Forgetting 单元测试
"""
import pytest
import time
import sys
sys.path.insert(0, 'src')

from memex._decay import (
    calc_decay_score,
    should_archive,
    archive_record,
    find_records_to_archive,
    DECAY_THRESHOLD,
    ARCHIVED_IMPORTANCE,
)
from memex._types import MemoryRecord, MemoryType


class TestCalcDecayScore:
    """Decay 分数计算"""
    
    def test_new_record_low_decay(self):
        """刚创建且访问过的记录 decay 很低"""
        now_ms = int(time.time() * 1000)
        score = calc_decay_score(
            last_accessed=now_ms,
            access_count=10,
            importance=0.7,
            created_at=now_ms,
        )
        assert score < 0.3
    
    def test_old_unaccessed_record_high_decay(self):
        """久未访问的老记录 decay 很高"""
        old_time = int((time.time() - 180 * 24 * 3600) * 1000)  # 180 天前
        score = calc_decay_score(
            last_accessed=old_time,
            access_count=1,
            importance=0.7,
            created_at=old_time,
        )
        # 180 天老记录 + 很少访问 → 高 decay
        assert score > DECAY_THRESHOLD


class TestShouldArchive:
    """归档判断"""
    
    def test_constraint_never_archived(self):
        """CONSTRAINT 类型永不归档"""
        old_time = int((time.time() - 365 * 24 * 3600) * 1000)
        record = MemoryRecord(
            type=MemoryType.CONSTRAINT,
            content="必须使用 Python",
            raw_text="必须使用 Python",
            created_at=old_time,
            last_accessed=old_time,
        )
        # 即使很老也不归档
        assert should_archive(record) is False
    
    def test_user_model_never_archived(self):
        """USER_MODEL 类型永不归档"""
        old_time = int((time.time() - 365 * 24 * 3600) * 1000)
        record = MemoryRecord(
            type=MemoryType.USER_MODEL,
            content="用户喜欢简洁回复",
            raw_text="用户喜欢简洁回复",
            created_at=old_time,
            last_accessed=old_time,
        )
        assert should_archive(record) is False
    
    def test_old_belief_should_archive(self):
        """旧的 BELIEF 应该归档"""
        old_time = int((time.time() - 200 * 24 * 3600) * 1000)  # 200 天前
        record = MemoryRecord(
            type=MemoryType.BELIEF,
            content="这个项目用 Python",
            raw_text="这个项目用 Python",
            created_at=old_time,
            last_accessed=old_time,
        )
        assert should_archive(record) is True


class TestArchiveRecord:
    """归档操作"""
    
    def test_archived_importance(self):
        """归档后 importance = 0.05"""
        record = MemoryRecord(
            type=MemoryType.BELIEF,
            content="测试内容",
            raw_text="测试内容",
            importance=0.8,
        )
        archived = archive_record(record)
        
        assert archived.importance == ARCHIVED_IMPORTANCE
        assert archived.metadata.get("archived") is True
        assert "archived_at" in archived.metadata


class TestFindRecordsToArchive:
    """批量查找待归档记录"""
    
    def test_finds_old_beliefs(self):
        """找出需要归档的 BELIEF"""
        old_time = int((time.time() - 200 * 24 * 3600) * 1000)
        
        records = [
            MemoryRecord(
                type=MemoryType.BELIEF,
                content="很老的 belief",
                raw_text="很老的 belief",
                created_at=old_time,
                last_accessed=old_time,
            ),
            MemoryRecord(
                type=MemoryType.CONSTRAINT,
                content="约束，不归档",
                raw_text="约束，不归档",
                created_at=old_time,
                last_accessed=old_time,
            ),
        ]
        
        candidates = find_records_to_archive(records)
        assert len(candidates) == 1
        assert candidates[0][0].type == MemoryType.BELIEF
    
    def test_sorted_by_decay_descending(self):
        """结果按 decay 降序"""
        very_old = int((time.time() - 365 * 24 * 3600) * 1000)
        somewhat_old = int((time.time() - 100 * 24 * 3600) * 1000)
        
        records = [
            MemoryRecord(
                type=MemoryType.BELIEF,
                content="有点老",
                raw_text="有点老",
                created_at=somewhat_old,
                last_accessed=somewhat_old,
            ),
            MemoryRecord(
                type=MemoryType.BELIEF,
                content="很老",
                raw_text="很老",
                created_at=very_old,
                last_accessed=very_old,
            ),
        ]
        
        candidates = find_records_to_archive(records)
        assert len(candidates) == 2
        # 更老的应该排在前面
        assert candidates[0][1] >= candidates[1][1]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
