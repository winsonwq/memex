#!/usr/bin/env python3
"""快速测试：单题检索"""
import json
import sys
sys.path.insert(0, '/home/aqiu/.openclaw/workspace/memex/src')

from memex._embed import embed_texts
from memex.store.memory import MemoryStore
from memex._types import MemoryRecord, MemoryType

# 加载数据
with open('/tmp/longmemeval-data/longmemeval_s_cleaned.json') as f:
    data = json.load(f)

item = data[0]
question = item['question']
haystack_sessions = item.get('haystack_sessions', [])
haystack_session_ids = item.get('haystack_session_ids', [])
answer_sessions = item.get('answer_session_ids', [])

print(f'Q: {question[:80]}...')
print(f'Sessions: {len(haystack_sessions)}, IDs: {len(haystack_session_ids)}')
print(f'Answer sessions: {answer_sessions}')

# 构建 records
records = []
for sess_idx, session in enumerate(haystack_sessions):
    sess_id = haystack_session_ids[sess_idx] if sess_idx < len(haystack_session_ids) else f'sess_{sess_idx}'
    for turn in session:
        if isinstance(turn, dict):
            content = turn.get('content', '')
            if content:
                records.append(MemoryRecord(
                    type=MemoryType.BELIEF,
                    content=content[:500],
                    raw_text=content[:500],
                    repo='bench',
                    metadata={'session_id': sess_id}
                ))

print(f'Records: {len(records)}')

# 创建 store 并添加
store = MemoryStore()
texts = [r.content for r in records]
print('Embedding...')
vectors = embed_texts(texts)

print('Adding to store...')
for record, vector in zip(records, vectors):
    store.add(record, vector)

# 搜索
print('Searching...')
query_vec = embed_texts([question])[0]
results, scores = zip(*store.search(query_vec, limit=10))

print('\nTop 10 results:')
for i, (r, s) in enumerate(zip(results, scores)):
    sess_id = r.metadata.get('session_id', 'unknown')
    hit = '✓' if sess_id in answer_sessions else ' '
    print(f'{hit} [{s:.3f}] {sess_id}: {r.content[:60]}...')

# R@5
top5_sessions = set(r.metadata.get('session_id') for r in results[:5])
r5 = any(sid in top5_sessions for sid in answer_sessions)
print(f'\nR@5: {r5}')
