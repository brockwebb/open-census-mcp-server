"""Stage 3: Pipeline Fidelity Verification (V2).

Loads three separate per-condition JSONL files (control, rag, pragmatics),
joins on query_id, and produces one FidelityRecord per query containing
fidelity and auditability results for all three conditions.

Govering requirements: SRS Section 8.5, VR-050 through VR-059.
"""

import argparse
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import defaultdict

import yaml
from dotenv import load_dotenv

from .judge_pipeline import get_api_caller, parse_judge_response
from .fidelity_prompts import build_treatment_prompt, build_control_prompt, build_rag_fidelity_prompt

# Load environment variables
load_dotenv()


def extract_slim_tool_data(tool_calls: list) -> list[dict]:
    """Extract only arguments and data from successful get_census_data calls.

    Strips out pragmatics, provenance, and other large fields to keep prompt
    size manageable (~1.5K instead of 100K+).

    Args:
        tool_calls: List of tool call dicts from ResponseRecord

    Returns:
        List of slim tool call dicts with only arguments and data
    """
    slim_calls = []
    for tc in tool_calls:
        # Handle both dict (from JSON) and object (from Pydantic)
        if isinstance(tc, dict):
            tool_name = tc.get('tool_name')
            arguments = tc.get('arguments', {})
            result = tc.get('result', {})
        else:
            tool_name = getattr(tc, 'tool_name', None)
            arguments = getattr(tc, 'arguments', {})
            result = getattr(tc, 'result', {})

        if tool_name in ('get_census_data', 'get_acs_data'):
            if isinstance(result, dict) and 'data' in result:
                slim_calls.append({
                    'arguments': arguments,
                    'data': result['data']
                })

    return slim_calls


def extract_rag_chunk_data(retrieved_chunks: list) -> str:
    """Format retrieved RAG chunks as verification evidence.

    Args:
        retrieved_chunks: List of chunk dicts from RAG ResponseRecord

    Returns:
        Formatted string of chunk text for verification prompt
    """
    if not retrieved_chunks:
        return ""

    parts = []
    for i, chunk in enumerate(retrieved_chunks, 1):
        source = chunk.get('source', 'unknown')
        section = chunk.get('section_path', [])
        section_str = ' > '.join(section) if section else 'N/A'
        page_start = chunk.get('page_start', '?')
        page_end = chunk.get('page_end', '?')
        if page_start == page_end:
            pages = f"p. {page_start}"
        else:
            pages = f"pp. {page_start}-{page_end}"
        score = chunk.get('score', 0)
        text = chunk.get('text', '')

        parts.append(
            f"[Chunk {i}] Source: {source}, {pages}, "
            f"Section: {section_str}, Similarity: {score:.3f}\n{text}"
        )

    return "\n\n---\n\n".join(parts)


def verify_treatment(
    query_id: str,
    response_text: str,
    tool_calls: list,
    config: Dict[str, Any],
    api_caller,
    **kwargs
) -> Dict[str, Any]:
    """Verify treatment response fidelity against tool call data or RAG chunks.

    Args:
        query_id: Query identifier
        response_text: Treatment response text
        tool_calls: List of tool calls made during treatment
        config: Fidelity configuration
        api_caller: API caller function from judge_pipeline
        **kwargs: Additional arguments (retrieved_chunks for RAG responses)

    Returns:
        Treatment fidelity result with claims and summary
    """
    # Extract slim tool data (arguments + data only)
    slim_calls = extract_slim_tool_data(tool_calls)

    # RAG responses: no tool calls, but have retrieved chunks
    retrieved_chunks = kwargs.get('retrieved_chunks', [])

    if not slim_calls and not retrieved_chunks:
        return {
            "has_data": False,
            "claims": [],
            "summary": {
                "total_claims": 0,
                "matched": 0,
                "mismatched": 0,
                "no_source": 0,
                "calculation_correct": 0,
                "calculation_incorrect": 0
            }
        }

    # Build verification prompt
    if slim_calls:
        # Existing path: verify against tool call data
        prompt = build_treatment_prompt(response_text, slim_calls)
    else:
        # RAG path: verify against retrieved chunks
        chunk_text = extract_rag_chunk_data(retrieved_chunks)
        prompt = build_rag_fidelity_prompt(response_text, chunk_text)

    # Call LLM via judge_pipeline infrastructure
    try:
        raw_response, _, _, _ = api_caller(prompt, config)
        result = parse_judge_response(raw_response)
    except Exception as e:
        print(f"  Treatment verification error: {str(e)[:80]}")
        result = None

    if not result or 'claims' not in result:
        return {
            "has_data": True,
            "claims": [],
            "summary": {
                "total_claims": 0,
                "matched": 0,
                "mismatched": 0,
                "no_source": 0,
                "calculation_correct": 0,
                "calculation_incorrect": 0
            },
            "error": "Failed to parse verification result"
        }

    # Compute summary statistics
    claims = result['claims']
    summary = {
        "total_claims": len(claims),
        "matched": sum(1 for c in claims if c.get('verdict') == 'match'),
        "mismatched": sum(1 for c in claims if c.get('verdict') == 'mismatch'),
        "no_source": sum(1 for c in claims if c.get('verdict') == 'no_source'),
        "calculation_correct": sum(1 for c in claims if c.get('verdict') == 'calculation_correct'),
        "calculation_incorrect": sum(1 for c in claims if c.get('verdict') == 'calculation_incorrect')
    }

    return {
        "has_data": True,
        "claims": claims,
        "summary": summary
    }


