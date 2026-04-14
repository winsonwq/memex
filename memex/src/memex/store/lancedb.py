"""
LanceDB 实现
"""
from pathlib import Path
from typing import Optional, List

import lancedb

from .._types import MemoryRecord
from .._config import load_config, get_storage_path
from .interface import VectorStore


class LanceDBStore(VectorStore):
    """LanceDB 向量存储实现"""
    
    def __init__(self, db_path: Optional[str] = None):
        config = load_config()
        
        if db_path is None:
            db_path = get_storage_path() / "lancedb"
        else:
            db_path = Path(db_path)
        
        self.db = lancedb.connect(str(db_path))
        self.table_name = "memories"
        self._ensure_table()
    
    def _ensure_table(self):
        """确保表存在"""
        if self.table_name not in self.db.table_names():
            # 创建表
            self.db.create_table(self.table_name, data=[
                {
                    "id": "placeholder",
                    "vector": [0.0] * 768,
                }
            ])
            # 删除 placeholder
            tbl = self.db.open_table(self.table_name)
            tbl.delete("id = 'placeholder'")
    
    def _get_table(self):
        return self.db.open_table(self.table_name)
    
    def add(self, record: MemoryRecord, vector: List[float]) -> None:
        """添加记忆"""
        table = self._get_table()
        
        data = record.to_dict()
        data["vector"] = vector
        
        table.add([data])
    
    def search(
        self,
        query_vector: List[float],
        repo: Optional[str] = None,
        limit: int = 10,
    ) -> list[tuple[MemoryRecord, float]]:
        """向量相似度搜索"""
        table = self._get_table()
        
        # 构建过滤
        where = f"repo = '{repo}'" if repo else None
        
        results = table.vector_search(
            query_vector,
            vector_column_name="vector",
            where=where,
            limit=limit,
        )
        
        records = []
        for r in results.to_list():
            record = MemoryRecord.from_dict(r)
            # LanceDB 不直接返回分数，用相似度排名作为近似
            records.append((record, 1.0 - (len(records) / (limit * 2))))
        
        return records
    
    def search_by_content(
        self,
        content: str,
        repo: Optional[str] = None,
        limit: int = 10,
    ) -> list[tuple[MemoryRecord, float]]:
        """
        文本搜索（使用 LanceDB 的 full-text search）
        """
        # TODO: Phase 2 实现 FTS
        # 目前返回空列表，需要 embedding 支持
        return []
    
    def get(self, record_id: str) -> Optional[MemoryRecord]:
        """获取单条记忆"""
        table = self._get_table()
        
        results = table.search().where(f"id = '{record_id}'").limit(1).to_list()
        
        if not results:
            return None
        
        return MemoryRecord.from_dict(results[0])
    
    def list(
        self,
        repo: Optional[str] = None,
        type: Optional[str] = None,
        limit: int = 100,
    ) -> list[MemoryRecord]:
        """列出记忆"""
        table = self._get_table()
        
        query = table.search()
        
        conditions = []
        if repo:
            conditions.append(f"repo = '{repo}'")
        if type:
            conditions.append(f"type = '{type}'")
        
        if conditions:
            where = " AND ".join(conditions)
            query = query.where(where)
        
        results = query.limit(limit).to_list()
        
        return [MemoryRecord.from_dict(r) for r in results]
    
    def update(self, record: MemoryRecord) -> None:
        """更新记忆"""
        table = self._get_table()
        
        record.last_updated = int(datetime.now().timestamp() * 1000)
        
        # LanceDB 没有原生 update，用 delete + add 模拟
        table.delete(f"id = '{record.id}'")
        
        # 注意：update 需要同时更新 vector，这里简化处理
        # 完整实现需要在调用 update 时传入新 vector
        table.add([record.to_dict()])
    
    def delete(self, record_id: str) -> None:
        """删除记忆"""
        table = self._get_table()
        table.delete(f"id = '{record_id}'")
    
    def count(self, repo: Optional[str] = None) -> int:
        """统计数量"""
        table = self._get_table()
        
        if repo:
            results = table.search().where(f"repo = '{repo}'").limit(1000).to_list()
        else:
            results = table.search().limit(1000).to_list()
        
        return len(results)
    
    def close(self) -> None:
        """关闭连接"""
        # LanceDB 是嵌入式，不需要显式关闭
        pass


# 需要 datetime
from datetime import datetime
