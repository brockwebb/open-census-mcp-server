#!/usr/bin/env python3
"""Stage 2 QC Script — Consolidates structural validation, preference analysis,
identical vector detection, and vendor calibration checks.

Usage:
    python src/eval/qc_stage2.py --file results/v2_redo/stage2/control_vs_rag_20260217_083951.jsonl

Exit codes:
    0: All checks passed
    1: Structural check failed (wrong record count, same-condition pairs, missing comparison)
"""

import argparse
import json
import sys
from collections import defaultdict, Counter
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Stage 2 QC validation script")
    parser.add_argument("--file", required=True, help="Path to Stage 2 JSONL output file")
    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    # Load records
    with open(file_path) as f:
        records = [json.loads(line) for line in f]

    print(f"=== Stage 2 QC Report: {file_path.name} ===\n")

    # === STRUCTURAL CHECKS (exit 1 on failure) ===
    exit_code = 0

    # Expected: 702 records (39 queries × 6 passes × 3 vendors)
    total = len(records)
    print(f"Total records: {total}")
    if total != 702:
        print(f"  ⚠️  WARNING: Expected 702 records (39 queries × 6 passes × 3 vendors)", file=sys.stderr)
        exit_code = 1

    # Parse failures
    parse_failures = sum(1 for r in records if not r["parse_success"])
    print(f"Parse failures: {parse_failures} ({parse_failures/total*100:.1f}%)")
    if parse_failures > 0:
        print(f"  ℹ️  Parse failures stored with preference='parse_failed'")

    # Comparison field
    comparisons = set(r["comparison"] for r in records)
    print(f"Comparison: {comparisons}")
    if len(comparisons) != 1:
        print(f"  ❌ ERROR: Multiple comparison values found", file=sys.stderr)
        exit_code = 1

    # Labels
    labels = set((r["response_a_label"], r["response_b_label"]) for r in records)
    print(f"Labels: {labels}")
    if len(labels) != 2:
        print(f"  ⚠️  WARNING: Expected 2 label pairs (A,B) and (B,A)", file=sys.stderr)

    # Same-condition pairs (should be 0)
    same_condition = sum(1 for r in records if r["response_a_label"] == r["response_b_label"])
    print(f"Same-condition pairs: {same_condition}")
    if same_condition > 0:
        print(f"  ❌ ERROR: Found same-condition pairs (invalid)", file=sys.stderr)
        exit_code = 1

    # Presentation ordering (should be balanced)
    ordering = Counter(r["presentation_order"] for r in records)
    print(f"Ordering: {dict(ordering)}")
    if len(ordering) == 2:
        counts = list(ordering.values())
        if abs(counts[0] - counts[1]) > 1:
            print(f"  ⚠️  WARNING: Unbalanced presentation ordering", file=sys.stderr)

    # Vendor distribution (should be balanced)
    vendors = Counter(r["judge_vendor"] for r in records)
    print(f"Vendors: {dict(vendors)}")
    if len(vendors) == 3:
        counts = list(vendors.values())
        if max(counts) - min(counts) > 1:
            print(f"  ⚠️  WARNING: Unbalanced vendor distribution", file=sys.stderr)

    print()

    # === CQS SCORES ===
    scores = defaultdict(lambda: defaultdict(list))
    for r in records:
        if not r['parse_success']:
            continue
        for lk, sk in [('response_a_label', 'scores_response_a'), ('response_b_label', 'scores_response_b')]:
            for dim, s in r[sk].items():
                scores[r[lk]][dim].append(s['score'])

    print("=== CQS Scores ===")
    for cond in sorted(scores):
        cqs_vals = [v for d in ['D1', 'D2', 'D3', 'D4', 'D5'] for v in scores[cond][d]]
        cqs_mean = sum(cqs_vals) / len(cqs_vals)
        print(f"{cond} CQS: {cqs_mean:.3f}")
        for d in ['D1', 'D2', 'D3', 'D4', 'D5']:
            vals = scores[cond][d]
            print(f"  {d}: {sum(vals)/len(vals):.3f}")
    print()

    # === PREFERENCES ===
    prefs = Counter()
    for r in records:
        if not r['parse_success']:
            continue
        p = r.get('preference', '')
        if p in ('A', 'B'):
            winner = r['response_a_label'] if p == 'A' else r['response_b_label']
            prefs[winner] += 1
        elif p == 'tie':
            prefs['tie'] += 1
        else:
            prefs[f'other:{p}'] += 1

    print("=== Preferences ===")
    total_prefs = sum(prefs.values())
    for k, v in prefs.most_common():
        print(f"  {k}: {v} ({v/total_prefs*100:.1f}%)")
    print()

    # === IDENTICAL VECTORS ===
    identical = Counter()
    for r in records:
        if not r['parse_success']:
            continue
        a_vec = tuple(r['scores_response_a'].get(d, {}).get('score', -1) for d in ['D1', 'D2', 'D3', 'D4', 'D5', 'D6'])
        b_vec = tuple(r['scores_response_b'].get(d, {}).get('score', -1) for d in ['D1', 'D2', 'D3', 'D4', 'D5', 'D6'])
        if a_vec == b_vec:
            identical[r['query_id']] += 1

    parsed_count = len([r for r in records if r["parse_success"]])
    identical_total = sum(identical.values())
    print(f"=== Identical Vectors ===")
    print(f"Total: {identical_total}/{parsed_count} ({identical_total/parsed_count*100:.1f}%)")
    print(f"Top queries with identical scores:")
    for qid, cnt in identical.most_common(10):
        print(f"  {qid}: {cnt}")
    print()

    # === VENDOR BREAKDOWN ===
    vs = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for r in records:
        if not r['parse_success']:
            continue
        for lk, sk in [('response_a_label', 'scores_response_a'), ('response_b_label', 'scores_response_b')]:
            for dim, s in r[sk].items():
                vs[r['judge_vendor']][r[lk]][dim].append(s['score'])

    print("=== Vendor Breakdown ===")
    for vendor in sorted(vs):
        for cond in sorted(vs[vendor]):
            cqs_vals = [x for d in ['D1', 'D2', 'D3', 'D4', 'D5'] for x in vs[vendor][cond][d]]
            cqs_mean = sum(cqs_vals) / len(cqs_vals)
            print(f"  {vendor}/{cond}: {cqs_mean:.3f}")

    print()
    if exit_code == 0:
        print("✅ All structural checks passed")
    else:
        print("❌ Structural checks FAILED", file=sys.stderr)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
