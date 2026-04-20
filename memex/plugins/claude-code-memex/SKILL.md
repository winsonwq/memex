---
name: memex
description: Agent 长期记忆系统。memex-plugin 已自动保存工具调用记忆。当用户查询"之前..."、"上次..."、"我记得..."时，使用 memex search 查询记忆。
---

# Memex — Agent 长期记忆

memex-plugin 自动记录每次工具调用和会话摘要。记忆通过向量相似度 + 重要性 + 新鲜度 + 频率混合评分。

## 何时使用

- 用户问"之前怎么处理这个问题"
- 用户说"我记得上次..."
- 用户说"上次你说过..."

## 命令

```bash
# 语义搜索记忆（推荐）
memex search "查询内容" --repo claude-code --limit 5

# 列出最近记忆
memex list --repo claude-code --limit 10

# 手动保存重要信息
memex save --type <type> --content "内容" --repo claude-code
```

## 记忆类型

| 类型 | 用途 |
|------|------|
| `constraint` | 用户强制的规则 |
| `user_model` | 用户偏好 |
| `strategy` | 方法论 |
| `system_pattern` | 系统模式 |
| `belief` | 验证过的结论 |
| `journal` | 工作日志（自动保存） |
