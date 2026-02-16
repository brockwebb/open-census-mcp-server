"""Real determinism test: replay actual treatment tool calls.

Extracts actual get_methodology_guidance calls from primary eval treatment
responses and replays them twice to verify:
1. Determinism: same call → same results (run1 vs run2)
2. Reproducibility: results match original (run1 vs original)

Usage:
    python scripts/test_determinism_real.py
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from src.eval.mcp_client import MCPClient


def extract_methodology_calls(responses_file: Path):
    """Extract get_methodology_guidance calls from treatment responses."""
    calls = []
    call_index = 0

    with open(responses_file) as f:
        for line in f:
            pair = json.loads(line)
            query_id = pair['query_id']
            treatment = pair['treatment']

            for tc in treatment.get('tool_calls', []):
                tool_name = tc.get('tool_name', '')
                if tool_name == 'get_methodology_guidance':
                    # Extract original context IDs
                    result = tc.get('result', {})
                    if isinstance(result, dict):
                        guidance = result.get('guidance', [])
                        context_ids = [c.get('context_id', 'unknown') for c in guidance]
                    else:
                        context_ids = []

                    calls.append({
                        'call_id': f"{query_id}_{call_index}",
                        'query_id': query_id,
                        'tool_name': tool_name,
                        'arguments': tc.get('arguments', {}),
                        'original_context_ids': context_ids
                    })
                    call_index += 1

    return calls


async def replay_calls(client: MCPClient, calls: list):
    """Replay tool calls twice and collect results."""
    run1_results = {}
    run2_results = {}

    print("\n=== RUN 1 ===")
    for call in calls:
        call_id = call['call_id']
        args = call['arguments']

        result = await client.call_tool('get_methodology_guidance', args)
        run1_results[call_id] = result

        num_contexts = len(result.get('guidance', []))
        topics = args.get('topics', [])
        print(f"  {call_id}: topics={topics}, contexts={num_contexts}")

    print("\n=== RUN 2 ===")
    for call in calls:
        call_id = call['call_id']
        args = call['arguments']

        result = await client.call_tool('get_methodology_guidance', args)
        run2_results[call_id] = result

        num_contexts = len(result.get('guidance', []))
        topics = args.get('topics', [])
        print(f"  {call_id}: topics={topics}, contexts={num_contexts}")

    return run1_results, run2_results


def compare_results(calls: list, run1_results: dict, run2_results: dict):
    """Three-way comparison: run1 vs run2, run1 vs original."""
    comparison_results = []

    run1_vs_run2_identical = 0
    run1_vs_run2_different = 0
    run1_vs_original_identical = 0
    run1_vs_original_different = 0

    print("\n=== THREE-WAY COMPARISON ===")
    print(f"{'Call ID':<20} {'Topics':<30} {'Orig':<6} {'Run1':<6} {'Run2':<6} {'R1=R2':<8} {'R1=Orig':<8}")
    print("-" * 100)

    for call in calls:
        call_id = call['call_id']
        topics = call['arguments'].get('topics', [])
        original_ids = set(call['original_context_ids'])

        run1_ids = set(c.get('context_id', '') for c in run1_results[call_id].get('guidance', []))
        run2_ids = set(c.get('context_id', '') for c in run2_results[call_id].get('guidance', []))

        # Compare run1 vs run2
        run1_vs_run2 = "MATCH" if run1_ids == run2_ids else "DIFFER"
        if run1_vs_run2 == "MATCH":
            run1_vs_run2_identical += 1
        else:
            run1_vs_run2_different += 1

        # Compare run1 vs original
        run1_vs_original = "MATCH" if run1_ids == original_ids else "DIFFER"
        if run1_vs_original == "MATCH":
            run1_vs_original_identical += 1
        else:
            run1_vs_original_different += 1

        # Format topics for display
        topics_str = ', '.join(topics[:2]) if len(topics) <= 2 else f"{topics[0]}, +{len(topics)-1}"

        print(f"{call_id:<20} {topics_str:<30} {len(original_ids):<6} {len(run1_ids):<6} {len(run2_ids):<6} {run1_vs_run2:<8} {run1_vs_original:<8}")

        # Show details for differing results
        if run1_vs_run2 == "DIFFER":
            print(f"  ⚠️  Run1 vs Run2 DIFFER:")
            print(f"    Only in run1: {run1_ids - run2_ids}")
            print(f"    Only in run2: {run2_ids - run1_ids}")

        if run1_vs_original == "DIFFER":
            print(f"  ⚠️  Run1 vs Original DIFFER:")
            print(f"    Only in original: {original_ids - run1_ids}")
            print(f"    Only in run1: {run1_ids - original_ids}")

        comparison_results.append({
            'call_id': call_id,
            'query_id': call['query_id'],
            'topics': topics,
            'original_contexts': sorted(original_ids),
            'run1_contexts': sorted(run1_ids),
            'run2_contexts': sorted(run2_ids),
            'run1_vs_run2': run1_vs_run2,
            'run1_vs_original': run1_vs_original
        })

    return {
        'comparison_results': comparison_results,
        'run1_vs_run2_identical': run1_vs_run2_identical,
        'run1_vs_run2_different': run1_vs_run2_different,
        'run1_vs_original_identical': run1_vs_original_identical,
        'run1_vs_original_different': run1_vs_original_different
    }


async def main():
    print("="*70)
    print("REAL DETERMINISM TEST")
    print("="*70)
    print("\nReplaying actual treatment tool calls from primary eval")

    # Step 1: Extract real tool calls
    responses_file = Path('results/cqs_responses_20260213_091530.jsonl')
    print(f"\nExtracting calls from {responses_file}...")

    calls = extract_methodology_calls(responses_file)
    unique_queries = len(set(c['query_id'] for c in calls))

    print(f"\n✅ Found {len(calls)} get_methodology_guidance calls")
    print(f"   across {unique_queries} unique queries")

    # Show sample of calls
    print("\nSample calls:")
    for call in calls[:5]:
        topics = call['arguments'].get('topics', [])
        domain = call['arguments'].get('domain', 'N/A')
        num_contexts = len(call['original_context_ids'])
        print(f"  {call['call_id']}: topics={topics}, domain={domain}, "
              f"returned {num_contexts} contexts")

    # Step 2: Replay calls twice
    print("\nStarting MCP client...")
    client = MCPClient()
    await client.start()

    if not await client.health_check():
        print("❌ MCP health check failed")
        await client.stop()
        return 1

    print("✅ MCP client ready")

    run1_results, run2_results = await replay_calls(client, calls)

    # Step 3: Three-way comparison
    comparison = compare_results(calls, run1_results, run2_results)

    # Step 4: Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    deterministic = comparison['run1_vs_run2_different'] == 0
    reproducible = comparison['run1_vs_original_different'] == 0

    print(f"\nTotal calls replayed: {len(calls)}")
    print(f"Unique queries: {unique_queries}")

    print(f"\nDeterminism (Run1 vs Run2):")
    print(f"  Identical: {comparison['run1_vs_run2_identical']}/{len(calls)}")
    print(f"  Different: {comparison['run1_vs_run2_different']}/{len(calls)}")
    if deterministic:
        print(f"  ✅ DETERMINISTIC: Same call → same results")
    else:
        print(f"  ❌ NON-DETERMINISTIC: Found {comparison['run1_vs_run2_different']} mismatches")

    print(f"\nReproducibility (Run1 vs Original):")
    print(f"  Identical: {comparison['run1_vs_original_identical']}/{len(calls)}")
    print(f"  Different: {comparison['run1_vs_original_different']}/{len(calls)}")
    if reproducible:
        print(f"  ✅ REPRODUCIBLE: Current results match original eval")
    else:
        print(f"  ⚠️  CHANGED: {comparison['run1_vs_original_different']} calls differ from original")
        print(f"     (Pack may have been updated since primary eval)")

    # Save results
    output = {
        'test': 'pragmatics_determinism_real',
        'timestamp': datetime.now().isoformat(),
        'total_calls_replayed': len(calls),
        'total_queries': unique_queries,
        'run1_vs_run2_identical': comparison['run1_vs_run2_identical'],
        'run1_vs_run2_different': comparison['run1_vs_run2_different'],
        'run1_vs_original_identical': comparison['run1_vs_original_identical'],
        'run1_vs_original_different': comparison['run1_vs_original_different'],
        'deterministic': deterministic,
        'reproducible': reproducible,
        'calls': comparison['comparison_results']
    }

    output_path = Path('results/rag_ablation/analysis/determinism_test_real.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n💾 Results saved to {output_path}")

    await client.stop()
    return 0


if __name__ == '__main__':
    exit(asyncio.run(main()))