def classify_control(
    query_id: str,
    response_text: str,
    config: Dict[str, Any],
    api_caller
) -> Dict[str, Any]:
    """Classify control response auditability.

    Args:
        query_id: Query identifier
        response_text: Control response text
        config: Fidelity configuration
        api_caller: API caller function from judge_pipeline

    Returns:
        Control auditability result with claims and summary
    """
    # Build classification prompt
    prompt = build_control_prompt(response_text)

    # Call LLM via judge_pipeline infrastructure
    try:
        raw_response, _, _, _ = api_caller(prompt, config)
        result = parse_judge_response(raw_response)
    except Exception as e:
        print(f"  Control classification error: {str(e)[:80]}")
        result = None

    if not result or 'claims' not in result:
        return {
            "claims": [],
            "summary": {
                "total_claims": 0,
                "auditable": 0,
                "partially_auditable": 0,
                "unauditable": 0,
                "non_claims": 0
            },
            "error": "Failed to parse classification result"
        }

    # Compute summary statistics
    claims = result['claims']
    summary = {
        "total_claims": len(claims),
        "auditable": sum(1 for c in claims if c.get('specificity') == 'auditable'),
        "partially_auditable": sum(1 for c in claims if c.get('specificity') == 'partially_auditable'),
        "unauditable": sum(1 for c in claims if c.get('specificity') == 'unauditable'),
        "non_claims": sum(1 for c in claims if c.get('specificity') == 'non_claim')
    }

    return {
        "claims": claims,
        "summary": summary
    }


def process_query(
    query_id: str,
    conditions: Dict[str, Dict[str, Any]],
    query_metadata: Dict[str, Any],
    config: Dict[str, Any],
    api_caller
) -> Dict[str, Any]:
    """Process one query across all three conditions.

    Args:
        query_id: Query identifier
        conditions: Dict mapping condition name to ResponseRecord
                    {'control': {...}, 'rag': {...}, 'pragmatics': {...}}
        query_metadata: Dict with 'query_text' and 'category'
        config: Full configuration dict
        api_caller: API caller function from judge_pipeline

    Returns:
        FidelityRecord with results for all three conditions (VR-051)
    """
    print(f"  Processing {query_id}...")

    condition_results = {}
    for cond_name in ('control', 'rag', 'pragmatics'):
        record = conditions[cond_name]
        response_text = record.get('response_text', '')
        tool_calls = record.get('tool_calls', [])

        # Fidelity verification — RAG also uses retrieved_chunks (VR-056)
        if cond_name == 'rag':
            fidelity = verify_treatment(
                query_id, response_text, tool_calls, config['fidelity'], api_caller,
                retrieved_chunks=record.get('retrieved_chunks', [])
            )
        else:
            fidelity = verify_treatment(
                query_id, response_text, tool_calls, config['fidelity'], api_caller
            )

        # Auditability classification — symmetric for all conditions (VR-053)
        auditability = classify_control(
            query_id, response_text, config['fidelity'], api_caller
        )

        condition_results[cond_name] = {
            'fidelity': fidelity,
            'auditability': auditability
        }

    return {
        'query_id': query_id,
        'query_text': query_metadata['query_text'],
        'category': query_metadata['category'],
        'timestamp': datetime.now().isoformat(),
        'conditions': condition_results
    }


