"""
Embed — Embedding 生成
支持可配置的模型：BGE、E5 等
"""
from typing import Optional

from sentence_transformers import SentenceTransformer

from ._config import load_config


# 全局模型实例
_model: Optional[SentenceTransformer] = None


def get_model() -> SentenceTransformer:
    """获取或加载模型"""
    global _model
    
    if _model is not None:
        return _model
    
    config = load_config()
    
    _model = SentenceTransformer(config.embedding.model)
    
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """生成文本的 embedding 向量"""
    model = get_model()
    return model.encode(texts, normalize_embeddings=True).tolist()


def embed_text(text: str) -> list[float]:
    """生成单条文本的 embedding"""
    return embed_texts([text])[0]


def get_dimension() -> int:
    """获取 embedding 维度"""
    config = load_config()
    return config.embedding.dimension
