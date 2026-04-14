# Memex 测试策略（草案）

> 创建时间：2026-04-14
> 状态：草稿，待完善

---

## 测试分层

### Level 1: 单元测试（客观可测）

每个组件单独测，输入输出明确。

| 组件 | 测什么 | 怎么测 |
|------|--------|--------|
| `distillation` | 过滤逻辑 | 垃圾内容 → 验证拒绝；有效内容 → 验证接受 |
| `scoring` | 混合评分公式 | 固定向量/importance/freshness → 验证公式输出 |
| `decay` | 衰减计算 | 模拟 X 天未访问 → 验证 decay 值 |
| `consolidate` | 相似合并 | 两条近似记忆 → 验证合并逻辑 |
| `search` | 检索结果排序 | 存 N 条 → 搜索 → 验证 score 递减 |

**覆盖目标：100% 覆盖核心逻辑**

---

### Level 2: 功能测试（黑盒端到端）

整体流程验证。

**核心测试集：**

```
测试集 A: 检索准确性
- 存入 100 条不同类型记忆
- 用 query 搜索
- 验证前 5 条包含期望记忆
- 重复 N 次，取命中率

测试集 B: 遗忘效果
- 存入 50 条记忆
- 7 天不访问
- 执行 decay
- 验证 decay 值上升
- 验证新鲜记忆排名更高
```

---

### Level 3: 模拟 Agent 测试（最关键）

模拟真实 Coding Agent 使用场景。

```
场景：模拟 Coding Agent 的 10 次对话

Session 1:
  - 对话：用户说"我喜欢用中文交流，回复要简洁"
  - memex save → 存入 user_model
  
Session 2（1小时后）:
  - 用户说"帮我 review 这段代码"
  - memex search "用户偏好"
  - 验证返回包含"中文交流"
  
Session 3-10:
  - 继续模拟不同话题
  - 每个 session 结束时自动存记忆
  
最终验证：
  - 第 10 次 session 搜索"用户的沟通风格"
  - 是否能回忆 Session 1 的偏好？
  - 是否能回忆中间提到的项目架构？
```

**衡量指标：**
- Recall@5：前 5 条结果里有多少真正相关
- Mean Reciprocal Rank（MRR）：第一个相关结果的位置
- 记忆持久性：存入后 N 天还能不能搜到

---

### Level 4: 人工评估（主观质量）

定期抽样人工 review。

```
每月随机抽取 20 条记忆，人工评估：
- 这条记忆有没有价值？
- 内容是否准确？
- 类型标注是否正确？
- 有没有矛盾？

打分：0-10
```

---

## 测试数据设计

准备 Golden Test Set：

```
tests/fixtures/golden_memories/
├── constraints.json    # 10 条 constraint，附预期 importance
├── user_models.json   # 10 条 user_model
├── strategies.json    # 10 条 strategy
├── beliefs.json       # 10 条 belief
└── garbage.json       # 10 条应被 distillation 拒绝的垃圾
```

**测试流程：**
1. 清空测试数据库
2. 逐条存入 golden_memories
3. 搜索验证

---

## 测试文件结构

```
tests/
├── conftest.py                 # pytest fixtures
├── test_distillation.py        # Level 1
├── test_scoring.py            # Level 1
├── test_decay.py              # Level 1
├── test_consolidate.py        # Level 1
├── test_search.py              # Level 2
├── fixtures/
│   └── golden_memories/       # 测试数据集
└── cassettes/                 # 录制的 API 响应（如有外部调用）
```

---

## 待完善

- [ ] 补充 Level 3 模拟 Agent 的具体对话脚本
- [ ] 制定 Recall@5 的具体阈值（暂定 > 0.7）
- [ ] 制定 MRR 的具体阈值（暂定 > 0.6）
- [ ] 设计"记忆持久性"测试的时间加速方案（跳过 7 天等待）
- [ ] Level 4 人工评估的抽样规则
