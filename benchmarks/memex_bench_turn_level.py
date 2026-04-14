#!/usr/bin/env python3
"""
Memex × LongMemEval Benchmark (Turn-Level)
==========================================

评估 Memex 的检索能力，对标 MemPalace (R@5 = 96.6%)

Turn-Level: 每题 ~550 条记录（每条 = 一个 turn）
vs Session-Level: ~53 条记录（每条 = 一个 session 拼接）

内存优化：
1. 每条记录截断到 200 字符（减少文本内存）
2. 强制 GC：每题处理完立即释放
3. 批处理 GC：每 5 题强制 gc.collect()
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


def flatten_sessions_turn_level(haystack_sessions, session_ids):
    """
    Turn 级别（每条记录 = 一个 turn）
    
    每题 ~550 条记录
    每条记录最多 200 字符
    """
    records = []
    
    for sess_idx, session in enumerate(haystack_sessions):
        sess_id = session_ids[sess_idx] if sess_idx < len(session_ids) else f"sess_{sess_idx}"
        
        for turn_idx, turn in enumerate(session):
            if isinstance(turn, dict):
                content = turn.get("content", "")
                if content:
                    # 截断到 200 字符（减少内存）
                    truncated = content[:200]
                    turn_id = f"{sess_id}_turn_{turn_idx}"
                    records.append(MemoryRecord(
                        type=MemoryType.BELIEF,
                        content=truncated,
                        raw_text=truncated,
                        repo="bench",
                        metadata={"turn_id": turn_id, "session_id": sess_id}
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
    
    # Turn 级别聚合
    records = flatten_sessions_turn_level(haystack_sessions, haystack_session_ids)
    
    if not records:
        return None
    
    # 创建 store
    store = MemoryStore()
    texts = [r.content for r in records]
    
    # Embedding
    vectors = embed_texts(texts)
    
    # 添加到 store
    for record, vector in zip(records, vectors):
        store.add(record, vector)
    
    # 搜索
    query_vec = embed_texts([question])[0]
    results, _ = zip(*store.search(query_vec, limit=10))
    
    # 构建 corpus - 用 session_id 而不是 turn_id
    # 因为答案是 session 级别的
    corpus_session_ids = [r.metadata.get("session_id", "") for r in results]
    rankings = list(range(len(results)))
    
    # 计算 metrics - 用 session_id 做评估
    r5_any, r5_all, n5 = evaluate_retrieval(rankings, answer_sessions, corpus_session_ids, 5)
    r10_any, r10_all, n10 = evaluate_retrieval(rankings, answer_sessions, corpus_session_ids, 10)
    
    # 强制释放内存
    del store
    del records
    del texts
    del vectors
    del results
    del query_vec
    
    return {
        "r5": r5_any,
        "r10": r10_any,
        "r10_all": r10_all,
        "ndcg10": n10,
        "records": len(records) if 'records' in locals() else 0
    }


def run_benchmark(data, limit=None, batch_gc=5):
    """运行 benchmark"""
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
        r10_current = r10_sum / valid if valid > 0 else 0.0
        
        # 预热模型
        if not warmup_done:
            print(f"  Warming up embedding model...")
            _ = embed_texts(["warmup"])
            warmup_done = True
        
        print(f"\r[{i+1}/{n}] {elapsed:.1f}s | ETA: {eta:.0f}s | R@5: {r5_current:.3f} | R@10: {r10_current:.3f} | Records: ~550", end="", flush=True)
        
        result = run_item(data[i], warmup_done)
        
        if result:
            r5_sum += result["r5"]
            r10_sum += result["r10"]
            r10_all_sum += result["r10_all"]
            ndcg_sum += result["ndcg10"]
            valid += 1
        
        # 批处理 GC
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
    parser.add_argument("--batch-gc", type=int, default=5, help="GC every N items")
    args = parser.parse_args()
    
    print("=" * 60)
    print("Memex × LongMemEval Benchmark (Turn-Level)")
    print("=" * 60)
    print()
    print("Configuration:")
    print("  Granularity: Turn-level (~550 records/question)")
    print("  Text truncation: 200 chars per turn")
    print("  Batch GC: every", args.batch_gc, "items")
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
    print("RESULTS (Turn-Level)")
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
    print("Comparison with MemPalace (turn-level baseline):")
    print(f"  MemPalace:  Recall@5 = 0.966")
    print(f"  Memex:      Recall@5 = {results['recall@5']:.4f}")
    print(f"  Delta:      {results['recall@5'] - 0.966:+.4f}")


if __name__ == "__main__":
    main()
