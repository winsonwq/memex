# Memex — 项目策划

> 创建时间：2026-04-14
> 状态：策划中

---

## 一、项目愿景

**一句话：** 用嵌入式向量数据库实现一套轻量级 Agent 记忆系统，以 CLI + Skill 的形式交付，让 Agent 可以快速接入"超强记忆能力"。

**解决的问题：**
- Agent 每次对话从零开始，没有积累
- 跨 session 的语义记忆无法复用
- 现有 Agent 框架的记忆方案要么太重（需要独立服务），要么太简陋（文件存储）

**技术目标：**
- 数据库抽象层：支持 LanceDB、Chroma 等多种嵌入式向量数据库平替
- 默认使用 LanceDB，接口清晰，换库无需修改业务逻辑

**对标参考：**
- OpenSwarm 的记忆系统设计（TypeScript 实现）
- MemPalace 的记忆分层理念

---

## 二、技术方案

### 2.1 技术栈选择

| 组件 | 选择 | 理由 |
|------|------|------|
| **核心语言** | Python | 最广泛的 Agent/ML 生态，LangChain/LlamaIndex 原生支持 |
| **向量数据库** | **抽象接口 + 多实现** | 嵌入式 DB 平替，配置化切换 |
| **Embedding** | **可配置**（默认 BGE-base-zh） | 本地运行，离线可用，中文友好 |
| **CLI 框架** | Click | Python CLI 标准，内置交互式 prompt |
| **交互提示** | questionary | Click 的交互式引导（类似 inquirer） |
| **Skill 格式** | OpenClaw Skill | 与现有 Agent 生态无缝集成 |

**Embedding 模型可选项：**

| 模型 | 维度 | 默认 | 适用场景 |
|------|------|------|---------|
| `BAAI/bge-base-zh-v1.5` | 768 | ✅ | 中文为主 |
| `BAAI/bge-small-zh-v1.5` | 512 | | 轻量，中文 |
| `Xenova/multilingual-e5-base` | 768 | | 中英混合 |
| `Xenova/multilingual-e5-small` | 384 | | 轻量，多语言 |

**向量数据库实现：**

| 实现 | 状态 | 适用场景 |
|------|------|---------|
| **LanceDB** | ✅ 首发 | 生产级，列式存储，多模态，版本控制 |
| **Chroma** | 🔲 规划 | 轻量，简单场景，快速原型 |
| **内存实现** | 🔲 测试用 | 单元测试，不需要持久化 |

**模型通过配置文件选择，存放在 `~/.memex/config.toml`，用户可随时修改。**

### 2.2 核心架构

```
memex/
├── src/memex/               # 核心库（installable package）
│   ├── __init__.py
│   ├── _config.py            # 配置管理（读写 config.toml）
│   ├── _embed.py             # Embedding 生成（可配置模型）
│   ├── _distillation.py      # 内容过滤/蒸馏
│   ├── _ops.py               # 高级操作（decay、consolidate、compact）
│   ├── _types.py             # 类型定义
│   ├── _installer.py         # 安装引导逻辑
│   │
│   │   # === 存储抽象层（核心设计）===
│   │   # 业务逻辑调用 VectorStore 接口，不直接依赖具体数据库
│   ├── store/
│   │   ├── __init__.py       # VectorStore 导出
│   │   ├── interface.py      # VectorStore 抽象接口（ABC）
│   │   ├── factory.py        # 工厂函数：根据配置创建实例
│   │   ├── lancedb.py        # LanceDB 实现
│   │   ├── chroma.py         # ChromaDB 实现
│   │   └── memory.py         # 内存实现（测试用）
│   │
│   └── cli.py                # CLI 命令入口
├── skills/                   # OpenClaw Skill
│   └── memory-skill/
│       └── SKILL.md          # Agent 读得懂的指令
├── tests/
│   └── test_memory.py
├── pyproject.toml
├── uv.lock
├── README.md
└── .env.example
```

**配置存储：**
```
~/.memex/
├── config.toml              # 配置文件
└── memory/                  # 向量数据库数据目录
```

