#!/usr/bin/env python3
"""
Memex × LongMemEval Benchmark
================================

评估 Memex 的检索能力，对标 MemPalace。

优化记录：
1. Session 级别聚合：每题 ~53 条记录 vs ~550 条（减少 90% 数据量）
2. 文本截断：每条记录最多 500 字符
3. 强制 GC：每题处理完立即释放内存
4. 批处理：每 10 题强制 gc.collect()

MemPalace 参考：
- Raw ChromaDB (verbatim): R@5 = 96.6%
- LongMemEval: 500 questions, ~53 sessions per question
"""
import json
import sys
import math
import time
import gc
sys.path.insert(0, '/home/aqiu/.openclaw/workspace/memex/src')

from memex._embed import embed_texts
from memex.store.memory import MemoryStore
from memex._types import MemoryRecord, MemoryType


# =============================================================================
# METRICS
# =============================================================================

def dcg(relevances, k):
    score = 0.0
    for i, rel in enumerate(relevances[:k]):
        score += rel / math.log2(i + 2)
    return score

def ndcg(rankings, correct_ids, corpus_ids, k):
    relevances = [1.0 if corpus_ids[idx] in correct_ids else 0.0 for idx in rankings[:k]]
    ideal = sorted(relevances, reverse=True)
    idcg = dcg(ideal, k)
    if idcg == 0:
        return 0.0
    return dcg(relevances, k) / idcg

def evaluate_retrieval(rankings, correct_ids, corpus_ids, k):
    top_k_ids = set(corpus_ids[idx] for idx in rankings[:k])
    recall_any = float(any(cid in top_k_ids for cid in correct_ids))
    recall_all = float(all(cid in top_k_ids for cid in correct_ids))
    ndcg_score = ndcg(rankings, correct_ids, corpus_ids, k)
    return recall_any, recall_all, ndcg_score


# =============================================================================
# DATA LOADING & PREPROCESSING
# =============================================================================

def load_data(path):
    """加载 LongMemEval 数据集"""
    with open(path) as f:
        return json.load(f)


def flatten_sessions_session_level(haystack_sessions, session_ids):
    """
    Session 级别聚合（优化点 1）
    
    每题 ~53 sessions × 1 record = ~53 条记录
    vs turn 级别 ~550 条记录（减少 90%）
    
    每个 session 的所有 turns 拼接为一个 record
    """
    records = []
    
    for sess_idx, session in enumerate(haystack_sessions):
        sess_id = session_ids[sess_idx] if sess_idx < len(session_ids) else f"sess_{sess_idx}"
        
        # 拼接 session 内所有 turns
        combined_content = []
        for turn in session:
            if isinstance(turn, dict):
                content = turn.get("content", "")
                if content:
                    combined_content.append(content[:200])  # 每条截断到 200 字符
        
        if combined_content:
            # 合并内容，最多 500 字符
            full_content = " ".join(combined_content)[:500]
            records.append(MemoryRecord(
                type=MemoryType.BELIEF,
                content=full_content,
                raw_text=full_content,
                repo="bench",
                metadata={"session_id": sess_id}
            ))
    
    return records


# =============================================================================
# BENCHMARK
# =============================================================================

def run_item(item, warmup_done):
    """单题处理"""
    question = item["question"]
    haystack_sessions = item.get("haystack_sessions", [])
    haystack_session_ids = item.get("haystack_session_ids", [])
    answer_sessions = item.get("answer_session_ids", [])
    
    if not haystack_sessions:
        return None
    
    # Session 级别聚合
    records = flatten_sessions_session_level(haystack_sessions, haystack_session_ids)
    
    if not records:
        return None
    
    # 创建 store
    store = MemoryStore()
    texts = [r.content for r in records]
    
    # Embedding（使用缓存的模型）
    vectors = embed_texts(texts)
    
    # 添加到 store
    for record, vector in zip(records, vectors):
        store.add(record, vector)
    
    # 搜索
    query_vec = embed_texts([question])[0]
    results, _ = zip(*store.search(query_vec, limit=10))
    
    # 构建 corpus
    corpus_ids = [r.metadata.get("session_id", r.id) for r in results]
    rankings = list(range(len(results)))
    
    # 计算 metrics
    r5_any, r5_all, n5 = evaluate_retrieval(rankings, answer_sessions, corpus_ids, 5)
    r10_any, r10_all, n10 = evaluate_retrieval(rankings, answer_sessions, corpus_ids, 10)
    
    # 强制释放内存（优化点 3）
    del store
    del records
    del texts
    del vectors
    del results
    
    return {
        "r5": r5_any,
        "r10": r10_any,
        "r10_all": r10_all,
        "ndcg10": n10,
        "records": len(records) if 'records' in locals() else 0
    }


