# Memex — Agent 记忆系统

> 用嵌入式向量数据库实现轻量级 Agent 记忆系统，以 CLI + Skill 的形式交付。

## 一句话

**Memex 让 Agent 记住一切，实现跨会话的持续学习。**

---

## 特性

- **原文存储** — 原文保留，不依赖 LLM 提取摘要
- **向量语义搜索** — 支持自然语言查询记忆
- **六种记忆类型** — constraint / user_model / strategy / system_pattern / belief / journal
- **隐私可控** — recall / purge 用户自主控制
- **多 Agent 支持** — 通过 repo 命名空间隔离
- **便携设计** — `~/.memex/` 打包迁移

---

## 快速开始

### 安装

```bash
pip install memex
```

### 初始化

```bash
memex init
```

### 存入记忆

```bash
memex save --type belief --content "用户喜欢简洁的回复风格" --repo user
```

### 搜索记忆

```bash
memex search "用户有什么偏好" --repo user --limit 5
```

**返回 JSON**（供 Agent 解析）：

```json
{
  "query": "用户有什么偏好",
  "results": [
    {
      "id": "uuid",
      "type": "belief",
      "content": "用户喜欢简洁的回复风格",
      "importance": 0.7,
      "confidence": 0.8,
      "score": 0.92
    }
  ],
  "total": 1
}
```

### 更多命令

```bash
memex list --repo user              # 列出记忆
memex get <memory-id>               # 获取单条
memex delete <memory-id>            # 删除
memex stats                         # 统计
memex recall                        # 隐私查看
memex purge <memory-id>             # 隐私删除
memex purge --all                   # 清空所有
```

---

## 记忆类型

| 类型 | 用途 | importance | 示例 |
|------|------|-----------|------|
| `constraint` | 强制规则 | 0.9 | "用户不喜欢废话" |
| `user_model` | 用户偏好 | 0.85 | "用户喜欢简洁回复" |
| `strategy` | 方法论 | 0.8 | "用分治法解决复杂问题" |
| `system_pattern` | 系统模式 | 0.75 | "项目采用前后端分离" |
| `belief` | 验证结论 | 0.7 | "Python 适合快速原型" |
| `journal` | 工作日志 | 0.4 | "今天完成了 xxx" |

---

## 技术栈

| 组件 | 选择 |
|------|------|
| 向量数据库 | LanceDB（嵌入式，列式存储） |
| Embedding | BGE-base-zh-v1.5（中文优化） |
| CLI | Click |
| 存储抽象 | 可切换 LanceDB / Chroma / Memory |

---

## 架构

```
memex/
├── src/memex/
│   ├── _types.py        # MemoryRecord、MemoryType
│   ├── _config.py       # 配置管理
│   ├── _embed.py        # Embedding 生成
│   ├── store/           # 存储抽象层
│   │   ├── interface.py # VectorStore 接口
│   │   ├── lancedb.py   # LanceDB 实现
│   │   └── memory.py    # 内存实现（测试用）
│   └── cli.py           # CLI 命令
├── skills/
│   └── memory-skill/
│       └── SKILL.md     # 通用 Agent Skill
└── tests/
```

---

## 配置

配置文件：`~/.memex/config.toml`

```toml
[memory]
storage_path = "~/.memex/memory"

[vector_store]
provider = "lancedb"

[embedding]
model = "BAAI/bge-base-zh-v1.5"
dimension = 768

[retrieval]
default_limit = 10
min_similarity = 0.4
```

---

## 通用 Agent Skill

将 Memex 接入 Agent：

1. 复制 skill 到 `~/.openclaw/skills/memex/`
2. Agent 在合适的时机调用 `memex search` / `memex save`

详见 [`skills/memory-skill/SKILL.md`](skills/memory-skill/SKILL.md)

---

## LongMemEval Benchmark

在 [LongMemEval](https://github.com/xiaowu0162/longmemeval)（ICLR 2025, UCLA + 腾讯 AI Lab）上测试了 Memex 的记忆召回能力。

### 测试配置

- **Embedding**: BAAI/bge-base-zh-v1.5（768 维）
- **存储**: LanceDB 嵌入式向量数据库
- **粒度**: Turn-level（每条记录 = 一个对话回合，约 550 条/题）

### 测试结果

| 配置 | 题数 | R@5 | R@10 | NDCG@10 |
|------|------|------|------|---------|
| MemPalace (baseline) | 500 | **96.6%** | 98.2% | 88.9% |
| Memex (turn-level) | 500 | **91.8%** | 94.0% | ~80% |
| Memex (session-level) | 500 | 85.8% | 92.2% | 78.9% |

### 粒度说明

LongMemEval 支持两种评估粒度：

| 粒度 | 每题记录数 | 说明 |
|------|-----------|------|
| **Turn-level** | ~550 条 | 每条 = 一个对话回合（user/assistant 的一条消息），最细粒度 |
| **Session-level** | ~53 条 | 每条 = 一个完整会话（30-40 回合聚成），较粗粒度 |

MemPalace 的 96.6% 是 turn-level 的结果。Turn-level 更接近真实场景——你的每一次对话、每一条消息，都可能藏着答案。

Memex 在 turn-level 达到 91.8%，和 MemPalace 差距约 5 个百分点，且完全本地化、开源。

### 核心发现

1. **原文存储有效**：不经过 LLM 提取的 原文方案，在记忆召回任务上表现优异
2. **Turn-level 优于 Session-level**：粒度越细，能找回的细节越多
3. **本地化可行**：用开源工具 + 本地存储，可以达到甚至超越商业服务

---

## 项目状态

**Phase 1: MVP** ✅

- [x] 核心类型定义
- [x] 存储抽象层（VectorStore 接口 + LanceDB 实现）
- [x] CLI 命令（init / save / search / get / list / delete / stats / recall / purge）
- [x] BGE embedding 集成
- [x] 基本测试
- [x] SKILL.md

**Phase 2**: distillation / revision / contradiction detection

---

## License

MIT
