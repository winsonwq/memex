"""
VectorStore — 向量存储抽象接口
业务逻辑只依赖此接口，不直接调用具体数据库
"""
from abc import ABC, abstractmethod
from typing import Optional, List

from .._types import MemoryRecord


class VectorStore(ABC):
    """向量存储抽象接口"""
    
    @abstractmethod
    def add(self, record: MemoryRecord, vector: List[float]) -> None:
        """添加记忆"""
        pass
    
    @abstractmethod
    def search(
        self,
        query_vector: List[float],
        repo: Optional[str] = None,
        limit: int = 10,
    ) -> list[tuple[MemoryRecord, float]]:
        """
        向量相似度搜索
        
        Returns:
            list of (record, score) tuples
        """
        pass
    
    @abstractmethod
    def search_by_content(
        self,
        content: str,
        repo: Optional[str] = None,
        limit: int = 10,
    ) -> list[tuple[MemoryRecord, float]]:
        """
        文本搜索（数据库实现自行决定是否用向量）
        """
        pass
    
    @abstractmethod
    def get(self, record_id: str) -> Optional[MemoryRecord]:
        """获取单条记忆"""
        pass
    
    @abstractmethod
    def list(
        self,
        repo: Optional[str] = None,
        type: Optional[str] = None,
        limit: int = 100,
    ) -> list[MemoryRecord]:
        """列出记忆"""
        pass
    
    @abstractmethod
    def update(self, record: MemoryRecord) -> None:
        """更新记忆"""
        pass
    
    @abstractmethod
    def delete(self, record_id: str) -> None:
        """删除记忆"""
        pass
    
    @abstractmethod
    def count(self, repo: Optional[str] = None) -> int:
        """统计数量"""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """关闭连接"""
        pass
