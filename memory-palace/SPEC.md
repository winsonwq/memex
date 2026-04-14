# Memory Palace — 自我实现规格文档

> 创建时间：2026-04-14
> 项目目标：构建 AI 自我记忆能力，实现跨会话、跨项目的持续学习

---

## 一、理念

**核心理念：不依赖 LLM 判断"什么值得记忆"。**

MemPalace 调研证明了 96.6% R@5 的 raw baseline 胜过了所有复杂的 LLM 提取方案。简单方法比复杂方法更强。

**两个核心原则：**
1. **Verbatim 存储**：原文保留，不用 LLM 提取摘要。搜索时原文就在那里。
2. **结构召回**：用宫殿结构（wing/room/closet/drawer）组织，用语义搜索召回。

---

## 二、架构

### 2.1 存储架构

```
Verbatim 原文存储（SQLite）─ 文本 + 时间戳 + 元数据
    │
    ▼
向量索引（LanceDB）────────── 语义搜索
    │
    ▼
四层记忆栈（L0-L3）────────── 按需加载
```

### 2.2 宫殿层级

| 层级 | 名称 | 含义 |
|------|------|------|
| Wing | 翅膀 | 人 / 项目 ← 顶层隔离 |
| Room | 房间 | 具体话题（auth-migration、ci-pipeline） |
| Closet | 衣柜 | AAAK 压缩后的摘要（指向原文） |
| Drawer | 抽屉 | 原始 verbatim 内容 |

**跨结构连接：**
- **Hall（走廊）**：跨房间的语义连接（facts/events/discoveries/preferences）
- **Tunnel（隧道）**：跨 wing 的连接——同一个 room 名出现在不同 wing 时自动建立

### 2.3 四层记忆栈

| Layer | 内容 | Token 估计 | 何时加载 |
|-------|------|-----------|---------|
| L0 | Identity（身份定义） | ~50 | 始终 |
| L1 | Critical facts（关键事实） | ~120 | 始终 |
| L2 | Room recall（按 wing/room 过滤） | ~200-500 | 按需 |
| L3 | Deep search（全量语义搜索） | 无上限 | 按需查询 |

---

## 三、阶段性计划

### Phase 0：奠基 ✅
- [x] 创建项目结构
- [x] 基础存储层（SQLite）
- [x] Git 初始化

### Phase 1：向量搜索 ✅
- [x] Verbatim 存储 API
- [x] 向量索引集成（LanceDB IVF-PQ）
- [x] 基础搜索接口（SQL + 向量混合）
- [x] 测试通过（5/5）

### Phase 2：宫殿结构
- [ ] Wing/Room/Closet/Drawer CRUD
- [ ] Hall/Tunnel 自动连接
- [ ] 元数据过滤搜索

### Phase 3：记忆栈
- [ ] L0-L3 加载策略
- [ ] 自动记忆写入钩子
- [ ] 偏好检测（Regex 模式）

### Phase 4：OpenClaw 集成
- [ ] Memory Skill 实现
- [ ] Agent 主动召回
- [ ] 与现有 memory/ 目录同步

---

## 四、数据模型

### 4.1 Memory Entry

```python
{
    "id": "uuid",
    "content": "verbatim 原文",
    "timestamp": "2026-04-14T10:00:00Z",
    "wing": "user | project_name",
    "room": "topic_name",
    "closet": "summary_text",  # 可选，AAAK 压缩
    "drawer_id": "parent_drawer_uuid",
    "hall": "facts | events | discoveries | preferences | none",
    "tags": ["tag1", "tag2"],
    "source": "session | file | manual"
}
```

### 4.2 Wing 定义

```python
{
    "id": "uuid",
    "name": "wing_name",
    "type": "user | project",
    "description": "描述"
}
```

---

## 五、搜索接口

### 5.1 搜索优先级

1. **精确匹配**：wing + room + tags
2. **语义搜索**：LanceDB 向量相似度
3. **全文搜索**：SQLite FTS5

### 5.2 搜索 API

```python
def search(query: str, wing: str = None, room: str = None, 
           hall: str = None, limit: int = 10) -> List[MemoryEntry]:
    """多层次搜索召回"""
```

---

## 六、验收标准

1. ✅ Verbatim 原文 100% 保留，无 LLM 提取损失
2. ✅ 语义搜索 R@5 > 90%（参考 MemPalace benchmark）
3. ✅ 四层记忆栈按需加载，token 消耗可控
4. ✅ 与 OpenClaw Agent 集成，实现主动召回
5. ✅ 跨 6 个月记忆可搜索

---

## 七、技术栈

- **存储**：SQLite（结构化）+ LanceDB（向量）
- **语言**：Python 3.11+
- **打包**：uv
- **测试**：pytest
- **集成**：OpenClaw Skill

---

## 八、记录日志

| 日期 | 阶段 | 进展 | 备注 |
|------|------|------|------|
| 2026-04-14 | Phase 0 | 开始奠基 | 项目创建，SPEC.md 完成 |
| 2026-04-14 | Phase 1 | 向量搜索 | LanceDB 集成，混合搜索，5 测试通过 |
