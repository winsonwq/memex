# Memex — Agent 记忆系统

> 用嵌入式向量数据库实现轻量级 Agent 记忆系统，以 CLI + Skill 的形式交付。

## 一句话

**Memex 让 Agent 记住一切，实现跨会话的持续学习。**

---

## 特性

- **Verbatim 存储** — 原文保留，不依赖 LLM 提取摘要
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
│       └── SKILL.md     # OpenClaw Skill
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

## OpenClaw Skill

将 Memex 接入 Agent：

1. 复制 skill 到 `~/.openclaw/skills/memex/`
2. Agent 在合适的时机调用 `memex search` / `memex save`

详见 [`skills/memory-skill/SKILL.md`](skills/memory-skill/SKILL.md)

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
