#!/usr/bin/env python3
"""Pair RAG responses with existing control responses for judge pipeline."""
import json
import sys
from pathlib import Path


def build_pairs(rag_path: str, control_path: str, output_path: str):
    """Pair RAG responses with control responses into QueryPair format.

    Args:
        rag_path: Path to RAG responses JSONL (ResponseRecord per line)
        control_path: Path to original paired JSONL (QueryPair per line)
        output_path: Path to write paired RAG vs Control JSONL
    """
    # Load control responses from original paired file
    controls = {}
    with open(control_path) as f:
        for line in f:
            pair = json.loads(line)
            controls[pair['query_id']] = pair['control']

    # Load RAG responses
    rags = {}
    with open(rag_path) as f:
        for line in f:
            rec = json.loads(line)
            rags[rec['query_id']] = rec

    # Build pairs: control stays control, RAG becomes "treatment" slot
    pairs = []
    for qid in sorted(rags.keys()):
        if qid not in controls:
            print(f"WARNING: {qid} has RAG response but no control - skipping")
            continue

        # Get query metadata from original pair
        with open(control_path) as f:
            for line in f:
                pair = json.loads(line)
                if pair['query_id'] == qid:
                    query_text = pair['query_text']
                    category = pair['category']
                    difficulty = pair['difficulty']
                    break

        pairs.append({
            'query_id': qid,
            'query_text': query_text,
            'category': category,
            'difficulty': difficulty,
            'control': controls[qid],
            'treatment': rags[qid],  # RAG goes in treatment slot
        })

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        for pair in pairs:
            f.write(json.dumps(pair) + '\n')

    print(f"Built {len(pairs)} pairs -> {output_path}")


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: build_rag_pairs.py <rag_path> <control_path> <output_path>")
        sys.exit(1)

    build_pairs(
        rag_path=sys.argv[1],
        control_path=sys.argv[2],
        output_path=sys.argv[3],
    )
