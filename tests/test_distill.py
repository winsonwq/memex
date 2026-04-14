"""
Distillation 单元测试

蒸馏逻辑：
- 短文本（<3词）+ 无关键词 → 拒绝
- 闲聊/情绪/确认词 → 拒绝
- 有类型关键词 → 按类型存储
- 普通陈述（≥3词）→ 默认 BELIEF 存储
"""

import pytest
import sys
sys.path.insert(0, 'src')

from memex._distill import distill
from memex._types import MemoryType


class TestRejectGreetings:
    """闲聊/问候 → 拒绝"""
    
    @pytest.mark.parametrize("text", [
        "hi", "hello", "hey",
        "你好", "您好",
        "안녕", "hola",
    ])
    def test_reject_greeting(self, text):
        result = distill(text)
        assert result.should_store is False
        assert result.reason == "greeting"


class TestRejectEmotions:
    """短暂情绪 → 拒绝"""
    
    @pytest.mark.parametrize("text", [
        "I hate it", "太气人了",
        "lol", "haha",
    ])
    def test_reject_emotion(self, text):
        result = distill(text)
        assert result.should_store is False
        assert result.reason == "emotion"


class TestRejectConfirmations:
    """确认/简短回复（<50字）→ 拒绝"""
    
    @pytest.mark.parametrize("text", [
        "ok", "okay", "yep", "好的",
        "got it", "nice", "cool",
    ])
    def test_reject_confirmation(self, text):
        result = distill(text)
        assert result.should_store is False
        assert result.reason == "confirmation"


class TestRejectContextual:
    """依赖上下文的提问 → 拒绝"""
    
    @pytest.mark.parametrize("text", [
        "帮我记住这个", "note this please",
        "怎么选择？", "哪个更好？",
    ])
    def test_reject_contextual(self, text):
        result = distill(text)
        assert result.should_store is False
        assert result.reason == "contextual_question"


class TestRejectTooShort:
    """太短且无关键词 → 拒绝"""
    
    @pytest.mark.parametrize("text", [
        "hi", "ok", "yes", "no",
    ])
    def test_reject_short(self, text):
        result = distill(text)
        assert result.should_store is False


class TestExtractConstraint:
    """约束/禁令 → CONSTRAINT"""
    
    @pytest.mark.parametrize("text", [
        "必须使用 Python 3.10+",
        "禁止使用 eval 函数",
        "NEVER use global state",
    ])
    def test_extract_constraint(self, text):
        result = distill(text)
        assert result.should_store is True
        assert result.memory_type == MemoryType.CONSTRAINT


class TestExtractUserModel:
    """用户偏好 → USER_MODEL"""
    
    @pytest.mark.parametrize("text", [
        "用户喜欢简洁的回复风格",
        "I prefer TypeScript over JavaScript",
        "她讨厌啰嗦的解释方式",
    ])
    def test_extract_user_model(self, text):
        result = distill(text)
        assert result.should_store is True
        assert result.memory_type == MemoryType.USER_MODEL


class TestExtractStrategy:
    """策略/方法论 → STRATEGY"""
    
    @pytest.mark.parametrize("text", [
        "推荐使用分治法解决复杂问题",
        "方法论：先测后写",
    ])
    def test_extract_strategy(self, text):
        result = distill(text)
        assert result.should_store is True
        assert result.memory_type == MemoryType.STRATEGY


class TestExtractSystemPattern:
    """系统/架构模式 → SYSTEM_PATTERN"""
    
    @pytest.mark.parametrize("text", [
        "项目采用前后端分离架构设计",
        "这个系统用 Python + FastAPI 构建",
        "使用了 React + TypeScript 作为前端",
    ])
    def test_extract_system_pattern(self, text):
        result = distill(text)
        assert result.should_store is True
        assert result.memory_type == MemoryType.SYSTEM_PATTERN


class TestExtractBelief:
    """验证结论/发现 → BELIEF"""
    
    @pytest.mark.parametrize("text", [
        "发现 TypeScript 比 JavaScript 更好用",
        "原来这个问题需要重启服务才能解决",
        "FastAPI 的性能比 Flask 快很多",
    ])
    def test_extract_belief(self, text):
        result = distill(text)
        assert result.should_store is True
        assert result.memory_type == MemoryType.BELIEF


class TestDefaultBelief:
    """普通陈述 → 默认 BELIEF"""
    
    @pytest.mark.parametrize("text", [
        "用户今天完成了登录模块的开发工作",
        "这个接口需要认证才能访问",
        "数据库连接使用了连接池",
        "部署脚本已经写好了测试用例",
    ])
    def test_default_belief(self, text):
        result = distill(text)
        assert result.should_store is True
        assert result.memory_type == MemoryType.BELIEF


class TestEdgeCases:
    """边界情况"""
    
    def test_empty_string(self):
        result = distill("")
        assert result.should_store is False
    
    def test_whitespace_only(self):
        result = distill("   ")
        assert result.should_store is False
    
    def test_none(self):
        result = distill(None)
        assert result.should_store is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
