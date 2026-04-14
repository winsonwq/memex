# LongMemEval Benchmark 复现指南

本文档说明如何在本地复现 Memex 的 LongMemEval 测评。

## 环境准备

### 1. 安装依赖

```bash
pip install -e .
```

需要 Python >= 3.10。

### 2. 下载数据集

```bash
mkdir -p /tmp/longmemeval-data
cd /tmp/longmemeval-data

# 如果网络不通，需要设置代理
export https_proxy="http://你的代理地址:端口"
export http_proxy="http://你的代理地址:端口"

wget https://huggingface.co/datasets/xiaowu0162/longmemeval-cleaned/resolve/main/longmemeval_s_cleaned.json
```

数据集约 265MB。

### 3. 配置代理（如需要）

如果下载 HuggingFace 模型时网络不通，需要设置代理：

```bash
export https_proxy="http://你的代理地址:端口"
export http_proxy="http://你的代理地址:端口"
```

## 快速测试（10 题）

先跑 10 题验证环境没问题：

```bash
cd /home/aqiu/.openclaw/workspace/memex

# Turn-level
bash benchmarks/run_turn_10.sh

# Session-level
bash benchmarks/run_10.sh
```

预期输出：
- Turn-level 10题: R@5 ≈ 1.000
- Session-level 10题: R@5 ≈ 0.600

## 完整测试（500 题）

### Turn-level（回合级）

每题 ~550 条记录（每条 = 一个对话回合），挑战最大，最接近真实场景。

```bash
cd /home/aqiu/.openclaw/workspace/memex

# 500 题，约 90 分钟
bash benchmarks/run_turn_500.sh

# 或手动运行
python3 -u benchmarks/memex_bench_turn_level.py \
    /tmp/longmemeval-data/longmemeval_s_cleaned.json \
    --limit 500 \
    --batch-gc 10
```

**预期结果**：
- R@5 ≈ 0.918
- R@10 ≈ 0.940
- NDCG@10 ≈ 0.80
- 耗时约 90 分钟

### Session-level（会话级）

每题 ~53 条记录（每条 = 一个完整会话），较粗粒度。

```bash
cd /home/aqiu/.openclaw/workspace/memex

# 500 题，约 37 分钟
bash benchmarks/run_full_500.sh

# 或手动运行
python3 -u benchmarks/memex_bench.py \
    /tmp/longmemeval-data/longmemeval_s_cleaned.json \
    --limit 500 \
    --batch-gc 10
```

**预期结果**：
- R@5 ≈ 0.858
- R@10 ≈ 0.922
- NDCG@10 ≈ 0.789
- 耗时约 37 分钟

## 粒度说明

| 粒度 | 每题记录数 | 说明 |
|------|-----------|------|
| **Turn-level** | ~550 条 | 每条 = 一个对话回合（user 或 assistant 的一条消息） |
| **Session-level** | ~53 条 | 每条 = 一个完整会话（30-40 回合聚成一个 session） |

粒度越细，数据量越大（10 倍差距），挑战也越大。MemPalace 的 96.6% 是 turn-level 的结果。

## 内存优化

脚本内置了两层内存优化：

1. **文本截断**：每条记录最多 200 字符（turn-level）或 500 字符（session-level）
2. **批处理 GC**：每 N 题强制 `gc.collect()`

如果内存不够，可以调小 batch-gc：

```bash
python3 -u benchmarks/memex_bench_turn_level.py \
    /tmp/longmemeval-data/longmemeval_s_cleaned.json \
    --limit 500 \
    --batch-gc 5  # 更频繁 GC，内存更省
```

## 结果解读

脚本会输出和 MemPalace baseline 的对比：

```
Comparison with MemPalace (turn-level baseline):
  MemPalace:  Recall@5 = 0.966
  Memex:      Recall@5 = 0.9180
  Delta:      -0.0480
```

- **R@5**：正确答案出现在前 5 个检索结果里的概率
- **Delta**：和 MemPalace 的差距（越小越好）

## 项目结构

```
benchmarks/
├── memex_bench.py              # Session-level benchmark
├── memex_bench_turn_level.py  # Turn-level benchmark
├── run_10.sh                  # 10题快速测试
├── run_turn_10.sh             # Turn-level 10题
├── run_turn_50.sh             # Turn-level 50题
├── run_turn_500.sh            # Turn-level 500题
└── run_full_500.sh           # Session-level 500题
```
