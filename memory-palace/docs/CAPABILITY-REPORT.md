# Memory Palace & Memex — 能力报告

> 日期：2026-04-14
> 参考基准：MemPalace LongMemEval Benchmark

---

## 一、参考基准：MemPalace Benchmark

### LongMemEval R@5（500 题）

| 模式 | R@5 得分 | API 调用 | 成本 |
|------|---------|---------|------|
| **Raw ChromaDB（纯 verbatim）** | **96.6%** | **0** | **$0** |
| Hybrid v4 + Haiku rerank | 100% | ~500 次 | ~$0.50 |
| Mem0 | ~85% | 需要 | $19-249/月 |
| Supermemory | ~85% | 需要 | — |
| Mastra | 94.87% | GPT-5-mini | API 费用 |
| Zep | ~85% | 需要 + Neo4j | $25/月+ |

### 核心 Insight

**Verbatim 存储本身就是最强的。**

96.6% 的 raw baseline 打败了所有需要 LLM 提取摘要的方案。原因：
- LLM 提取"user prefers PostgreSQL"时丢失了 *why*、*alternatives considered*、*tradeoffs discussed*
- Verbatim 全部保留，搜索时原文就在那里

### Palace 结构的贡献

```
搜所有 closets:           60.9%  R@10
限定 wing 搜索:           73.1%  (+12%)
wing + hall 过滤:         84.8%  (+24%)
wing + room 过滤:         94.8%  (+34%)
```

---

## 二、Memory Palace + Memex 当前能力

### 2.1 架构对比

| 维度 | MemPalace | Memory Palace | Memex |
|------|-----------|--------------|-------|
| **存储** | ChromaDB | SQLite + LanceDB | LanceDB |
| **向量搜索** | ChromaDB | LanceDB (IVF-PQ) | LanceDB (IVF-PQ) |
| **记忆类型** | 4 Hall 类型 | 5 种 | 6 种 |
| **结构** | Wing/Room/Closet/Drawer | Wing/Room/Closet/Drawer | Repo 隔离 |
| **层级加载** | L0-L3 | L0-L3 | 全部加载 |
| **Verbatim 存储** | ✅ | ✅ | ✅ |

### 2.2 已实现能力

#### Memory Palace
- [x] Verbatim 原文存储（不依赖 LLM 提取）
- [x] SQLite 结构化存储
- [x] LanceDB 向量索引（Phase 1）
- [x] Wing/Room/Closet/Drawer 宫殿结构
- [x] 四层记忆栈框架（L0-L3）
- [x] Hall/Tunnel 跨房间连接

#### Memex
- [x] 6 种记忆类型（constraint/user_model/strategy/system_pattern/belief/journal）
- [x] LanceDB 向量存储
- [x] BGE-base-zh-v1.5 Embedding（768 维，中文优化）
- [x] 语义搜索（JSON 输出）
- [x] Repo 命名空间隔离
- [x] 隐私控制（recall/purge）
- [x] CLI + OpenClaw Skill

### 2.3 性能预估

基于 MemPalace benchmark 推断：

| 场景 | 预估得分 | 说明 |
|------|---------|------|
| **纯语义搜索** | ~85-90% | LanceDB IVF-PQ vs ChromaDB |
| **+ Wing/Repo 过滤** | ~90-95% | 元数据过滤增强 |
| **+ Hall 类型过滤** | ~93-97% | 同类记忆聚合 |

**差距分析**：
- MemPalace 使用 ChromaDB，我们使用 LanceDB——性能相近
- Palace 结构的元数据过滤机制类似——预期效果接近
- 主要差距：MemPalace 有 LongMemEval 实际测试数据，我们没有

---

## 三、与 MemPalace 的差距

### 3.1 已达到

| 能力 | Memory Palace | Memex | MemPalace |
|------|-------------|-------|-----------|
| Verbatim 存储 | ✅ | ✅ | ✅ |
| 向量语义搜索 | ✅ | ✅ | ✅ |
| Wing/Repo 隔离 | ✅ | ✅ | ✅ |
| Room/Type 分类 | ✅ | ✅ | ✅ |
| Hall 跨房间连接 | ✅ | ❌ | ✅ |
| Tunnel 跨 wing 连接 | ❌ | ❌ | ✅ |
| 四层记忆栈 | ✅ | ❌ | ✅ |
| LLM-free 设计 | ✅ | ✅ | ✅ |

### 3.2 差距

| 差距 | 影响 | 优先级 |
|------|------|--------|
| **无实际 benchmark 测试** | 无法量化真实 R@5/R@10 | 中 |
| **MemPalace 有 AAAK 压缩** | 更高存储效率 | 低 |
| **MemPalace 有偏好 Regex 检测** | 自动识别偏好表达 | 中 |
| **MemPalace 有 contradiction detection** | 自动检测矛盾记忆 | 低 |

