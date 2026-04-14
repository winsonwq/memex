"""
Store Factory — 根据配置创建存储实例
"""
from typing import Optional

from .interface import VectorStore
from .lancedb import LanceDBStore
from .._config import load_config


def create_store(provider: Optional[str] = None) -> VectorStore:
    """
    工厂函数：根据配置创建向量存储实例
    
    Args:
        provider: 可选，覆盖配置中的 provider
    """
    config = load_config()
    
    if provider is None:
        provider = config.vector_store.provider
    
    if provider == "lancedb":
        return LanceDBStore()
    elif provider == "memory":
        # 测试用内存实现
        from .memory import MemoryStore
        return MemoryStore()
    else:
        raise ValueError(f"Unknown provider: {provider}")
