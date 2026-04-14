---
name: memex
description: Agent 长期记忆系统。用于跨会话积累知识和偏好。支持自然语言搜索、六种记忆类型分类、隐私控制。当需要记住关键信息、查询用户偏好、检索决策依据时使用。
install:
  - pip install memex-agent-memory
  - memex init
requires:
  commands: [memex]
---

# Memex Skill — 通用 Agent 记忆系统

## 简介

Memex 是 Agent 的长期记忆系统，让 Agent 能在跨会话中积累知识和偏好。

**通用设计**：任何 Agent 框架都可以接入（OpenClaw、Claude Code、Cursor、Codex 等）。

**核心理念**：
- 原文存储 — 原文保留，不依赖 LLM 提取
- 向量语义搜索 — 支持自然语言查询
- 隐私可控 — 用户可随时查看、删除记忆

---

## 何时使用

| 时机 | 命令 | 说明 |
|------|------|------|
| 对话结束 | `memex save` | 提炼关键信息存入记忆 |
| 新对话开始 | `memex search` | 检索相关记忆 |
| 遇到决策点 | `memex search` | 查询约束/策略 |
| 发现新 pattern | `memex save --type system_pattern` | 存入系统模式 |
| 用户明确偏好 | `memex save --type user_model` | 存入用户偏好 |

---

## 记忆类型

| 类型 | 何时用 | importance | 示例 |
|------|--------|-----------|------|
| `constraint` | 用户强制的规则 | 0.9 | "用户不喜欢废话" |
| `user_model` | 用户偏好/习惯 | 0.85 | "用户喜欢简洁回复" |
| `strategy` | 验证过的方法论 | 0.8 | "用 divide and conquer 解决复杂问题" |
| `system_pattern` | 系统设计模式 | 0.75 | "项目采用前后端分离架构" |
| `belief` | 验证过的结论 | 0.7 | "Python 适合快速原型" |
| `journal` | 工作日志 | 0.4 | "今天完成了 xxx" |

---

## 命令参考

### 存入记忆

```bash
memex save --type <type> --content "<内容>" --repo <namespace>
```

**示例**：
```bash
memex save --type user_model --content "用户喜欢简洁的回复风格，不喜欢废话" --repo user
memex save --type belief --content "这个项目使用 Python FastAPI" --repo myproject
```

### 语义搜索

```bash
memex search "<查询内容>" --repo <namespace> --limit <数量>
```

**示例**：
```bash
memex search "用户的偏好是什么" --repo user --limit 5
```

**返回格式**（JSON，Agent 自行解析）：
```json
{
  "query": "用户的偏好是什么",
  "results": [
    {
      "id": "uuid",
      "type": "user_model",
      "content": "用户喜欢简洁的回复风格，不喜欢废话",
      "importance": 0.85,
      "confidence": 0.8,
      "stability": "medium",
      "score": 0.92
    }
  ],
  "total": 1
}
```

### 其他命令

```bash
# 列出记忆
memex list --repo <namespace> --limit 20

# 获取单条记忆
memex get <memory-id>

# 删除记忆
memex delete <memory-id>

# 查看统计
memex stats --repo <namespace>
```

---

## 隐私控制

用户可以随时查看和删除自己的记忆：

```bash
# 查看被记住的内容
memex recall --repo user

# 删除单条记忆
memex purge <memory-id>

# 清空所有记忆
memex purge --all
```

---

## 混合评分

搜索结果按以下公式排序：

```
final_score = 0.55×similarity + 0.20×importance + 0.15×freshness + 0.10×frequency
```

- `similarity`：向量余弦相似度
- `importance`：记忆类型预设重要性
- `freshness`：最近访问时间
- `frequency`：访问频率

---

## 多 Agent 支持

每个 Agent 用不同的 `--repo` 命名空间：

| Repo | 用途 |
|------|------|
| `user` | 跨 Agent 共享的用户偏好 |
| `<agent-name>` | 特定 Agent 的记忆 |
| `default` | 通用记忆 |

---

## 安装

```bash
# 安装 memex
pip install memex

# 初始化
memex init

# 验证
memex stats
```

### OpenClaw Agent 接入

将 skill 复制到 `~/.openclaw/skills/memex/`，Agent 在合适的时机调用 `memex search` / `memex save`。

### 其他 Agent 框架

直接调用 CLI 命令即可：
```bash
memex search "用户偏好" --repo user --limit 5
```

---

## 注意事项

1. **模型升级兼容**：`raw_text` 字段保存原始文本，换 embedding 模型后自动重建索引
2. **向量维度**：BGE-base-zh-v1.5 = 768 维
3. **存储位置**：`~/.memex/memory/`
4. **网络需求**：首次下载 BGE 模型约 400MB，之后离线可用
