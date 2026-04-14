"""
Memory Revision — 记忆修订

当新的证据出现时，更新已有记忆的状态。
不是 append-only，而是支持对 belief 的修订。

稳定性状态机：
  low ←→ medium ←→ high

修订规则：
- 新证据确认 → stability 提升
- 新证据矛盾 → stability 降低
- revision_count 每次修订递增
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from ._types import MemoryRecord, MemoryType


class StabilityLevel(Enum):
    """稳定性级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# 稳定性升级/降级映射
STABILITY_ORDER = [StabilityLevel.LOW, StabilityLevel.MEDIUM, StabilityLevel.HIGH]

STABILITY_INDEX = {s: i for i, s in enumerate(STABILITY_ORDER)}


def increase_stability(current: str) -> str:
    """提升稳定性"""
    level = StabilityLevel(current)
    idx = STABILITY_INDEX[level]
    if idx < len(STABILITY_ORDER) - 1:
        return STABILITY_ORDER[idx + 1].value
    return current  # 已经是最高


def decrease_stability(current: str) -> str:
    """降低稳定性"""
    level = StabilityLevel(current)
    idx = STABILITY_INDEX[level]
    if idx > 0:
        return STABILITY_ORDER[idx - 1].value
    return current  # 已经是最低


@dataclass
class RevisionResult:
    """修订结果"""
    record: MemoryRecord
    changed: bool        # 是否有变化
    action: str          # 修订动作：confirmed / weakened / unchanged
    new_stability: str   # 新的稳定性


def revise_belief(
    record: MemoryRecord,
    evidence: str,
    confirms: bool,
) -> RevisionResult:
    """
    修订一条记忆
    
    Args:
        record: 要修订的记忆
        evidence: 新证据文本
        confirms: 新证据是否支持该记忆
        
    Returns:
        RevisionResult: 包含修订后的记录和动作描述
    """
    if record.type != MemoryType.BELIEF:
        # 非 BELIEF 类型不修订
        return RevisionResult(
            record=record,
            changed=False,
            action="not_belief",
            new_stability=record.stability,
        )
    
    old_stability = record.stability
    
    if confirms:
        new_stability = increase_stability(old_stability)
        action = "confirmed"
    else:
        new_stability = decrease_stability(old_stability)
        action = "weakened"
    
    # 如果没有变化，不需要更新
    if new_stability == old_stability:
        return RevisionResult(
            record=record,
            changed=False,
            action="unchanged",
            new_stability=old_stability,
        )
    
    # 创建修订后的副本
    updated = MemoryRecord.from_dict(record.to_dict())
    updated.stability = new_stability
    updated.revision_count = updated.revision_count + 1
    updated.last_updated = int(__import__("time").time() * 1000)
    updated.content = f"[修订版 {updated.revision_count}] {updated.content}"
    # 保留原始内容在 raw_text
    updated.metadata["revision_evidence"] = evidence
    updated.metadata["last_revision_action"] = action
    
    return RevisionResult(
        record=updated,
        changed=True,
        action=action,
        new_stability=new_stability,
    )


def detect_contradiction(record: MemoryRecord, new_text: str) -> bool:
    """
    检测新文本是否与已有记忆矛盾
    
    简单的关键词检测：检测否定模式
    """
    import re
    
    def simple_tokenize(text: str) -> set[str]:
        """简单的 tokenize，返回字符集合（对中文）和单词集合（对英文）"""
        text_lower = text.lower()
        # 提取英文字母序列和单个中文字符
        english_words = re.findall(r'[a-z]+', text_lower)
        chinese_chars = list(text_lower)  # 中文按字符分
        return set(english_words) | set(chinese_chars)
    
    record_tokens = simple_tokenize(record.content)
    new_tokens = simple_tokenize(new_text)
    
    # 否定词
    negation_words = {"不", "否", "无", "非", "no", "not", "never", "don't", "doesn't", "didn't", "cant", "cannot"}
    
    # 检测原内容是否有否定（英文字符串级别）
    english_negation = {"no", "not", "never", "dont", "doesnt", "didnt", "cant", "cannot"}
    record_has_en_neg = bool(english_negation & record_tokens)
    new_has_en_neg = bool(english_negation & new_tokens)
    
    # 检测中文否定
    record_has_cn_neg = "不" in record_tokens or "否" in record_tokens
    new_has_cn_neg = "不" in new_tokens or "否" in new_tokens
    
    # 如果原内容无否定，新内容有否定
    if (not record_has_en_neg and not record_has_cn_neg) and (new_has_en_neg or new_has_cn_neg):
        # 检查关键词重叠（中英文都算）
        # 英文字符序列 + 中文字符
        # 移除常见停用词
        stop_words = {"的", "是", "在", "有", "了", "和", "与", "the", "a", "an", "is", "are", "was", "were"}
        record_key = record_tokens - stop_words
        new_key = new_tokens - stop_words
        # 检查共同词（英文单词或中文字符）
        if record_key & new_key:
            return True
    
    return False
