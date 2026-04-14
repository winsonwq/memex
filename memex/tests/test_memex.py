"""
Memex 基本测试
"""
import pytest

from memex._types import MemoryRecord, MemoryType, DEFAULT_IMPORTANCE
from memex.store.memory import MemoryStore


class TestMemoryStore:
    """Memory Store 测试"""
    
    @pytest.fixture
    def store(self):
        return MemoryStore()
    
    @pytest.fixture
    def sample_record(self):
        return MemoryRecord(
            type=MemoryType.BELIEF,
            content="用户喜欢简洁的回复",
            raw_text="用户喜欢简洁的回复",
            importance=0.8,
            repo="test",
        )
    
    def test_add_and_get(self, store, sample_record):
        """测试添加和获取"""
        vector = [0.1] * 768
        store.add(sample_record, vector)
        
        retrieved = store.get(sample_record.id)
        
        assert retrieved is not None
        assert retrieved.content == sample_record.content
        assert retrieved.type == MemoryType.BELIEF
    
    def test_list(self, store, sample_record):
        """测试列表"""
        store.add(sample_record, [0.1] * 768)
        
        records = store.list(repo="test")
        
        assert len(records) == 1
        assert records[0].id == sample_record.id
    
    def test_list_by_type(self, store, sample_record):
        """测试按类型过滤"""
        store.add(sample_record, [0.1] * 768)
        
        # 添加另一个类型
        record2 = MemoryRecord(
            type=MemoryType.STRATEGY,
            content="另一个记忆",
            raw_text="另一个记忆",
            repo="test",
        )
        store.add(record2, [0.2] * 768)
        
        beliefs = store.list(repo="test", type="belief")
        strategies = store.list(repo="test", type="strategy")
        
        assert len(beliefs) == 1
        assert len(strategies) == 1
        assert beliefs[0].type == MemoryType.BELIEF
    
    def test_delete(self, store, sample_record):
        """测试删除"""
        store.add(sample_record, [0.1] * 768)
        
        store.delete(sample_record.id)
        
        assert store.get(sample_record.id) is None
        assert store.count(repo="test") == 0
    
    def test_count(self, store, sample_record):
        """测试计数"""
        assert store.count(repo="test") == 0
        
        store.add(sample_record, [0.1] * 768)
        
        assert store.count(repo="test") == 1
    
    def test_search(self, store, sample_record):
        """测试向量搜索"""
        store.add(sample_record, [0.1] * 768)
        
        results = store.search([0.1] * 768, repo="test")
        
        assert len(results) == 1
        assert results[0][0].id == sample_record.id
    
    def test_search_by_content(self, store, sample_record):
        """测试内容搜索"""
        store.add(sample_record, [0.1] * 768)
        
        results = store.search_by_content("简洁", repo="test")
        
        assert len(results) == 1


class TestMemoryRecord:
    """MemoryRecord 测试"""
    
    def test_to_dict(self):
        """测试序列化"""
        record = MemoryRecord(
            type=MemoryType.USER_MODEL,
            content="测试内容",
            raw_text="原始文本",
            importance=0.85,
            repo="default",
        )
        
        data = record.to_dict()
        
        assert data["type"] == "user_model"
        assert data["content"] == "测试内容"
        assert data["importance"] == 0.85
        assert data["id"] is not None
    
    def test_from_dict(self):
        """测试反序列化"""
        data = {
            "id": "test-id",
            "type": "constraint",
            "content": "约束内容",
            "raw_text": "原始",
            "importance": 0.9,
            "confidence": 0.8,
            "stability": "high",
            "revision_count": 0,
            "contradicts": [],
            "supports": [],
            "derived_from": "",
            "created_at": 1234567890,
            "last_updated": 1234567890,
            "last_accessed": 1234567890,
            "expires_at": 9999999999999,
            "repo": "default",
            "title": "",
            "metadata": {},
            "trust": 1.0,
        }
        
        record = MemoryRecord.from_dict(data)
        
        assert record.type == MemoryType.CONSTRAINT
        assert record.content == "约束内容"
        assert record.importance == 0.9
    
    def test_default_importance(self):
        """测试默认 importance"""
        for mtype, expected in DEFAULT_IMPORTANCE.items():
            assert 0 <= expected <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
