# Phase 0：奠基 ✅

**完成时间**：2026-04-14

---

## 交付物

### 1. 项目结构

```
memory-palace/
├── SPEC.md              # 规格文档
├── .gitignore
├── pyproject.toml
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── models.py    # MemoryEntry, Wing 数据模型
│   │   └── store.py     # SQLite 存储层
│   ├── palace/
│   │   ├── __init__.py
│   │   └── structure.py # 宫殿结构管理
│   ├── search/
│   │   ├── __init__.py
│   │   └── engine.py   # 搜索召回引擎
│   └── memory_stack/
│       ├── __init__.py
│       └── layer.py     # 四层记忆栈
└── data/               # 数据库存储目录
```

### 2. 核心模块

| 模块 | 状态 | 说明 |
|------|------|------|
| `core/models.py` | ✅ | MemoryEntry, Wing 数据模型 |
| `core/store.py` | ✅ | SQLite 存储 CRUD |
| `palace/structure.py` | ✅ | Wing/Room 结构管理 |
| `search/engine.py` | ✅ | 搜索接口（Phase 1 扩展向量搜索） |
| `memory_stack/layer.py` | ✅ | L0-L3 记忆栈框架 |

### 3. 设计决策

**✅ 决策 1：Verbatim 存储**
- 原文 100% 保留，不做 LLM 提取
- 摘要（closet）可选存储，指向原文

**✅ 决策 2：SQLite + LanceDB 混合**
- SQLite：结构化数据、索引、事务
- LanceDB：向量搜索（Phase 1 集成）

**✅ 决策 3：四层记忆栈**
- L0 Identity (~50 tokens)：始终加载
- L1 Critical Facts (~120 tokens)：始终加载
- L2 Room Recall (~200-500 tokens)：按需
- L3 Deep Search（无上限）：按需查询

---

## Phase 1 计划

- [ ] LanceDB 向量索引集成
- [ ] 语义搜索 API
- [ ] 全文搜索（FTS5）
- [ ] 基础测试

---

## Git 提交

```
commit xxxxx: Phase 0: 奠基 — 项目结构、核心模型、SQLite 存储层
```