def run_benchmark(data, limit=None, batch_gc=10):
    """
    运行 benchmark
    
    Args:
        data: LongMemEval 数据
        limit: 限制题目数量
        batch_gc: 每 N 题强制 GC（优化点 4）
    """
    if limit:
        data = data[:limit]
    
    n = len(data)
    r5_sum, r10_sum, r10_all_sum, ndcg_sum = 0, 0, 0, 0
    valid = 0
    warmup_done = False
    
    start = time.time()
    
    for i in range(n):
        elapsed = time.time() - start
        eta = (elapsed / (i + 1)) * (n - i - 1) if i > 0 else 0
        r5_current = r5_sum / valid if valid > 0 else 0.0
        
        # 预热模型
        if not warmup_done:
            print(f"  Warming up embedding model...")
            _ = embed_texts(["warmup"])
            warmup_done = True
        
        print(f"\r[{i+1}/{n}] {elapsed:.1f}s | ETA: {eta:.0f}s | R@5: {r5_current:.3f}", end="", flush=True)
        
        result = run_item(data[i], warmup_done)
        
        if result:
            r5_sum += result["r5"]
            r10_sum += result["r10"]
            r10_all_sum += result["r10_all"]
            ndcg_sum += result["ndcg10"]
            valid += 1
        
        # 批处理 GC（优化点 4）
        if (i + 1) % batch_gc == 0:
            gc.collect()
    
    elapsed = time.time() - start
    
    return {
        "recall@5": r5_sum / valid if valid > 0 else 0,
        "recall@10": r10_sum / valid if valid > 0 else 0,
        "recall@10_all": r10_all_sum / valid if valid > 0 else 0,
        "ndcg@10": ndcg_sum / valid if valid > 0 else 0,
        "count": valid,
        "total": n,
        "elapsed": elapsed,
    }


# =============================================================================
# MAIN
# =============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("data", help="Path to longmemeval_s_cleaned.json")
    parser.add_argument("--limit", type=int, default=None, help="Limit questions")
    parser.add_argument("--batch-gc", type=int, default=10, help="GC every N items")
    args = parser.parse_args()
    
    print("=" * 60)
    print("Memex × LongMemEval Benchmark")
    print("=" * 60)
    print()
    print("Optimizations applied:")
    print("  1. Session-level aggregation (~53 records vs ~550)")
    print("  2. Text truncation (500 chars max)")
    print("  3. Forced memory release after each item")
    print("  4. Batch GC every 10 items")
    print()
    
    # 加载数据
    print(f"Loading data from {args.data}...")
    data = load_data(args.data)
    print(f"Loaded {len(data)} questions")
    
    if args.limit:
        print(f"Limited to {args.limit} questions")
    
    # 运行
    print()
    results = run_benchmark(data, limit=args.limit, batch_gc=args.batch_gc)
    
    # 输出
    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Questions:      {results['count']}/{results['total']}")
    print(f"Recall@5:      {results['recall@5']:.4f}")
    print(f"Recall@10:     {results['recall@10']:.4f}")
    print(f"Recall@10(all):{results['recall@10_all']:.4f}")
    print(f"NDCG@10:       {results['ndcg@10']:.4f}")
    print(f"Time:          {results['elapsed']:.1f}s")
    print("=" * 60)
    
    # 对标 MemPalace
    print()
    print("Comparison with MemPalace (raw mode):")
    print(f"  MemPalace:  Recall@5 = 0.966")
    print(f"  Memex:      Recall@5 = {results['recall@5']:.4f}")
    print(f"  Delta:      {results['recall@5'] - 0.966:+.4f}")
    print()
    print("Note: MemPalace uses turn-level granularity (550 records/question)")
    print("      Memex uses session-level granularity (~53 records/question)")
    print("      This is a different experimental setup!")


if __name__ == "__main__":
    main()