def load_existing_results(output_path: Path) -> set[str]:
    """Load already-processed query IDs from output file.

    Args:
        output_path: Path to output JSONL file

    Returns:
        Set of query IDs already processed
    """
    if not output_path.exists():
        return set()

    completed = set()
    with open(output_path) as f:
        for line in f:
            record = json.loads(line)
            completed.add(record['query_id'])

    return completed


def print_summary_statistics(output_path: Path):
    """Print 3-condition comparison table from completed fidelity checks.

    Args:
        output_path: Path to output JSONL file
    """
    if not output_path.exists():
        print("\nNo results to summarize.")
        return

    records = []
    with open(output_path) as f:
        for line in f:
            records.append(json.loads(line))

    if not records:
        print("\nNo results to summarize.")
        return

    print("\n" + "="*70)
    print("FIDELITY CHECK SUMMARY")
    print("="*70)

    CONDS = ['control', 'rag', 'pragmatics']

    # Aggregate stats per condition
    fid_stats = {c: defaultdict(int) for c in CONDS}
    aud_stats = {c: defaultdict(int) for c in CONDS}
    cat_stats = defaultdict(
        lambda: {c: {'fid': defaultdict(int), 'aud': defaultdict(int)} for c in CONDS}
    )

    for record in records:
        category = record['category']
        for cond in CONDS:
            cond_data = record.get('conditions', {}).get(cond, {})

            fid = cond_data.get('fidelity', {}).get('summary', {})
            for k, v in fid.items():
                fid_stats[cond][k] += v
                cat_stats[category][cond]['fid'][k] += v

            aud = cond_data.get('auditability', {}).get('summary', {})
            for k, v in aud.items():
                aud_stats[cond][k] += v
                cat_stats[category][cond]['aud'][k] += v

    def fidelity_score(stats: defaultdict):
        total = stats.get('total_claims', 0)
        if total == 0:
            return 0.0, 0
        return (stats.get('matched', 0) + stats.get('calculation_correct', 0)) / total * 100, total

    def error_rate(stats: defaultdict):
        total = stats.get('total_claims', 0)
        if total == 0:
            return 0.0
        return (stats.get('mismatched', 0) + stats.get('calculation_incorrect', 0)) / total * 100

    def audit_rate(stats: defaultdict):
        total = stats.get('total_claims', 0)
        non_claims = stats.get('non_claims', 0)
        denom = total - non_claims
        if denom == 0:
            return 0.0
        return stats.get('auditable', 0) / denom * 100

    # 3-column comparison table
    COL_W = 14
    header = f"{'Metric':<22}" + "".join(f"{c.capitalize():>{COL_W}}" for c in CONDS)
    print(f"\n{header}")
    print("-" * (22 + COL_W * 3))

    fs = {c: fidelity_score(fid_stats[c]) for c in CONDS}
    print(f"{'Fidelity Score':<22}" + "".join(f"{fs[c][0]:>{COL_W-1}.1f}%" for c in CONDS))
    print(f"{'Error Rate':<22}" + "".join(f"{error_rate(fid_stats[c]):>{COL_W-1}.1f}%" for c in CONDS))
    print(f"{'Auditability':<22}" + "".join(f"{audit_rate(aud_stats[c]):>{COL_W-1}.1f}%" for c in CONDS))
    print(f"{'Total Claims':<22}" + "".join(f"{fid_stats[c].get('total_claims', 0):>{COL_W}}" for c in CONDS))

    # Per-category breakdown
    print("\n## Per-Category Breakdown")
    for category in sorted(cat_stats.keys()):
        stats = cat_stats[category]
        print(f"\n  {category}")
        for cond in CONDS:
            fs_cat, n = fidelity_score(stats[cond]['fid'])
            ar_cat = audit_rate(stats[cond]['aud'])
            if n > 0:
                print(f"    {cond:<14} fidelity: {fs_cat:.1f}% ({n} claims)  auditability: {ar_cat:.1f}%")

    print("\n" + "="*70)


