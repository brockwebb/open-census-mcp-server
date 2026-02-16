"""Determinism test: verify pragmatics and RAG produce identical results on repeated calls.

Tests:
1. Pragmatics (MCP get_methodology_guidance): same query → same contexts every time
2. RAG (FAISS retrieval): same query → same chunks/scores every time

Usage:
    python scripts/test_determinism.py
"""

import asyncio
import json
import yaml
from pathlib import Path
from datetime import datetime

from src.eval.mcp_client import MCPClient
from src.eval.rag_retriever import RAGRetriever


async def test_pragmatics_determinism(queries):
    """Test that pragmatics retrieval is deterministic."""
    print("\n" + "="*70)
    print("PRAGMATICS DETERMINISM TEST")
    print("="*70)

    client = MCPClient()
    await client.start()

    # Verify MCP health
    if not await client.health_check():
        raise RuntimeError("MCP health check failed")

    results_run1 = {}
    results_run2 = {}

    # Use a consistent set of topics for all queries
    # This tests tool determinism, not LLM topic selection determinism
    topics = ["margin_of_error", "small_area", "geography"]

    # Run 1
    print("\n=== RUN 1 ===")
    for q in queries:
        qid = q['id']
        result = await client.call_tool('get_methodology_guidance', {
            'topics': topics,
            'domain': 'acs'
        })
        results_run1[qid] = result
        num_contexts = len(result.get('contexts', []))
        print(f"  {qid}: {num_contexts} contexts")

    # Run 2
    print("\n=== RUN 2 ===")
    for q in queries:
        qid = q['id']
        result = await client.call_tool('get_methodology_guidance', {
            'topics': topics,
            'domain': 'acs'
        })
        results_run2[qid] = result
        num_contexts = len(result.get('contexts', []))
        print(f"  {qid}: {num_contexts} contexts")

    # Compare
    print("\n=== COMPARISON ===")
    identical = 0
    different = 0
    differences = []

    for qid in sorted(results_run1.keys()):
        r1 = json.dumps(results_run1[qid], sort_keys=True)
        r2 = json.dumps(results_run2[qid], sort_keys=True)

        if r1 == r2:
            identical += 1
        else:
            different += 1
            print(f"  DIFFER: {qid}")
            # Show what changed
            c1 = [c.get('context_id') for c in results_run1[qid].get('contexts', [])]
            c2 = [c.get('context_id') for c in results_run2[qid].get('contexts', [])]
            print(f"    Run 1: {c1}")
            print(f"    Run 2: {c2}")
            differences.append({
                'query_id': qid,
                'run1_contexts': c1,
                'run2_contexts': c2
            })

    print(f"\nPragmatics: {identical}/{len(queries)} identical, {different}/{len(queries)} different")

    # Check if contexts are being returned
    avg_contexts = sum(len(r.get('contexts', [])) for r in results_run1.values()) / len(results_run1)
    if avg_contexts == 0:
        print(f"  ⚠️  WARNING: All queries returned 0 contexts (topics used: {topics})")
        print(f"  This may indicate pack is empty or topics don't match trigger patterns")

    await client.stop()

    return {
        'total_queries': len(queries),
        'identical': identical,
        'different': different,
        'deterministic': different == 0,
        'differences': differences,
        'avg_contexts_returned': avg_contexts,
        'topics_used': topics
    }