**`config.toml` 示例：**
```toml
[memory]
storage_path = "~/.memex/memory"

[vector_store]
provider = "lancedb"   # 可选：lancedb | chroma | memory（测试）

[embedding]
model = "BAAI/bge-base-zh-v1.5"
dimension = 768

[retrieval]
default_limit = 10
min_similarity = 0.4
```

**便携性：**
- 数据全在 `~/.memex/`，迁移只需打包复制
- 迁移方法：`tar -czvf memex-backup.tar.gz ~/.memex/` → 新机器解压即可
- 代码：`git clone + pip install -e .`
- 换电脑 / 换环境 = 复制粘贴完事

**包结构说明：**
- 存储抽象层是本项目的**核心设计**：业务逻辑只依赖 `VectorStore` 接口，不直接调用 LanceDB 或 Chroma
- 切换数据库只需要改 `config.toml` 的 `provider`，无需修改业务代码
- Embedding 模型下载到 HuggingFace 缓存目录（`~/.cache/huggingface/`）

### 2.3 数据模型

```python
# 基于 OpenSwarm PRD v2.0 设计

class MemoryType(Enum):
    CONSTRAINT = "constraint"       # 约束/禁令 (importance: 0.9)
    USER_MODEL = "user_model"       # 用户偏好 (importance: 0.85)
    STRATEGY = "strategy"           # 策略方法 (importance: 0.8)
    SYSTEM_PATTERN = "system_pattern" # 系统模式 (importance: 0.75)
    BELIEF = "belief"               # 验证结论 (importance: 0.7)
    JOURNAL = "journal"             # 工作日志 (importance: 0.4, 14天过期)

@dataclass
class MemoryRecord:
    id: str
    type: MemoryType
    content: str                  # 规范化后的语义陈述
    raw_text: str                 # 原始文本，用于模型升级后重建索引
    vector: list[float]           # 768维 E5 embedding

    # PRD v2.0 核心字段
    importance: float              # 0-1，对推理的影响程度
    confidence: float              # 0-1，确定性
    stability: str                # 'low' | 'medium' | 'high'
    revision_count: int
    decay: float                  # 0-1，遗忘程度

    # 关系
    contradicts: list[str]         # 矛盾记忆 ID
    supports: list[str]            # 支持记忆 ID
    derived_from: str              # 来源 session/conv ID

    # 时间
    created_at: int               # timestamp ms
    last_updated: int
    last_accessed: int
    expires_at: int               # timestamp ms，永久=9999-12-31

    # 元数据
    repo: str                     # 所属项目
    title: str
    metadata: dict
    trust: float                  # 0-1
```

### 2.4 CLI 命令设计

```bash
# === 安装与初始化 ===
memex install     # 引导式安装（交互式 prompt）
memex setup       # 引导式配置（可选重新选择 embedding 模型）
memex init        # 非交互式初始化（使用默认配置）

# === 记忆读写 ===
memex save --type belief --content "..." --repo default
memex save --type constraint --content "..." --repo default --importance 0.95
memex search "查询内容" --limit 5 --repo default
memex get <memory-id>
memex list [--type belief] [--repo default] [--limit 20]
memex list --recent

# === 记忆管理 ===
memex update <memory-id> --content "新内容" --confidence 0.9
memex delete <memory-id>

# === 隐私控制（用户视角）===
memex recall            # 查看自己被记住了什么
memex purge <memory-id>  # 删除单条记忆
memex purge --all        # 清空所有记忆

# === 后台维护 ===
memex decay         # 应用 decay 衰减
memex consolidate    # 合并相似记忆
memex compact        # 清理过期/无用记忆（包括重建索引）
memex stats          # 查看统计

# === 导入导出 ===
memex export --format json > memories.json
memex import memories.json

# === 配置 ===
memex config show   # 查看当前配置
memex config set vector_store.provider lancedb  # 切换数据库实现
memex config set embedding.model <model-name>  # 修改 embedding 模型
```

#### 记忆检索输出设计（Agent Context 注入）

`memex search` 默认输出 JSON 格式，供 Agent 直接解析注入 context：

