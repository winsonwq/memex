"""
Vector Index — LanceDB 向量索引层
Verbatim 原文 + 向量嵌入，不依赖 LLM 判断什么值得记忆
"""
import os
from typing import Optional

import lancedb

from ..core.models import MemoryEntry


class VectorIndex:
    """
    LanceDB 向量索引
    
    设计原则：
    - 原文 100% 存储，不做摘要提取
    - 向量用于语义搜索，原始内容始终可查
    - 支持 IVF_PQ（默认）、HNSW、FLAT 索引
    """
    
    def __init__(
        self,
        db_path: str = "data/memory_vectors",
        embed_model: str = "openai",
        api_key: Optional[str] = None,
    ):
        self.db_path = db_path
        self.embed_model = embed_model
        
        # 初始化 LanceDB
        self.db = lancedb.connect(db_path)
        
        # Embedding 模型
        self._embedder = self._init_embedder(api_key)
        
        # 表名
        self.table_name = "memory_entries"
    
    def _init_embedder(self, api_key: Optional[str]):
        """初始化 embedding 模型"""
        if self.embed_model == "openai":
            from lancedb.embeddings import OpenAI

            return OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
        elif self.embed_model == "sentence-transformers":
            from lancedb.embeddings import SentenceTransformer
            
            return SentenceTransformer()
        else:
            raise ValueError(f"Unsupported embed model: {self.embed_model}")
    
    def _get_or_create_table(self):
        """获取或创建表"""
        if self.table_name in self.db.table_names():
            return self.db.open_table(self.table_name)
        
        # 创建表，使用 embedder 自动向量化
        table = self.db.create_table(
            self.table_name,
            schema={
                "id": "string",
                "content": "string",
                "vector": self._embedder.vector_field(),
                "wing": "string",
                "room": "string",
                "hall": "string",
                "timestamp": "string",
            },
        )
        return table
    
    def add(self, entry: MemoryEntry) -> None:
        """添加记忆到向量索引"""
        table = self._get_or_create_table()
        
        table.add([
            {
                "id": entry.id,
                "content": entry.content,
                "wing": entry.wing,
                "room": entry.room,
                "hall": entry.hall,
                "timestamp": entry.timestamp,
            }
        ])
    
    def search(
        self,
        query: str,
        wing: Optional[str] = None,
        room: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict]:
        """
        向量语义搜索
        
        1. 将 query 文本向量化
        2. 在 LanceDB 中进行 ANN 搜索
        3. 可选过滤：wing / room
        """
        table = self._get_or_create_table()
        
        # 构建过滤条件
        where_clauses = []
        if wing:
            where_clauses.append(f"wing = '{wing}'")
        if room:
            where_clauses.append(f"room = '{room}'")
        
        where = " AND ".join(where_clauses) if where_clauses else None
        
        # 向量搜索
        results = table.vector_search(
            query,
            vector_column_name="content",  # 使用 content 列的向量化
            where=where,
            limit=limit,
        )
        
        return results.to_list()
    
    def search_hybrid(
        self,
        query: str,
        wing: Optional[str] = None,
        room: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict]:
        """
        混合搜索：向量 + 全文
        
        TODO: LanceDB 支持 full-text search，这个方法在 Phase 2 实现
        """
        # Phase 2: 混合向量 + FTS
        return self.search(query, wing, room, limit)
    
    def delete(self, entry_id: str) -> None:
        """删除记忆"""
        table = self._get_or_create_table()
        table.delete(f"id = '{entry_id}'")
    
    def rebuild_index(self) -> None:
        """
        重建向量索引
        
        LanceDB 支持在线重建索引，不需要全量重写
        """
        table = self._get_or_create_table()
        
        # IVF_PQ 索引适合大多数场景
        table.create_index(
            type="IVF_PQ",
            column="vector",
            num_sub_vectors=96,
        )
