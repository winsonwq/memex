"""
Contradiction Detection — 矛盾检测

检测两条记忆之间的语义矛盾。
当检测到矛盾时，降低双方的 importance。

矛盾模式：
1. 否定模式：A 说"X 是 Y"，B 说"X 不是 Y"
2. 行为冲突模式：A 说"做 X"，B 说"不做 X"
"""

from dataclasses import dataclass
from typing import Optional, List, Tuple

from ._types import MemoryRecord


@dataclass
class ContradictionResult:
    """矛盾检测结果"""
    has_contradiction: bool
    confidence: float           # 0-1，矛盾置信度
    pattern: str               # 矛盾模式
    details: str               # 详细描述


def detect_record_pair_contradiction(
    record_a: MemoryRecord,
    record_b: MemoryRecord,
) -> ContradictionResult:
    """
    检测两条记忆之间的矛盾
    
    Returns:
        ContradictionResult
    """
    content_a = record_a.content.lower()
    content_b = record_b.content.lower()
    
    # 1. 检测否定模式
    pattern = _detect_negation_pattern(content_a, content_b)
    if pattern:
        return ContradictionResult(
            has_contradiction=True,
            confidence=0.8,
            pattern="negation",
            details=pattern,
        )
    
    # 2. 检测行为冲突（做 vs 不做）
    pattern = _detect_action_pattern(content_a, content_b)
    if pattern:
        return ContradictionResult(
            has_contradiction=True,
            confidence=0.7,
            pattern="action_conflict",
            details=pattern,
        )
    
    return ContradictionResult(
        has_contradiction=False,
        confidence=0.0,
        pattern="none",
        details="",
    )


def _detect_negation_pattern(a: str, b: str) -> Optional[str]:
    """检测否定模式矛盾"""
    import re
    
    # 英文单词集合
    def get_english_words(text: str) -> set:
        return set(re.findall(r'[a-z]+', text))
    
    english_words_a = get_english_words(a)
    english_words_b = get_english_words(b)
    
    # 英文否定词
    en_neg = {"no", "not", "never", "dont", "doesnt", "cant", "shouldnt", "wont", "noone"}
    
    # 检测英文否定
    a_has_en_neg = bool(en_neg & english_words_a)
    b_has_en_neg = bool(en_neg & english_words_b)
    
    # 检测中文否定（直接搜索否定词）
    def has_cn_negation(text: str) -> bool:
        cn_negations = [
            "不用", "不是", "不支持", "不可以", "不应", "不推荐", "不建议", "不愿意",
            "不使用", "不应该", "不建议", "不鼓励", "不允许",
        ]
        return any(neg in text for neg in cn_negations)
    
    a_has_cn_neg = has_cn_negation(a)
    b_has_cn_neg = has_cn_negation(b)
    
    # 英文肯定词
    en_pos = {"use", "uses", "is", "are", "was", "were", "do", "does", "can", "should", "recommend", "like"}
    
    # 检测英文矛盾：A 无否定，B 有否定，且有共同肯定词
    if not a_has_en_neg and b_has_en_neg:
        common = en_pos & english_words_a & english_words_b
        if common:
            return f"A 说\"{a[:50]}\"，B 说\"{b[:50]}\"（英文否定矛盾）"
    if not b_has_en_neg and a_has_en_neg:
        common = en_pos & english_words_a & english_words_b
        if common:
            return f"A 说\"{a[:50]}\"，B 说\"{b[:50]}\"（英文否定矛盾）"
    
    # 检测中文矛盾：当一方有否定词时，必须有共同关键词
    def has_shared_content(text_a: str, text_b: str) -> bool:
        """检查两句话是否有共同的内容词（排除停用词）"""
        stop_words = {"的", "是", "在", "有", "了", "和", "与", "很", "也", "都", "the", "a", "an", "is", "are", "was", "were", "this", "that", "it"}
        # 提取中文词（简单按字符，不精确但够用）
        def get_cn_words(text):
            import re
            # 提取连续中文字符序列
            cn_phrases = re.findall(r'[\u4e00-\u9fff]+', text)
            words = set()
            for phrase in cn_phrases:
                for char in phrase:
                    words.add(char)
            return words
        
        cn_a = get_cn_words(text_a) - stop_words
        cn_b = get_cn_words(text_b) - stop_words
        
        # 英文词
        en_a = set(re.findall(r'[a-z]+', text_a))
        en_b = set(re.findall(r'[a-z]+', text_b))
        
        return bool((cn_a & cn_b) or (en_a & en_b))
    
    if a_has_cn_neg and not b_has_cn_neg:
        if has_shared_content(a, b):
            return f"A 说\"{a[:50]}\"，B 说\"{b[:50]}\"（中文否定矛盾）"
    if b_has_cn_neg and not a_has_cn_neg:
        if has_shared_content(a, b):
            return f"A 说\"{a[:50]}\"，B 说\"{b[:50]}\"（中文否定矛盾）"
    if a_has_cn_neg and b_has_cn_neg:
        if has_shared_content(a, b):
            return f"A 说\"{a[:50]}\"，B 说\"{b[:50]}\"（中文双重否定矛盾）"
    
    return None


def _detect_action_pattern(a: str, b: str) -> Optional[str]:
    """检测行为冲突（做 vs 不做）"""
    # 英文行为词对
    action_pairs = [
        ("use", "avoid"),
        ("recommend", "don't recommend"),
        ("should", "shouldn't"),
    ]
    
    for pos, neg in action_pairs:
        if pos in a and neg in b:
            return f"行为冲突：A 推荐\"{pos}\"，B 反对\"{neg}\""
        if neg in a and pos in b:
            return f"行为冲突：A 反对\"{neg}\"，B 推荐\"{pos}\""
    
    return None


def find_contradictions(
    records: List[MemoryRecord],
) -> List[Tuple[MemoryRecord, MemoryRecord, ContradictionResult]]:
    """
    在记忆列表中找出所有相互矛盾的记忆对
    """
    contradictions = []
    
    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            result = detect_record_pair_contradiction(records[i], records[j])
            if result.has_contradiction:
                contradictions.append((records[i], records[j], result))
    
    return contradictions


def apply_contradiction_penalty(
    record_a: MemoryRecord,
    record_b: MemoryRecord,
) -> Tuple[MemoryRecord, MemoryRecord]:
    """
    当检测到矛盾时，降低双方 importance
    """
    import time
    
    def _penalize(r: MemoryRecord, confidence: float) -> MemoryRecord:
        factor = 0.7 if confidence >= 0.8 else 0.85
        updated = MemoryRecord.from_dict(r.to_dict())
        updated.importance = max(0.1, updated.importance * factor)
        updated.metadata["contradiction_penalty"] = True
        updated.metadata["contradiction_at"] = int(time.time() * 1000)
        return updated
    
    result = detect_record_pair_contradiction(record_a, record_b)
    if not result.has_contradiction:
        return record_a, record_b
    
    updated_a = _penalize(record_a, result.confidence)
    updated_b = _penalize(record_b, result.confidence)
    
    return updated_a, updated_b
