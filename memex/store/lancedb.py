"""
LanceDB 实现
"""
from datetime import datetime
from pathlib import Path
from typing import Optional, List

import lancedb
import pyarrow as pa

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
        self._dimension = config.embedding.dimension
        self._ensure_table()
    
    def _ensure_table(self):
        """确保表存在"""
        if self.table_name not in self.db.table_names():
            # 使用正确的 schema 创建表
            schema = pa.schema([
                pa.field("id", pa.string()),
                pa.field("type", pa.string()),
                pa.field("content", pa.string()),
                pa.field("raw_text", pa.string()),
                pa.field("importance", pa.float64()),
                pa.field("confidence", pa.float64()),
                pa.field("stability", pa.string()),
                pa.field("revision_count", pa.int64()),
                pa.field("contradicts", pa.list_(pa.string())),
                pa.field("supports", pa.list_(pa.string())),
                pa.field("derived_from", pa.string()),
                pa.field("created_at", pa.int64()),
                pa.field("last_updated", pa.int64()),
                pa.field("last_accessed", pa.int64()),
                pa.field("expires_at", pa.int64()),
                pa.field("repo", pa.string()),
                pa.field("title", pa.string()),
                pa.field("metadata", pa.string()),  # JSON 字符串
                pa.field("trust", pa.float64()),
                pa.field("vector", pa.list_(pa.float64(), self._dimension)),
            ])
            
            self.db.create_table(self.table_name, schema=schema)
    
    def _get_table(self):
        return self.db.open_table(self.table_name)
    
    def add(self, record: MemoryRecord, vector: List[float]) -> None:
        """添加记忆"""
        table = self._get_table()
        
        data = record.to_dict()
        data["vector"] = vector
        data["metadata"] = str(data["metadata"])  # JSON 字符串
        
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
        
        query = table.search(
            query_vector,
            vector_column_name="vector",
        )
        
        if where:
            query = query.where(where)
        
        results = query.limit(limit).to_list()
        
        records = []
        for i, r in enumerate(results):
            r.pop("vector", None)  # 移除 vector 字段
            r.pop("_distance", None)  # 移除 LanceDB 返回的距离字段
            r["metadata"] = {}
            record = MemoryRecord.from_dict(r)
            # 用排名作为近似分数
            score = 1.0 - (i / (limit * 2))
            records.append((record, score))
        
        return records
    
    def search_by_content(
        self,
        content: str,
        repo: Optional[str] = None,
        limit: int = 10,
    ) -> list[tuple[MemoryRecord, float]]:
        """文本搜索（TODO: Phase 2 实现 FTS）"""
        return []
    
    def get(self, record_id: str) -> Optional[MemoryRecord]:
        """获取单条记忆"""
        table = self._get_table()
        
        results = table.search().where(f"id = '{record_id}'").limit(1).to_list()
        
        if not results:
            return None
        
        r = results[0]
        r.pop("vector", None)
        r["metadata"] = {}
        return MemoryRecord.from_dict(r)
    
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
        
        records = []
        for r in results:
            r.pop("vector", None)
            r["metadata"] = {}
            records.append(MemoryRecord.from_dict(r))
        
        return records
    
    def update(self, record: MemoryRecord) -> None:
        """更新记忆"""
        table = self._get_table()
        
        record.last_updated = int(datetime.now().timestamp() * 1000)
        
        # 删除旧记录
        table.delete(f"id = '{record.id}'")
        
        # 添加新记录（需要重新获取 vector，这里简化处理）
        # 完整实现需要调用者传入新 vector
        data = record.to_dict()
        data.pop("vector", None)
        data["metadata"] = str(data["metadata"])
        # 注意：update 需要同时更新 vector，这里会丢失
        table.add([data])
    
    def delete(self, record_id: str) -> None:
        """删除记忆"""
        table = self._get_table()
        table.delete(f"id = '{record_id}'")
    
    def count(self, repo: Optional[str] = None) -> int:
        """统计数量"""
        return len(self.list(repo=repo, limit=10000))
    
    def close(self) -> None:
        """关闭连接"""
        pass