def test_rag_determinism(queries):
    """Test that RAG retrieval is deterministic."""
    print("\n" + "="*70)
    print("RAG DETERMINISM TEST")
    print("="*70)

    index_dir = Path('results/rag_ablation/index')
    if not index_dir.exists():
        print(f"  ⚠️  RAG index not found at {index_dir}")
        return {
            'total_queries': 0,
            'identical': 0,
            'different': 0,
            'deterministic': None,
            'differences': [],
            'error': 'Index not found'
        }

    retriever = RAGRetriever(str(index_dir), top_k=5)

    results_run1 = {}
    results_run2 = {}

    # Run 1
    print("\n=== RUN 1 ===")
    for q in queries:
        qid = q['id']
        result = retriever.retrieve(q['text'])
        results_run1[qid] = result
        num_chunks = len(result.get('retrieved_chunks', []))
        print(f"  {qid}: {num_chunks} chunks")

    # Run 2
    print("\n=== RUN 2 ===")
    for q in queries:
        qid = q['id']
        result = retriever.retrieve(q['text'])
        results_run2[qid] = result
        num_chunks = len(result.get('retrieved_chunks', []))
        print(f"  {qid}: {num_chunks} chunks")

    # Compare
    print("\n=== COMPARISON ===")
    identical = 0
    different = 0
    differences = []

    for qid in sorted(results_run1.keys()):
        # Compare chunk IDs and scores (rounded to 6 decimals)
        chunks1 = results_run1[qid].get('retrieved_chunks', [])
        chunks2 = results_run2[qid].get('retrieved_chunks', [])

        ids1 = [c['chunk_id'] for c in chunks1]
        ids2 = [c['chunk_id'] for c in chunks2]
        scores1 = [round(c['score'], 6) for c in chunks1]
        scores2 = [round(c['score'], 6) for c in chunks2]

        if ids1 == ids2 and scores1 == scores2:
            identical += 1
        else:
            different += 1
            print(f"  DIFFER: {qid}")
            if ids1 != ids2:
                print(f"    Chunk IDs differ")
                print(f"    Run 1: {ids1}")
                print(f"    Run 2: {ids2}")
            if scores1 != scores2:
                print(f"    Scores differ")
                print(f"    Run 1: {scores1}")
                print(f"    Run 2: {scores2}")

            differences.append({
                'query_id': qid,
                'run1_chunks': ids1,
                'run2_chunks': ids2,
                'run1_scores': scores1,
                'run2_scores': scores2
            })

    print(f"\nRAG: {identical}/{len(queries)} identical, {different}/{len(queries)} different")

    return {
        'total_queries': len(queries),
        'identical': identical,
        'different': different,
        'deterministic': different == 0,
        'differences': differences
    }


async def main():
    print("="*70)
    print("DETERMINISM TEST")
    print("="*70)
    print("\nVerifying that same inputs → same outputs for both systems")

    # Load queries
    with open('src/eval/battery/queries.yaml') as f:
        data = yaml.safe_load(f)
        queries = data['queries']

    print(f"\nLoaded {len(queries)} queries from test battery")

    # Test pragmatics
    pragmatics_results = await test_pragmatics_determinism(queries)

    # Test RAG
    rag_results = test_rag_determinism(queries)

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    print(f"\nPragmatics: {pragmatics_results['identical']}/{pragmatics_results['total_queries']} identical")
    if pragmatics_results['deterministic']:
        print("  ✅ DETERMINISTIC: Same inputs → same outputs")
    else:
        print("  ❌ NON-DETERMINISTIC: Found differences")

    if rag_results.get('error'):
        print(f"\nRAG: {rag_results['error']}")
    else:
        print(f"\nRAG: {rag_results['identical']}/{rag_results['total_queries']} identical")
        if rag_results['deterministic']:
            print("  ✅ DETERMINISTIC: Same inputs → same outputs")
            print("  Note: RAG uses FAISS IndexFlatIP (exact search) which is deterministic.")
            print("  Approximate methods (HNSW, LSH) would NOT be deterministic.")
        else:
            print("  ❌ NON-DETERMINISTIC: Found differences")

    print("\nArchitectural Note:")
    print("  Pragmatics = deterministic by design (graph lookup)")
    print("  RAG = deterministic by accident (exact search, but config-dependent)")

    # Save results
    output = {
        'test': 'determinism_verification',
        'timestamp': datetime.now().isoformat(),
        'pragmatics': pragmatics_results,
        'rag': rag_results,
        'summary': {
            'both_deterministic': (
                pragmatics_results['deterministic'] and
                rag_results.get('deterministic', False)
            ),
            'architectural_distinction': (
                "Pragmatics are deterministic by design (graph lookup). "
                "RAG with IndexFlatIP is deterministic by accident (exact search), "
                "but approximate methods (HNSW, LSH) would not be."
            )
        }
    }

    output_path = Path('results/rag_ablation/analysis/determinism_test.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n💾 Results saved to {output_path}")


if __name__ == '__main__':
    asyncio.run(main())