def main():
    """Main entry point for fidelity check pipeline (V2)."""
    parser = argparse.ArgumentParser(description="Stage 3: Pipeline Fidelity Verification (V2)")
    parser.add_argument(
        "--config",
        default="src/eval/judge_config.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--batch",
        type=int,
        help="Process only first N queries (for testing)"
    )

    args = parser.parse_args()

    # Load configuration
    with open(args.config) as f:
        config = yaml.safe_load(f)

    if 'fidelity' not in config:
        print("ERROR: No 'fidelity' section in config file")
        return

    # Get API caller for the fidelity provider
    provider = config['fidelity']['provider']
    api_caller = get_api_caller(provider)

    # Output path
    output_dir = Path(config['paths']['stage3_output_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"fidelity_{timestamp}.jsonl"

    print("="*70)
    print("STAGE 3: PIPELINE FIDELITY VERIFICATION (V2)")
    print("="*70)
    print(f"Model: {config['fidelity']['model']} ({provider})")

    # Load all 3 condition files (VR-050)
    stage3_inputs = config['paths']['stage3_inputs']
    condition_records: Dict[str, Dict[str, Any]] = {}  # {cond: {query_id: record}}

    for cond_name, file_path in stage3_inputs.items():
        path = Path(file_path)
        if not path.exists():
            print(f"\nERROR: Input file not found: {path}")
            return
        records: Dict[str, Any] = {}
        with open(path) as f:
            for line in f:
                record = json.loads(line)
                records[record['query_id']] = record
        condition_records[cond_name] = records
        print(f"  {cond_name}: {len(records)} records")

    # Validate all 3 files have the same query IDs
    all_id_sets = [set(r.keys()) for r in condition_records.values()]
    common_ids = set.intersection(*all_id_sets)
    for cond_name, records in condition_records.items():
        missing = common_ids - set(records.keys())
        if missing:
            print(f"WARNING: {cond_name} missing query IDs: {missing}")
        extra = set(records.keys()) - common_ids
        if extra:
            print(f"WARNING: {cond_name} has extra query IDs not in all files: {extra}")

    query_ids = sorted(common_ids)
    print(f"\nLoaded {len(query_ids)} queries present in all 3 conditions")

    # Load query metadata from battery (query_text, category)
    battery_path = Path(config['paths']['battery'])
    with open(battery_path) as f:
        battery = yaml.safe_load(f)
    battery_meta = {
        q['id']: {'query_text': q['text'], 'category': q['category']}
        for q in battery['queries']
    }

    # Apply batch limit if specified
    if args.batch:
        query_ids = query_ids[:args.batch]
        print(f"Processing first {args.batch} queries only (test mode)")

    # Load existing results for checkpointing
    completed = load_existing_results(output_path)
    if completed:
        print(f"Skipping {len(completed)} already-completed queries")

    print(f"Output: {output_path}")

    # Process each query (6 LLM calls per query: 2 per condition × 3 conditions)
    processed = 0
    with open(output_path, 'a') as out_f:
        for i, query_id in enumerate(query_ids, 1):
            if query_id in completed:
                continue

            print(f"\n[{i}/{len(query_ids)}] {query_id}")

            # Build conditions dict for this query
            conditions = {
                cond_name: condition_records[cond_name][query_id]
                for cond_name in ('control', 'rag', 'pragmatics')
            }

            # Get query metadata from battery (ResponseRecords don't carry query_text/category)
            query_metadata = battery_meta.get(query_id, {'query_text': '', 'category': 'unknown'})

            result = process_query(query_id, conditions, query_metadata, config, api_caller)

            # Write immediately for checkpointing
            out_f.write(json.dumps(result) + '\n')
            out_f.flush()

            processed += 1

            # Rate limiting
            time.sleep(config['fidelity'].get('rate_limit_delay', 0.5))

    print(f"\n\nProcessed {processed} queries")
    print_summary_statistics(output_path)
    print(f"\nComplete! Results: {output_path}")


if __name__ == '__main__':
    main()
