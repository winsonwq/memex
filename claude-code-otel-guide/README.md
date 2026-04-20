# Claude Code + OpenTelemetry + Jaeger 追踪指南

## 概述

Claude Code 原生支持 OTel 导出，trace 数据通过两条路径汇入 Jaeger：

```
Claude Code ──→ OTel ──────────────────────────→ Jaeger
                ↑
                │ (skill/tool 细节)
Claude Code ──→ relay ──→ OTel ──────────────→ Jaeger
                ↑
                └── hooks
```

- **主路**：Claude Code 原生 OTel → Jaeger（session、interaction、llm_request 等高层 spans）
- **岔路**：relay 接收 hooks 事件 → 细粒度 skill/tool 调用 → Jaeger（skill 嵌套、token 消耗等）

两条路径共享同一个 Jaeger service，数据互补便于完整分析。

![Jaeger Overview](/claude-code-otel-guide/jaeger-overview.png)

---

## 安装

### Claude Code CLI

下载并安装 Claude Code CLI：

```bash
# macOS/Linux
curl -sL https://artifacts.claudecode.com | bash

# 或下载二进制
curl -sL https://artifacts.claudecode.com/Darwin/claude-enterprise.tar.gz -o claude.tar.gz
tar -xzf claude.tar.gz
mv claude /usr/local/bin/claude
```

验证安装：

```bash
claude --version
```

### Jaeger（Docker）

```bash
docker run -d --name jaeger \
  -e COLLECTOR_OTLP_ENABLED=true \
  -p 16686:16686 \
  -p 4317:4317 \
  -p 4318:4318 \
  jaegertracing/all-in-one:latest
```

安装后访问 http://127.0.0.1:16686

### relay（可选）

```bash
git clone https://github.com/winsonwq/claude-agent-hook-relay.git
cd claude-agent-hook-relay
npm install
npm run build
```

---

## 配置

### 主路：Claude Code 原生 OTel

设置环境变量：

```bash
# Claude Code OTel 开关（缺一不可）
export CLAUDE_CODE_ENABLE_TELEMETRY=true
export CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=true

# OTel 导出配置
export OTEL_TRACES_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_TRACES_PROTOCOL=http/json
export OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4318
export OTEL_SERVICE_NAME=claude-code
```

**关键**：`CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=true` 是真正的开关，没有它 trace exporter 不会初始化。

源码中控制 trace 是否启用的函数：

```js
Fl8(){
    let H=process.env.CLAUDE_CODE_ENHANCED_TELEMETRY_BETA 
         ?? process.env.ENABLE_ENHANCED_TELEMETRY_BETA;
    if(hH(H))return!0;  // "true" -> 启用
    if(i_(H))return!1;  // "false" -> 禁用
    return!1             // 未设置 -> 禁用（默认）
}
```

### 岔路：relay（可选）

启动 relay：

```bash
# 默认 service name 为 'claude-code'（与主路合并）
RELAY_OTEL_URL=http://127.0.0.1:4318/v1/traces node dist/index.js

# 自定义 service name
RELAY_OTEL_URL=http://127.0.0.1:4318/v1/traces \
RELAY_OTEL_SERVICE_NAME=claude-code \
node dist/index.js
```

在 `~/.claude/settings.json` 中配置 hooks：

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "*",
      "hooks": [{
        "type": "http",
        "url": "http://localhost:8080/hook/post-tool-use",
        "timeout": 10
      }]
    }]
  }
}
```

relay 默认监听 `http://localhost:8080`。

---

## 查看 Trace 数据

### Jaeger UI

打开浏览器访问 http://127.0.0.1:16686

1. **选择 Service**：左侧面板选择 `claude-code`
2. **查找 Trace**：点击 "Find Traces"
3. **查看结构**：点击某条 trace 查看 spans 树形结构

![Trace Tree](/claude-code-otel-guide/jaeger-trace-tree.png)

### API 查询

```bash
# 列出所有 services
curl -s "http://127.0.0.1:16686/api/services" | jq '.data'

# 查询某个 service 的 traces
curl -s "http://127.0.0.1:16686/api/traces?service=claude-code" | jq '.'

# 查询最新 trace
curl -s "http://127.0.0.1:16686/api/traces?service=claude-code" | jq '.data[0]'
```

### 端口说明

| 端口 | 协议 | 用途 |
|------|------|------|
| 16686 | HTTP | Jaeger Web UI |
| 4317 | gRPC | OTLP gRPC 接收 |
| 4318 | HTTP | OTLP HTTP/JSON 接收 |

---

## 快速启动

### 完整链路（主路 + 岔路）

```bash
# 1. 启动 Jaeger
docker run -d --name jaeger \
  -e COLLECTOR_OTLP_ENABLED=true \
  -p 16686:16686 -p 4317:4317 -p 4318:4318 \
  jaegertracing/all-in-one:latest

# 2. 启动 relay（岔路）
cd claude-agent-hook-relay
RELAY_OTEL_URL=http://127.0.0.1:4318/v1/traces node dist/index.js &

# 3. 设置环境变量（主路）
export CLAUDE_CODE_ENABLE_TELEMETRY=true
export CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=true
export OTEL_TRACES_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_TRACES_PROTOCOL=http/json
export OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4318
export OTEL_SERVICE_NAME=claude-code

# 4. 运行 Claude Code
claude -p "use nested-test-skill"

# 5. 查看结果（打开 http://127.0.0.1:16686，选择 service: claaude-code）
```

### 仅主路（仅 CLI 原生 OTel）

```bash
# 1. 启动 Jaeger
docker run -d --name jaeger \
  -e COLLECTOR_OTLP_ENABLED=true \
  -p 16686:16686 -p 4317:4317 -p 4318:4318 \
  jaegertracing/all-in-one:latest

# 2. 设置环境变量
export CLAUDE_CODE_ENABLE_TELEMETRY=true
export CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=true
export OTEL_TRACES_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_TRACES_PROTOCOL=http/json
export OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4318
export OTEL_SERVICE_NAME=claude-code

# 3. 运行 Claude Code
claude -p "say hello"

# 4. 查看结果
# 浏览器打开 http://127.0.0.1:16686
```

### 仅岔路（仅 relay skill 链）

```bash
# 1. 启动 Jaeger（同上）

# 2. 启动 relay
cd claude-agent-hook-relay
RELAY_OTEL_URL=http://127.0.0.1:4318/v1/traces node dist/index.js &

# 3. 运行 Claude Code（会自动发送 hook 事件到 relay）
claude -p "use nested-test-skill"

# 4. 查看结果
# 浏览器打开 http://127.0.0.1:16686
```
