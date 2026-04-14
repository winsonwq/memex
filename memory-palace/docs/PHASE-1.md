# Phase 1：向量搜索集成 ✅

**完成时间**：2026-04-14

---

## 交付物

### 1. 新增模块

| 模块 | 文件 | 状态 | 说明 |
|------|------|------|------|
| `search/vector_index.py` | LanceDB 向量索引 | ✅ | IVF-PQ 索引，OpenAI/SentenceTransformer embedding |
| `search/engine.py` | 搜索召回引擎 | ✅ | SQL + 向量混合搜索 |
| `palace/structure.py` | 宫殿结构 | ✅ | 集成向量索引 |
| `memory_stack/layer.py` | 四层记忆栈 | ✅ | L2 使用向量搜索 |
| `tests/test_phase1.py` | Phase 1 测试 | ✅ | 5 个测试全部通过 |

### 2. 核心功能

**向量搜索**：
- LanceDB IVF-PQ 索引
- 支持 OpenAI / SentenceTransformer embedding
- 按 wing/room 过滤
- 降级方案：SQL LIKE（无向量索引时）

**混合搜索策略**：
```
有 query + 有向量索引 → 向量语义搜索
有 query + 无向量索引 → SQL LIKE
无 query → SQL 精确匹配
```

---

## 设计决策

**✅ 决策：降级策略**
- 优先使用向量搜索
- 无 API Key 时自动降级到 SQL LIKE
- 不因为缺少依赖而崩溃

**✅ 决策：Embedding 模型**
- 默认 OpenAI（需要 API Key）
- 可选 SentenceTransformer（本地，无需 Key）
- 通过 `embed_model` 参数切换

---

## Phase 2 计划

- [ ] 全文搜索（FTS5）集成
- [ ] Hall/Tunnel 跨房间连接
- [ ] 偏好检测（Regex 16 种模式）
- [ ] 性能基准测试

---

## Git 提交

```
commit xxxxx: Phase 1: 向量搜索 — LanceDB 集成、SQL/向量混合搜索
```
