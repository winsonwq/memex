# AGENTS.md — Memex 代码库索引

## 文档索引

| 文档 | 路径 | 说明 |
|------|------|------|
| 设计对比 | `docs/comparison.md` | Memex vs MemPalace 完整对比分析 |
| Benchmark 文章草稿 | `docs/longmemeval-benchmark-article.md` | 微信公众号文章 |
| Benchmark 方法 | `benchmarks/README.md` | LongMemEval 复现指南 |
| Benchmark 运行记录 | `benchmarks/RUN-2026-04-14.md` | 实际运行结果 |

## 规则

- 在 `docs/` 目录下新增文档时，必须在本文档「文档索引」表格中添加对应条目
- 索引内容包含：文档用途简要说明 + 路径

## 项目结构

```
memex/
├── memex/              # 核心包
├── tests/              # 测试（112 个测试用例）
├── benchmarks/         # LongMemEval benchmark
├── docs/               # 文档
└── AGENTS.md           # 本文件
```
