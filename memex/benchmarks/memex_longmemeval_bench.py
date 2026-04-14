#!/usr/bin/env python3
"""
Memex × LongMemEval Benchmark
================================

评估 Memex 的检索能力，对标 MemPalace 的 96.6% R@5 raw baseline。

流程：
1. 对每个问题，灌入 haystack sessions
2. 用 question 做向量搜索
3. 计算 Recall@5, Recall@10, NDCG@10
"""
import os
import sys
import json
import math
import time
from pathlib import Path

# 添加 memex 到 path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from memex._types import MemoryRecord, MemoryType
from memex._embed import embed_texts
from memex.store.memory import MemoryStore


# =============================================================================
# METRICS
# =============================================================================

def dcg(relevances, k):
    """Discounted Cumulative Gain."""
    score = 0.0
    for i, rel in enumerate(relevances[:k]):
        score += rel / math.log2(i + 2)
    return score


def ndcg(rankings, correct_ids, corpus_ids, k):
    """Normalized DCG."""
    relevances = [1.0 if corpus_ids[idx] in correct_ids else 0.0 for idx in rankings[:k]]
    ideal = sorted(relevances, reverse=True)
    idcg = dcg(ideal, k)
    if idcg == 0:
        return 0.0
    return dcg(relevances, k) / idcg


def evaluate_retrieval(rankings, correct_ids, corpus_ids, k):
    """
    Evaluate retrieval at rank k.
    Returns (recall_any, recall_all, ndcg_score).
    """
    top_k_ids = set(corpus_ids[idx] for idx in rankings[:k])
    recall_any = float(any(cid in top_k_ids for cid in correct_ids))
    recall_all = float(all(cid in top_k_ids for cid in correct_ids))
    ndcg_score = ndcg(rankings, correct_ids, corpus_ids, k)
    return recall_any, recall_all, ndcg_score


# =============================================================================
# DATA LOADING
# =============================================================================

def load_longmemeval(path):
    """加载 LongMemEval 数据集"""
    with open(path) as f:
        return json.load(f)


def flatten_sessions(haystack_sessions, session_ids, repo="benchmark"):
    """
    将 sessions 展平为 memory records
    每个 turn 是一个独立的 memory entry
    """
    records = []
    
    for sess_idx, session in enumerate(haystack_sessions):
        # session_ids[i] 可能是字符串如 'sharegpt_yywfIrx_0'
        sess_id = session_ids[sess_idx] if sess_idx < len(session_ids) else f"sess_{sess_idx}"
        
        # session 是一个 turn 列表
        for turn_idx, turn in enumerate(session):
            if not isinstance(turn, dict):
                continue
                
            role = turn.get("role", "unknown")
            content = turn.get("content", "")
            
            if not content:
                continue
            
            # 创建 memory record
            record = MemoryRecord(
                type=MemoryType.BELIEF,
                content=f"[{role}] {content}",
                raw_text=content,
                repo=repo,
                metadata={
                    "session_id": sess_id,
                    "turn_idx": turn_idx,
                    "role": role,
                }
            )
            records.append(record)
    
    return records


# =============================================================================
# BENCHMARK
# =============================================================================

def run_benchmark(data, limit=None, verbose=True):
    """
    运行 LongMemEval benchmark
    
    Returns:
        dict with recall@5, recall@10, ndcg@10
    """
    if limit:
        data = data[:limit]
    
    n = len(data)
    recall5_any_sum = 0.0
    recall10_any_sum = 0.0
    recall10_all_sum = 0.0
    ndcg10_sum = 0.0
    
    # 预热 embedding 模型（加载一次）
    if verbose:
        print("Warming up embedding model...")
    _ = embed_texts(["warmup"])
    
    for i, item in enumerate(data):
        if verbose:
            print(f"\r[{i+1}/{n}] Processing...", end="", flush=True)
        
        question = item["question"]
        
        # 解析 ground truth
        answer_sessions_str = item.get("answer_session_ids", "[]")
        try:
            answer_sessions = eval(answer_sessions_str)
        except:
            answer_sessions = []
        
        # 解析 haystack sessions 和 session_ids（已经是 list）
        haystack_sessions = item.get("haystack_sessions", [])
        haystack_session_ids = item.get("haystack_session_ids", [f"sess_{i}" for i in range(len(haystack_sessions))])
        
        if not haystack_sessions:
            continue
        
        # 展平 sessions 为 records
        records = flatten_sessions(haystack_sessions, haystack_session_ids)
        
        if not records:
            continue
        
        # 创建临时 store
        store = MemoryStore()
        
        # 生成 embeddings
        texts = [r.content for r in records]
        vectors = embed_texts(texts)
        
        # 添加到 store
        for record, vector in zip(records, vectors):
            store.add(record, vector)
        
        # 用 question 搜索
        query_vector = embed_texts([question])[0]
        results, scores = zip(*store.search(query_vector, limit=10))
        
        # 构建 corpus（所有 session IDs）
        corpus_ids = [r.metadata.get("session_id", r.id) for r in results]
        rankings = list(range(len(results)))
        
        # 计算 metrics
        r5_any, r5_all, n5 = evaluate_retrieval(
            rankings, answer_sessions, corpus_ids, 5
        )
        r10_any, r10_all, n10 = evaluate_retrieval(
            rankings, answer_sessions, corpus_ids, 10
        )
        
        recall5_any_sum += r5_any
        recall10_any_sum += r10_any
        recall10_all_sum += r10_all
        ndcg10_sum += n10
    
    if verbose:
        print()
    
    return {
        "recall@5": recall5_any_sum / n,
        "recall@10": recall10_any_sum / n,
        "recall@10_all": recall10_all_sum / n,
        "ndcg@10": ndcg10_sum / n,
        "count": n,
    }


# =============================================================================
# MAIN
# =============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("data", help="Path to longmemeval_s_cleaned.json")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of questions")
    parser.add_argument("--verbose", action="store_true", default=True)
    args = parser.parse_args()
    
    print("=" * 60)
    print("Memex × LongMemEval Benchmark")
    print("=" * 60)
    
    # 加载数据
    print(f"\nLoading data from {args.data}...")
    data = load_longmemeval(args.data)
    print(f"Loaded {len(data)} questions")
    
    if args.limit:
        print(f"Limited to {args.limit} questions")
    
    # 运行 benchmark
    print("\nRunning benchmark...")
    start = time.time()
    results = run_benchmark(data, limit=args.limit, verbose=args.verbose)
    elapsed = time.time() - start
    
    # 输出结果
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Questions:     {results['count']}")
    print(f"Recall@5:      {results['recall@5']:.4f}")
    print(f"Recall@10:     {results['recall@10']:.4f}")
    print(f"Recall@10(all):{results['recall@10_all']:.4f}")
    print(f"NDCG@10:       {results['ndcg@10']:.4f}")
    print(f"Time:          {elapsed:.1f}s")
    print("=" * 60)
    
    # 对比 MemPalace
    print("\nComparison with MemPalace (raw mode):")
    print(f"  MemPalace:  Recall@5 = 0.966")
    print(f"  Memex:      Recall@5 = {results['recall@5']:.4f}")


if __name__ == "__main__":
    main()