```json
{
  "query": "用户的项目架构是什么样的",
  "results": [
    {
      "id": "strategy-001",
      "type": "strategy",
      "content": "项目采用前后端分离架构，前端 Vue，后端 Spring Boot",
      "importance": 0.8,
      "confidence": 0.85,
      "stability": "high",
      "score": 0.92
    }
  ],
  "total": 1
}
```

**设计原则：**
- 输出结构化 JSON，Agent 可编程解析
- `content` 是记忆的实际内容，Agent 自行决定是否注入 context
- `importance` / `confidence` / `stability` 帮助 Agent 判断可信度
- `score` 是混合评分（相似度 + 重要性 + 新鲜度），越高越相关
- Skill 里写清楚"检索结果以 JSON 输出，Agent 自己决定如何使用"

**模型升级兼容性：**
- 存入记忆时，`raw_text` 字段保存原始文本
- 切换 embedding 模型时，执行 `memex compact --rebuild`，用新模型对 `raw_text` 重新向量化
- 无需手动迁移，数据自动保持一致
```

#### `install` 引导流程设计

```
$ memex install

🚀 Memex 安装向导
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 数据存储目录：~/.memex
   （可直接回车使用默认路径，或输入自定义路径）

🗄️ 向量数据库实现：
   1) LanceDB  [默认] 生产级，列式存储，多模态 ✅
   2) Chroma   轻量，简单场景

🤖 Embedding 模型选择：
   1) BAAI/bge-base-zh-v1.5    [768维] 推荐中文场景 ✅
   2) BAAI/bge-small-zh-v1.5   [512维] 轻量中文
   3) Xenova/multilingual-e5-base [768维] 中英混合
   4) Xenova/multilingual-e5-small [384维] 轻量多语言

   请选择 1-4 [默认 1]:

📦 正在下载 Embedding 模型...
   （首次下载需要一些时间，请耐心等待）

✅ 安装完成！

   数据目录：~/.memex/
   配置文件：~/.memex/config.toml
   记忆数据库：~/.memex/memory/

   开始使用：
   memex save --type belief --content "我的第一条记忆"
   memex search "查询记忆"
```

**实现方式：**
- 使用 `questionary` 库提供交互式 prompt
- 配置文件 `config.toml` 存储在 `~/.memex/`
- Embedding 模型下载到 `~/.cache/huggingface/`（HuggingFace 默认缓存）
- 引导过程自动检测模型是否已缓存，避免重复下载

### 2.5 Skill 设计（Agent 接入协议）

SKILL.md 是 Agent 理解"何时用记忆系统"的核心文档。

**核心设计原则：**
- Skill 不封装逻辑，只描述"什么场景该调什么命令"
- Agent 在合适的时机自己决定是否调用
- 记忆的读写都通过 CLI 命令，不暴露内部实现

**SKILL.md 内容大纲：**

```markdown
# Memex Skill

## 触发时机
1. 对话结束时 → 提炼关键信息存入记忆
2. 新对话开始时 → 检索相关记忆（结果以 JSON 输出，Agent 自行注入 context）
3. 遇到决策点时 → 查询是否有相关约束/策略
4. 发现新 pattern 时 → 存入 system_pattern
5. 用户明确偏好时 → 存入 user_model

## 记忆类型使用指南

| 类型 | 何时用 | importance |
|------|--------|-----------|
| `constraint` | 用户强制的规则 | 0.9 |
| `user_model` | 用户偏好/习惯 | 0.85 |
| `strategy` | 验证过的方法论 | 0.8 |
| `system_pattern` | 系统设计模式 | 0.75 |
| `belief` | 验证过的结论 | 0.7 |
| `journal` | 工作日志 | 0.4 |

## 调用命令

### 存入记忆
memex save --type <type> --content "..." --repo <namespace>

### 语义检索
memex search "查询内容" --limit 5 --repo <namespace>

### 查看统计
memex stats --repo <namespace>

