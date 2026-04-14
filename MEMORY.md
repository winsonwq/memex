# MEMORY.md — 长期记忆入口

## 结构

- **每日笔记**：`memory/YYYY-MM-DD.md`
- **归档内容**：标注了归档日期的旧记忆
- **索引**：下面按主题列出所有记忆文件的索引

## 索引

- [Memory Palace 自我实现](memory-palace/) — AI 记忆系统 Phase 1 完成，LanceDB 向量搜索、SQL/向量混合搜索
- [Memex 项目](memex/) — Agent 记忆基础设施 CLI + Skill，Phase 1 MVP 完成，存储抽象层 + CLI 骨架
- [MemPalace 记忆宫殿调研](memory/mempalace-research/2026-04-09-调研报告.md) — AI 记忆系统深度分析，96.6% R@5 raw baseline，宫殿结构 + ChromaDB
- [📦 types/ 归档 2026-04-10](memory/2026-04-10-memory-types-归档.md) — 归档：旧 types/ 目录合并（用户信息、反馈记录、项目总览、资源索引）

## 写入规范

每次需要记忆时，直接写到 `memory/YYYY-MM-DD.md`。
如果内容重要且跨多天，在 MEMORY.md 加一行索引。

## 什么不该记

- 代码模式、架构、约定（代码里有，grep 能找到）
- Git 历史
- 调试方案（fix 在代码里）
- 临时任务细节（日记里有）
- CLAUDE.md / SOUL.md / IDENTITY.md 已有的内容

**核心原则**：只记「不可推导」的信息。
