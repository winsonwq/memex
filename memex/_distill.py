"""
Distillation - 语义蒸馏

存入记忆前先过滤内容,只保留有价值的 insight。

拒绝模式(匹配则不存储):
- 闲聊/问候
- 短暂情绪
- 纯确认/简单回复

提取模式(匹配则按类型存储):
- CONSTRAINT: 约束/禁令
- USER_MODEL: 用户偏好
- STRATEGY: 策略/方法论
- SYSTEM_PATTERN: 系统模式
- BELIEF: 验证结论
"""

from dataclasses import dataclass
from typing import Optional

from ._types import MemoryType


@dataclass
class DistillResult:
    """蒸馏结果"""
    should_store: bool       # 是否值得存储
    reason: str            # 原因
    content: str           # 蒸馏后的内容
    memory_type: MemoryType # 建议的记忆类型


# =============================================================================
# 拒绝模式
# =============================================================================

# 闲聊/问候关键词
GREETING_WORDS = {
    "hi", "hello", "hey", "greetings", "howdy",
    "你好", "您好", "早上好", "下午好", "晚上好",
    "안녕", "오", "viva", "hola", "ciao", "oi",
    "what's up", "sup",
}

# 短暂情绪关键词
EMOTION_WORDS = {
    "i love", "i hate", "i like", "i dislike",
    "lol", "lmao", "rofl", "haha", "hehe",
    "great", "awesome", "terrible", "awful",
    "좋아", "싫어", "화나", "슬퍼",
    # 中文情绪（简短表达）
    "好开心", "好高兴", "好难过", "好害怕",
    "太气人", "太棒了", "太好了", "太糟了",
    "气死了", "开心", "难过", "害怕", "生气",
}

# 确认/简短回复关键词
CONFIRM_WORDS = {
    "ok", "okay", "yep", "yeah", "yes", "no", "nope", "sure",
    "got it", "明白", "好的", "收到", "了解", "嗯", "네",
    "nice", "cool", "perfect", "sounds good",
}

# 依赖上下文的提问关键词
CONTEXTUAL_WORDS = {
    "帮我记住", "帮我存", "note this", "remember this", "save this",
    "怎么选择", "哪个更好", "帮我选", "memo", "write this down",
}


# =============================================================================
# 提取模式
# =============================================================================

# CONSTRAINT 关键词
CONSTRAINT_WORDS = {
    "必须", "一定", "千万", "禁止", "不得", "不许", "不要",
    "mustr", "never", "always must", "must not", "no way",
    "wajib", "harus", "not allowed", "forbidden",
}

# USER_MODEL 关键词
USER_MODEL_WORDS = {
    "喜欢", "偏好", "倾向于", "讨厌", "不爱", "不想",
    "prefer", "hate", "dislike", "doesn't like",
    "usually", "习惯", "always use", "never use",
}

# STRATEGY 关键词
STRATEGY_WORDS = {
    "策略", "方法", "做法", "思路", "窍门",
    "strategy", "approach", "method", "how to",
    "best practice", "recommended", "建议", "推荐", "ordinarily", "typically",
    "方法论", "分治", "递归",
}

# SYSTEM_PATTERN 关键词
SYSTEM_PATTERN_WORDS = {
    "系统", "架构", "设计模式", "结构", "堆栈",
    "architecture", "stack", "using", "built with",
    "项目", "代码", "仓库", "repo", "directory", "folder",
    "前端", "后端", "微服务", "monolith",
}

# BELIEF 关键词
BELIEF_WORDS = {
    "发现", "结论", "原来", "其实", "事实证明",
    "learned", "found", "discovered", "conclusion",
    "实践证明", "effective", "better", "faster", "slower", "works",
    "更好用", "更快", "更有效", "更简单",
}


def distill(text: str) -> DistillResult:
    """
    对输入文本进行语义蒸馏,判断是否值得存储。

    策略:
    1. 短文本(<3词)先快速检查确认类
    2. 中长文本进行分类检查
    3. 不确定时倾向于存储(False Negative 优于 False Positive)
    """
    if not text:
        return DistillResult(
            should_store=False,
            reason="empty",
            content=text,
            memory_type=MemoryType.BELIEF,
        )

    text = text.strip()
    text_lower = text.lower()
    words = text_lower.split()

    # 1. 检查拒绝模式(不看长度)
    # CONTEXTUAL 要在最前面,因为最具体
    for w in CONTEXTUAL_WORDS:
        if w in text_lower:
            return DistillResult(
                should_store=False,
                reason="contextual_question",
                content=text,
                memory_type=MemoryType.BELIEF,
            )

    for w in GREETING_WORDS:
        if text_lower.strip() == w or text_lower.startswith(w + " "):
            return DistillResult(
                should_store=False,
                reason="greeting",
                content=text,
                memory_type=MemoryType.BELIEF,
            )

    for w in EMOTION_WORDS:
        if w in text_lower:
            return DistillResult(
                should_store=False,
                reason="emotion",
                content=text,
                memory_type=MemoryType.BELIEF,
            )

    for w in CONFIRM_WORDS:
        # 确认词匹配,但内容长的话可能是详细解释
        if text_lower.strip() == w or text_lower.strip().startswith(w + " "):
            if len(text) < 50:
                return DistillResult(
                    should_store=False,
                    reason="confirmation",
                    content=text,
                    memory_type=MemoryType.BELIEF,
                )

    # 2. 尝试提取类型(按优先级)
    # CONSTRAINT 要在 USER_MODEL 之前,因为 "never/always/mustr" 更明确
    for w in CONSTRAINT_WORDS:
        if w in text_lower:
            return DistillResult(
                should_store=True,
                reason="extracted_constraint",
                content=text,
                memory_type=MemoryType.CONSTRAINT,
            )

    for w in USER_MODEL_WORDS:
        if w in text_lower:
            return DistillResult(
                should_store=True,
                reason="extracted_user_model",
                content=text,
                memory_type=MemoryType.USER_MODEL,
            )

    for w in STRATEGY_WORDS:
        if w in text_lower:
            return DistillResult(
                should_store=True,
                reason="extracted_strategy",
                content=text,
                memory_type=MemoryType.STRATEGY,
            )

    for w in SYSTEM_PATTERN_WORDS:
        if w in text_lower:
            return DistillResult(
                should_store=True,
                reason="extracted_system_pattern",
                content=text,
                memory_type=MemoryType.SYSTEM_PATTERN,
            )

    for w in BELIEF_WORDS:
        if w in text_lower:
            return DistillResult(
                should_store=True,
                reason="extracted_belief",
                content=text,
                memory_type=MemoryType.BELIEF,
            )

    # 3. 默认:BELIEF(通用陈述)
    # 过短且无关键词才拒绝(中文用字符数,英文用词数)
    is_cjk = ord(text[0]) > 0x3000 if text else False
    if is_cjk:
        # 中文：字符数 < 10 才拒绝
        if len(text) < 10:
            return DistillResult(
                should_store=False,
                reason="too_short_unclassified",
                content=text,
                memory_type=MemoryType.BELIEF,
            )
    else:
        # 英文:词数 <= 2 才拒绝
        if len(words) <= 2:
            return DistillResult(
                should_store=False,
                reason="too_short_unclassified",
                content=text,
                memory_type=MemoryType.BELIEF,
            )

    return DistillResult(
        should_store=True,
        reason="default_belief",
        content=text,
        memory_type=MemoryType.BELIEF,
    )