## 混合评分
final_score = 0.55×similarity + 0.20×importance + 0.15×freshness + 0.10×frequency
```

**多 Agent 共存：**
- 每个 Agent 用不同的 `--repo` 命名空间
- `default` repo 用于跨 Agent 共享的通用记忆
- Agent 安装本 Skill 时可配置默认 repo

---

## 三、可行性分析

### 3.1 LanceDB Python SDK 成熟度

✅ **成熟可用**
- 官方维护，文档完整：https://lancedb.com/docs/
- 与 LangChain、LlamaIndex 官方集成
- 支持向量搜索 + 全文搜索 + SQL 混合查询
- 数据存储在本地文件夹，零运维

### 3.2 本地 Embedding 方案

| 方案 | 模型 | 优点 | 缺点 |
|------|------|------|------|
| **BGE-base-zh-v1.5**（默认） | bge-base-zh-v1.5 | 中文效果好、国产 | 英文支持一般 |
| **BGE-small-zh-v1.5** | bge-small-zh-v1.5 | 最轻量、512维 | 效果稍弱 |
| multilingual-e5-base | Xenova/e5-base-v2 | 中英混合、多语言 | 中文不如 BGE |
| OpenAI API | text-embedding-3 | 效果好 | 需要网络、API key |

**Embedding 模型设计为可插拔：**
- 通过 `config.toml` 配置模型名称
- 支持 BGE 系列（中文）、E5 系列（多语言）
- 模型在首次使用时自动下载到 HuggingFace 缓存
- LanceDB 表的 vector 维度跟随模型自动调整（512 / 768 / 384）
- 切换模型后执行 `memex compact --rebuild` 重建索引（使用 raw_text 重新向量化）

**选择 BGE-base-zh-v1.5 作为默认的理由：**
- 国产模型，中文效果优秀
- 768 维，存储适中
- sentence-transformers 库直接支持
- 比 Xenova E5 在中文场景下效果更好

### 3.3 与 OpenSwarm 的差异化

| 维度 | OpenSwarm | Memex |
|------|-----------|-------|
| 语言 | TypeScript | Python |
| 交付形式 | Agent 框架子系统 | 独立 CLI 包 + Skill |
| 复用方式 | 强耦合 | 可插拔 |
| 分发 | 随框架发布 | pip 独立发布 |
| 定位 | 框架的一部分 | 通用记忆基础设施 |

**核心差异：**
- OpenSwarm 是 Agent 框架，记忆系统是框架内嵌功能
- Memex 是独立工具，通过 CLI/Skill 给任何 Agent 用

### 3.4 技术风险

| 风险 | 概率 | 影响 | 缓解方案 |
|------|------|------|----------|
| Embedding 模型中文效果差 | 中 | 高 | 默认 BGE-base-zh，测试验证 |
| 模型升级后旧记忆向量不兼容 | 高 | 中 | 存入时同时保存原始文本，换模型时自动重建索引 |
| LanceDB 版本迭代破坏兼容 | 低 | 中 | pin 版本，测试升级 |
| 记忆质量无法保证（garbage in） | 高 | 中 | distillation 过滤 |
| 首次加载延迟（模型下载） | 低 | 低 | 懒加载，首次后缓存，后续调用更快 |

**当前场景定位：单机 Coding Agent，不考虑多 Agent 共享问题。**

### 3.5 预期效果

基于 OpenSwarm 的实践：
- 10万条记忆检索延迟：< 100ms（本地 SSD）
- 存储效率：列式存储比 JSON 文件节省 3-5x 空间
- 遗忘机制：7天不访问的记忆开始衰减，避免记忆腐烂

---

## 四、Milestones

### Phase 1: MVP（核心能力）
- [ ] 项目初始化（pyproject.toml、目录结构）
- [ ] LanceDB 连接 + 表初始化（包含 raw_text 字段）
- [ ] BGE embedding 集成
- [ ] `save` / `search` / `get` / `list` / `delete` CLI 命令
- [ ] `recall` / `purge` 隐私控制命令
- [ ] OpenClaw Skill 编写（SKILL.md）
- [ ] 基本测试覆盖
- [ ] 文档（README + 安装指南）

### Phase 2: 增强记忆
- [ ] distillation 过滤逻辑
- [ ] revision 机制（更新已有记忆）
- [ ] contradiction detection
- [ ] `decay` / `consolidate` / `compact --rebuild` 后台任务（含模型升级重建索引）
- [ ] `export` / `import` 功能

### Phase 3: 生态集成
- [ ] 发布到 PyPI
- [ ] ClawHub 发布 Skill
- [ ] LangChain Integration（可选）
- [ ] 性能基准测试（10万条记录延迟）
- [ ] 与 OpenSwarm 效果对比测试

---

## 五、竞争分析

| 产品 | 类型 | 存储 | 优点 | 缺点 |
|------|------|------|------|------|
| **MemPalace** | 框架/论文 | Chroma | 记忆分层理念好 | 不开源，只发论文 |
| **OpenSwarm** | Agent 框架 | LanceDB | 记忆系统完整 | 强耦合框架，TS 实现 |
| **Kairo** | Harness 框架 | 文件 | 概念清晰 | 无实际记忆系统 |
| **Memex** | CLI + Skill | LanceDB | 轻量、可插拔、Python | 从零开始实现 |

**定位：** Memex 是"记忆系统的便携基础设施"，面向单机 Coding Agent 场景，通过 Skill 快速增强 Agent 记忆能力。差异化在于：独立发布 + Python 生态 + 便携式设计。

---

## 六、发布与分发

### 6.1 发布方式

**方式 1: pip / uv（推荐）**
```bash
# PyPI 发布后
pip install memex
uv pip install memex

