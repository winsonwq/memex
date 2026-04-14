"""
Config — 配置管理
~/.memex/config.toml
"""
import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class MemoryConfig(BaseModel):
    """记忆配置"""
    storage_path: str = "~/.memex/memory"


class VectorStoreConfig(BaseModel):
    """向量存储配置"""
    provider: str = "lancedb"  # lancedb | chroma | memory


class EmbeddingConfig(BaseModel):
    """Embedding 配置"""
    model: str = "BAAI/bge-base-zh-v1.5"
    dimension: int = 768


class RetrievalConfig(BaseModel):
    """检索配置"""
    default_limit: int = 10
    min_similarity: float = 0.4


class Config(BaseModel):
    """完整配置"""
    memory: MemoryConfig = MemoryConfig()
    vector_store: VectorStoreConfig = VectorStoreConfig()
    embedding: EmbeddingConfig = EmbeddingConfig()
    retrieval: RetrievalConfig = RetrievalConfig()


# 全局配置实例
_config: Optional[Config] = None


def get_config_path() -> Path:
    """获取配置路径"""
    return Path.home() / ".memex" / "config.toml"


def load_config() -> Config:
    """加载配置"""
    global _config
    
    if _config is not None:
        return _config
    
    config_path = get_config_path()
    
    if config_path.exists():
        import toml
        data = toml.load(config_path)
        _config = Config(**data)
    else:
        _config = Config()
    
    return _config


def save_config(config: Config) -> None:
    """保存配置"""
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    import toml
    with open(config_path, "w") as f:
        toml.dump(config.model_dump(), f)
    
    global _config
    _config = config


def get_storage_path() -> Path:
    """获取存储路径"""
    config = load_config()
    path = Path(config.memory.storage_path).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path
