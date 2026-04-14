"""
Phase 1 测试 — 向量搜索集成
"""
import os
import tempfile
from pathlib import Path

import pytest

from memory_palace.src.core.models import MemoryEntry
from memory_palace.src.core.store import MemoryStore
from memory_palace.src.palace.structure import Palace


class TestPhase1VectorSearch:
    """Phase 1: 向量搜索测试"""
    
    @pytest.fixture
    def temp_dir(self):
        """临时目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def store(self, temp_dir):
        """SQLite 存储"""
        db_path = os.path.join(temp_dir, "memory.db")
        return MemoryStore(db_path=db_path)
    
    @pytest.fixture
    def palace(self, store):
        """Palace（无向量索引，降级测试）"""
        return Palace(store=store, vector_index=None)
    
    def test_memory_entry_creation(self, palace):
        """测试记忆创建"""
        entry = palace.add_memory(
            content="用户喜欢简洁的回复风格，不喜欢废话",
            wing="user",
            room="preferences",
            hall="preferences",
            source="manual",
        )
        
        assert entry.id is not None
        assert entry.content == "用户喜欢简洁的回复风格，不喜欢废话"
        assert entry.wing == "user"
        assert entry.room == "preferences"
        assert entry.hall == "preferences"
    
    def test_wing_creation(self, palace):
        """测试 Wing 创建"""
        wing = palace.create_wing(
            name="openswarm",
            wing_type="project",
            description="OpenSwarm 多智能体系统",
        )
        
        assert wing.id is not None
        assert wing.name == "openswarm"
        assert wing.wing_type == "project"
    
    def test_room_memories(self, palace):
        """测试 Room 记忆查询"""
        # 添加两条记忆
        palace.add_memory(
            content="今天讨论了项目架构",
            wing="openswarm",
            room="architecture",
            source="session",
        )
        palace.add_memory(
            content="决定使用事件驱动架构",
            wing="openswarm",
            room="architecture",
            source="session",
        )
        
        memories = palace.get_room_memories("openswarm", "architecture")
        
        assert len(memories) == 2
        assert all(m.wing == "openswarm" for m in memories)
        assert all(m.room == "architecture" for m in memories)
    
    def test_search_no_query_sql(self, palace):
        """测试 SQL 搜索（无 query）"""
        palace.add_memory(
            content="这是一个关于 Python 项目的记忆",
            wing="user",
            room="projects",
            source="manual",
        )
        palace.add_memory(
            content="这是一个关于 Rust 项目的记忆",
            wing="user",
            room="projects",
            source="manual",
        )
        
        # 无 query → SQL 精确匹配
        results = palace.search_memories(
            query="",
            wing="user",
            room="projects",
        )
        
        assert len(results) == 2
    
    def test_search_with_query_sql_like(self, palace):
        """测试 SQL LIKE 搜索（降级方案）"""
        palace.add_memory(
            content="Python 是一种解释型语言",
            wing="user",
            room="languages",
            source="manual",
        )
        palace.add_memory(
            content="Rust 是一种系统编程语言",
            wing="user",
            room="languages",
            source="manual",
        )
        
        # 有 query，但无向量索引 → SQL LIKE
        results = palace.search_memories(
            query="Python",
            wing="user",
            room="languages",
        )
        
        assert len(results) == 1
        assert "Python" in results[0].content


# 向量搜索测试（需要 OpenAI API Key）
class TestPhase1VectorSearchWithLanceDB:
    """Phase 1: LanceDB 向量搜索测试（需要 API Key）"""
    
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def store(self, temp_dir):
        db_path = os.path.join(temp_dir, "memory.db")
        return MemoryStore(db_path=db_path)
    
    @pytest.mark.skipif(
        not os.environ.get("OPENAI_API_KEY"),
        reason="需要 OPENAI_API_KEY",
    )
    def test_vector_search(self, store, temp_dir):
        """测试向量语义搜索"""
        from memory_palace.src.search.vector_index import VectorIndex
        
        vector_path = os.path.join(temp_dir, "vectors")
        vector_index = VectorIndex(
            db_path=vector_path,
            embed_model="openai",
        )
        
        palace = Palace(store=store, vector_index=vector_index)
        
        # 添加记忆
        palace.add_memory(
            content="我喜欢在周末去爬山，呼吸新鲜空气",
            wing="user",
            room="hobbies",
            hall="preferences",
        )
        palace.add_memory(
            content="最近在学习 Rust 编程语言",
            wing="user",
            room="learning",
            hall="discoveries",
        )
        
        # 向量搜索
        results = palace.search_memories(
            query="户外运动",
            wing="user",
            limit=5,
        )
        
        # 应该找到关于爬山的内容
        assert len(results) >= 1
        assert any("爬山" in r.content for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
