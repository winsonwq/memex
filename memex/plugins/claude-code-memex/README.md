# memex-plugin

Claude Code 插件：自动保存工具调用记忆，SessionStart 时注入相关上下文。

## 功能

- **自动存档**：Bash/Edit/Write/Read 调用后自动保存到 memex
- **上下文注入**：SessionStart 时搜索相关记忆，注入为 Claude 可见 context
- **会话摘要**：SessionEnd 时保存会话摘要

## 安装

```bash
# 1. 安装 memex
pip install memex-agent-memory

# 2. 初始化
memex init

# 3. 安装 Claude Code 插件
memex install-plugin claude-code
```

## 卸载

```bash
rm ~/.claude/plugins/memex
```

## 验证

重启 Claude Code 后，运行：

```
/plugin list
```

应该看到 `memex-plugin`。

## 钩子说明

| 钩子 | 触发时机 | 操作 |
|------|---------|------|
| `SessionStart` | 会话开始/恢复 | memex search → 注入 context |
| `PostToolUse` | Bash/Edit/Write/Read 执行后 | memex save（异步） |
| `SessionEnd` | 会话结束 | 保存会话摘要 |