### 3.3 超越点

| 能力 | Memory Palace / Memex | MemPalace 没有 |
|------|----------------------|----------------|
| **中文 Embedding** | BGE-base-zh-v1.5（中文优化） | ❌ 只有英文模型 |
| **多 Agent 支持** | Repo 命名空间 | ❌ 单用户 |
| **便携设计** | `~/.memex/` 打包迁移 | ❌ 需要单独部署 |
| **OpenClaw Skill** | Agent 直接调用 | ❌ 无 |

---

## 四、技术能力分析

### 4.1 存储效率

| 组件 | 选择 | 理由 |
|------|------|------|
| **向量数据库** | LanceDB | 列式存储，版本控制，列式查询 |
| **Embedding** | BGE-base-zh-v1.5 | 768 维，中文 SOTA，本地运行 |
| **存储格式** | Parquet/Lance | 比 JSON 文件节省 3-5x 空间 |

### 4.2 检索延迟

| 场景 | 预期延迟 | 说明 |
|------|---------|------|
| 10,000 条记忆 | < 50ms | IVF-PQ 索引 |
| 100,000 条记忆 | < 100ms | 近似最近邻搜索 |
| 1,000,000 条记忆 | < 500ms | 需要量化优化 |

### 4.3 容量

| 指标 | 预估 |
|------|------|
| 单机存储上限 | ~10M 条记忆（受磁盘限制） |
| 向量维度 | 768 维 |
| 每条记忆大小 | ~2-5 KB（不含向量） |

---

## 五、对比总结

### 5.1 Memory Palace vs Memex

| 维度 | Memory Palace | Memex |
|------|-------------|-------|
| **定位** | AI 自我实现，研究导向 | Agent 基础设施，实用导向 |
| **存储** | SQLite + LanceDB | LanceDB |
| **Embedding** | 可配置（需 API Key） | 本地 BGE（无需 Key） |
| **交付** | 库/框架 | CLI + Skill |
| **目标用户** | 开发者/研究者 | Agent/终端用户 |

### 5.2 与业界对比

| 系统 | 记忆质量 | 成本 | 部署 | 中文支持 |
|------|---------|------|------|---------|
| **Memory Palace/Memex** | ~90-95%（预估） | $0 | 本地 | ✅ |
| MemPalace | 96.6%（实测） | $0 | 本地 | ❌ |
| Mem0 | ~85% | $19-249/月 | 云 | ✅ |
| Supermemory | ~85% | 订阅 | 云 | ✅ |
| Zep | ~85% | $25/月+ | 云 | ✅ |

---

## 六、结论

### 6.1 当前能力

Memory Palace + Memex 实现了：
- **Verbatim 存储**：不依赖 LLM 提取，保留完整上下文
- **向量语义搜索**：本地运行，中文优化，无需 API Key
- **结构化召回**：Wing/Repo + Room/Type 二层过滤
- **隐私可控**：recall/purge 用户自主控制

### 6.2 预期效果

基于 MemPalace benchmark 推断：
- **R@5**：~90-95%（纯搜索 + 元数据过滤）
- **R@10**：~85-90%（ Palace 结构增强）

### 6.3 差距

| 差距 | 说明 |
|------|------|
| 无实际 benchmark | 需要建立 LongMemEval 类似的测试集 |
| 偏好自动检测 | MemPalace 用 Regex 检测 16 种偏好模式 |
| 矛盾检测 | MemPalace 有 contradiction detection |

### 6.4 优势

| 优势 | 说明 |
|------|------|
| 中文优先 | BGE-base-zh-v1.5 中文 SOTA |
| 零成本 | 本地运行，无 API 费用 |
| 便携设计 | `~/.memex/` 打包迁移 |
| Agent 集成 | OpenClaw Skill 直接调用 |

---

## 七、下一步

| 优先级 | 任务 | 说明 |
|--------|------|------|
| 高 | 建立测试集 | 参考 LongMemEval 构建中文测试集 |
| 高 | Preference Regex | 自动检测用户偏好表达 |
| 中 | Contradiction Detection | 自动检测矛盾记忆 |
| 中 | LLM Summarization | 可选的 AAAK 压缩 |
| 低 | 多 Agent 共享 | 团队记忆同步 |

---

## 参考

- [MemPalace GitHub](https://github.com/milla-jovovich/mempalace)
- [LongMemEval Benchmark](https://github.com/milla-jovovich/mempalace/tree/main/benchmarks)
- [LanceDB](https://lancedb.com)
- [BGE-base-zh-v1.5](https://huggingface.co/BAAI/bge-base-zh-v1.5)