# 安装后直接用
memex init
memex save --type belief --content "..."
```

**方式 2: 打包成二进制（无 Python 环境要求）**
```bash
# 用 PyInstaller 打包
pyinstaller --onefile src/memex/cli.py

# 用户下载二进制，直接运行
./memex init
```

**方式 3: 通过 OpenClaw Skill 安装**
```bash
# 使用 clawhub 安装
clawhub install memex

# 或手动复制 skill 到 ~/.openclaw/skills/
```

### 6.2 依赖管理

```toml
# pyproject.toml
[project]
name = "memex"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "lancedb>=0.12",              # 默认向量数据库
    "chromadb>=0.4",              # 可选向量数据库
    "sentence-transformers>=2.2", # Embedding 模型加载
    "click>=8.0",                 # CLI 框架
    "questionary>=2.0",           # 交互式引导 prompt
    "pydantic>=2.0",             # 配置验证
    "toml>=0.10",                # 配置文件读写
]

[project.scripts]
memex = "memex.cli:cli"
```

### 6.3 发布渠道

| 渠道 | 适用场景 | 难度 |
|------|---------|------|
| PyPI | pip 安装，通用 | 需要账号，审核简单 |
| GitHub Release | 二进制打包分发 | 简单，手动操作 |
| ClawHub | OpenClaw 用户一键安装 | 需要账号 |
| Homebrew | macOS 用户 | 需要维护 tap |

---

## 七、结论

**可行吗？** ✅ 可行，技术方案成熟。

**技术路线：**
- Python + LanceDB + BGE = 本地离线、高性能、零运维
- 数据库抽象层 = 支持 LanceDB / Chroma 平替
- CLI 封装 = 人可以用
- Skill 封装 = Agent 可以用
- JSON 输出 = Agent 可直接注入 context
- 便携设计 = 数据打包迁移，代码 clone 即用

**核心价值：**
面向单机 Coding Agent 的"超能力记忆工具"，通过 Skill 快速增强 Agent 的记忆能力。设计原则：
1. **注入简单** — search 输出 JSON，Agent 自己决定怎么用
2. **迁移方便** — 文件系统存储，打包复制即可
3. **升级兼容** — raw_text 保留，换模型自动重建索引
4. **隐私可控** — recall/purge 用户自主控制

**下一步：**
1. ✅ 项目策划完成
2. Phase 1 MVP 详细设计
3. 开始写代码

---

## 相关文档

| 文档 | 说明 |
|------|------|
| `PROJECT_PLAN.md` | 项目策划主文档 |
| `TEST_STRATEGY.md` | 测试策略（草案）|
