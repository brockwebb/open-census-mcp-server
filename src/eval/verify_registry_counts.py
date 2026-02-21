#!/usr/bin/env python3
"""
Verify numbers cited in paper/numbers_registry.md

V&V artifact: every number traced to source with reproducible computation.
SRS: Supports Section 8.9 V&V Registry

Usage: python -m src.eval.verify_registry_counts
"""

import json
import yaml
import sqlite3
import os
from pathlib import Path
from datetime import datetime


def main():
    base = Path(__file__).parent.parent.parent  # repo root
    results = {}

    # === SD-001: Query count ===
    with open(base / 'src/eval/battery/queries.yaml') as f:
        battery = yaml.safe_load(f)
    queries = battery if isinstance(battery, list) else battery.get('queries', battery)
    if isinstance(queries, dict):
        query_count = len(queries)
        categories = {}
        for qid, q in queries.items():
            cat = q.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1
    else:
        query_count = len(queries)
        categories = {}
        for q in queries:
            cat = q.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1

    results['SD-001'] = {'value': query_count, 'source': 'src/eval/battery/queries.yaml'}

    # === SD-009: Normal/edge split ===
    normal_count = categories.get('normal', 0)
    edge_count = query_count - normal_count
    results['SD-009'] = {
        'normal': normal_count,
        'edge': edge_count,
        'normal_pct': f'{normal_count/query_count*100:.1f}%',
        'edge_pct': f'{edge_count/query_count*100:.1f}%',
        'categories': categories,
        'source': 'src/eval/battery/queries.yaml'
    }

    # === SD-006: Stage 2 record count ===
    stage2_dir = base / 'results/v2_redo/stage2'
    stage2_total = 0
    stage2_parse_fails = 0
    stage2_per_file = {}
    for jsonl_file in sorted(stage2_dir.glob('*.jsonl')):
        with open(jsonl_file) as f:
            records = [json.loads(line) for line in f if line.strip()]
        count = len(records)
        fails = sum(1 for r in records if r.get('preference') == 'parse_failed')
        stage2_total += count
        stage2_parse_fails += fails
        stage2_per_file[jsonl_file.name] = {'records': count, 'parse_failures': fails}

    results['SD-006'] = {
        'value': stage2_total,
        'parse_failures': stage2_parse_fails,
        'per_file': stage2_per_file,
        'source': 'results/v2_redo/stage2/*.jsonl'
    }

    # === SD-007: Records per comparison ===
    results['SD-007'] = {
        'value': stage2_total // 3 if stage2_total % 3 == 0 else 'UNEVEN',
        'expected': query_count * 6,  # 39 queries × 6 passes
        'source': 'derived from SD-006'
    }

    # === PL-001: Compiled pragmatic items (ACS pack) ===
    acs_db = base / 'packs/acs.db'
    conn = sqlite3.connect(str(acs_db))
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM context')
    acs_context_count = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM threads')
    acs_thread_count = cur.fetchone()[0]
    cur.execute('SELECT pack_id, version FROM packs')
    pack_info = cur.fetchone()
    conn.close()

    results['PL-001'] = {
        'context_items': acs_context_count,
        'threads': acs_thread_count,
        'pack_version': pack_info[1] if pack_info else 'unknown',
        'source': 'packs/acs.db (context table)'
    }

    # Also check census and general packs
    pack_totals = {'acs': acs_context_count}
    for pack_name, pack_file in [('census', 'census.db'), ('general', 'general_statistics.db')]:
        db_path = base / f'packs/{pack_file}'
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute('SELECT COUNT(*) FROM context')
            pack_totals[pack_name] = cur.fetchone()[0]
            conn.close()

    results['PL-001_inheritance'] = {
        'per_pack': pack_totals,
        'total_with_inheritance': sum(pack_totals.values()),
        'note': 'ACS inherits from census inherits from general (FR-PC-005)'
    }

    # === PL-002: Staged pragmatic items ===
    staging_dir = base / 'staging/acs'
    staged_total = 0
    staged_per_file = {}
    for json_file in sorted(staging_dir.glob('*.json')):
        if json_file.name in ('manifest.json', '.gitkeep'):
            continue
        with open(json_file) as f:
            data = json.load(f)
        if isinstance(data, list):
            count = len(data)
        elif isinstance(data, dict) and 'contexts' in data:
            count = len(data['contexts'])
        else:
            count = 1  # single item
        staged_total += count
        staged_per_file[json_file.name] = count

    results['PL-002'] = {
        'value': staged_total,
        'per_file': staged_per_file,
        'source': 'staging/acs/*.json (excluding manifest.json)'
    }

    # === PL-004: Grounding compliance ===
    # Check Stage 1 pragmatics responses for methodology_guidance calls
    prag_file = base / 'results/v2_redo/stage1/pragmatics_responses_20260216_074817.jsonl'
    if prag_file.exists():
        with open(prag_file) as f:
            prag_records = [json.loads(line) for line in f if line.strip()]
        grounded = 0
        for rec in prag_records:
            tool_calls = rec.get('tool_calls', [])
            has_methodology = any(
                tc.get('tool_name', tc.get('name', '')) == 'get_methodology_guidance'
                for tc in tool_calls
            )
            if has_methodology:
                grounded += 1
        results['PL-004'] = {
            'grounded': grounded,
            'total': len(prag_records),
            'compliance': f'{grounded}/{len(prag_records)}',
            'pct': f'{grounded/len(prag_records)*100:.1f}%' if prag_records else 'N/A',
            'source': 'results/v2_redo/stage1/pragmatics_responses_20260216_074817.jsonl'
        }
    else:
        results['PL-004'] = {'error': f'File not found: {prag_file}'}

    # Also check control and RAG for grounding compliance
    for cond, fname in [('control', 'control_responses_20260216_055354.jsonl'),
                         ('rag', 'rag_responses_20260216_055354.jsonl')]:
        cond_file = base / f'results/v2_redo/stage1/{fname}'
        if cond_file.exists():
            with open(cond_file) as f:
                cond_records = [json.loads(line) for line in f if line.strip()]
            grounded = sum(1 for rec in cond_records
                          if any(tc.get('tool_name', tc.get('name', '')) == 'get_methodology_guidance'
                                 for tc in rec.get('tool_calls', [])))
            results[f'PL-004_{cond}'] = {
                'grounded': grounded,
                'total': len(cond_records),
                'compliance': f'{grounded}/{len(cond_records)}'
            }

    # === GAP-008: Bootstrap CI parameters ===
    config_file = base / 'src/eval/judge_config.yaml'
    with open(config_file) as f:
        config = yaml.safe_load(f)
    analysis_config = config.get('analysis', {})
    results['GAP-008'] = {
        'bootstrap_iterations': analysis_config.get('bootstrap_iterations', 'NOT FOUND'),
        'bootstrap_seed': analysis_config.get('bootstrap_seed', 'NOT FOUND'),
        'source': 'src/eval/judge_config.yaml (analysis section)'
    }

    # === GAP-009: RAG index parameters ===
    rag_index_dir = base / 'results/rag_ablation/index'
    if rag_index_dir.exists():
        rag_files = list(rag_index_dir.iterdir())
        results['GAP-009'] = {
            'index_files': [f.name for f in rag_files],
            'source': 'results/rag_ablation/index/'
        }
        # Try to read metadata if exists
        for f in rag_files:
            if f.suffix == '.json' and 'meta' in f.name.lower():
                with open(f) as fh:
                    results['GAP-009']['metadata'] = json.load(fh)
    else:
        results['GAP-009'] = {'error': 'results/rag_ablation/index/ not found (V1 legacy path)'}

    # === OUTPUT REPORT ===
    timestamp = datetime.now().isoformat()

    sd001_status = 'PASS' if results['SD-001']['value'] == 39 else 'FAIL'
    sd006_status = 'PASS' if results['SD-006']['value'] == 2106 else f"DISCREPANCY (got {results['SD-006']['value']})"
    sd007_val = results['SD-007']['value']
    sd007_status = 'PASS' if sd007_val == 702 else f"DISCREPANCY (got {sd007_val})"
    sd009_normal_frac = results['SD-009']['normal'] / query_count
    sd009_status = 'PASS' if abs(sd009_normal_frac - 0.41) < 0.02 else 'DISCREPANCY'

    report = f"""# Numbers Registry Verification Report

**Generated:** {timestamp}
**Script:** src/eval/verify_registry_counts.py
**Reproduce:** `python -m src.eval.verify_registry_counts`

## Study Design Parameters

| ID | Claimed | Verified | Source | Status |
|----|---------|----------|--------|--------|
| SD-001 | 39 queries | {results['SD-001']['value']} | {results['SD-001']['source']} | {sd001_status} |
| SD-006 | 2,106 records | {results['SD-006']['value']} | {results['SD-006']['source']} | {sd006_status} |
| SD-007 | 702/comparison | {sd007_val} (expected {results['SD-007']['expected']}) | {results['SD-007']['source']} | {sd007_status} |
| SD-009 | 41%/59% | {results['SD-009']['normal_pct']}/{results['SD-009']['edge_pct']} | {results['SD-009']['source']} | {sd009_status} |

### SD-009 Category Breakdown
"""
    for cat, count in sorted(results['SD-009']['categories'].items()):
        report += f"- {cat}: {count}\n"

    report += f"""
### SD-006 Per-File Breakdown
"""
    for fname, info in results['SD-006']['per_file'].items():
        report += f"- {fname}: {info['records']} records ({info['parse_failures']} parse failures)\n"

    pl001_status = 'PASS' if results['PL-001']['context_items'] == 36 else f"NOTE: expected 36, got {results['PL-001']['context_items']}"

    report += f"""
## Pragmatics Layer

| ID | Claimed | Verified | Source | Status |
|----|---------|----------|--------|--------|
| PL-001 | 36 items | {results['PL-001']['context_items']} context, {results['PL-001']['threads']} threads | {results['PL-001']['source']} | {pl001_status} |
| PL-002 | 47 staged | {results['PL-002']['value']} | {results['PL-002']['source']} | {'PASS' if results['PL-002']['value'] == 47 else f"DISCREPANCY (got {results['PL-002']['value']})"} |
"""

    if 'PL-004' in results and 'error' not in results['PL-004']:
        pl004_status = 'PASS' if results['PL-004']['grounded'] == results['PL-004']['total'] else 'FAIL'
        report += f"| PL-004 | 39/39 (100%) | {results['PL-004']['compliance']} ({results['PL-004']['pct']}) | {results['PL-004']['source']} | {pl004_status} |\n"

    report += f"""
### PL-001 Pack Inheritance
"""
    for pack, count in results['PL-001_inheritance']['per_pack'].items():
        report += f"- {pack}: {count} items\n"
    report += f"- Total with inheritance: {results['PL-001_inheritance']['total_with_inheritance']}\n"

    report += f"""
### PL-002 Staged Items Per File
"""
    for fname, count in results['PL-002']['per_file'].items():
        report += f"- {fname}: {count}\n"

    if 'PL-004' in results and 'error' not in results['PL-004']:
        report += f"""
### PL-004 Grounding Compliance Per Condition
- Pragmatics: {results['PL-004']['compliance']}
"""
        for cond in ['control', 'rag']:
            key = f'PL-004_{cond}'
            if key in results:
                report += f"- {cond.title()}: {results[key]['compliance']}\n"

    report += f"""
## Config Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| Bootstrap iterations | {results['GAP-008']['bootstrap_iterations']} | {results['GAP-008']['source']} |
| Bootstrap seed | {results['GAP-008']['bootstrap_seed']} | {results['GAP-008']['source']} |
"""

    if 'error' in results.get('GAP-009', {}):
        report += f"\n## GAP-009: RAG Index\n\n{results['GAP-009']['error']}\n"
    elif 'GAP-009' in results:
        report += f"\n## GAP-009: RAG Index Files\n\n"
        for f in results['GAP-009']['index_files']:
            report += f"- {f}\n"
        if 'metadata' in results['GAP-009']:
            report += f"\nMetadata: {json.dumps(results['GAP-009']['metadata'], indent=2)}\n"

    # Write report
    output_dir = base / 'paper'
    output_dir.mkdir(exist_ok=True)
    report_path = output_dir / 'registry_verification_report.md'
    with open(report_path, 'w') as f:
        f.write(report)

    # Write JSON for programmatic consumption
    json_path = output_dir / 'registry_verification.json'
    with open(json_path, 'w') as f:
        json.dump({'timestamp': timestamp, 'results': results}, f, indent=2, default=str)

    print(report)
    print(f"\nReport written to: {report_path}")
    print(f"JSON written to: {json_path}")


if __name__ == '__main__':
    main()
