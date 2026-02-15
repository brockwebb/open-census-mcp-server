"""Stage 3: Pipeline Fidelity Verification.

Verifies treatment response accuracy against tool call data and classifies
control response auditability. Uses existing judge_pipeline infrastructure.
"""

import argparse
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
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
    pair: Dict[str, Any],
    config: Dict[str, Any],
    api_caller
) -> Dict[str, Any]:
    """Process one query pair for fidelity checking.

    Args:
        pair: QueryPair dict with control and treatment responses
        config: Full configuration dict
        api_caller: API caller function from judge_pipeline

    Returns:
        Fidelity result for this query
    """
    query_id = pair['query_id']
    query_text = pair['query_text']
    category = pair['category']

    print(f"  Processing {query_id}...")

    # Verify treatment
    treatment = pair['treatment']
    treatment_result = verify_treatment(
        query_id,
        treatment['response_text'],
        treatment['tool_calls'],
        config['fidelity'],
        api_caller,
        retrieved_chunks=treatment.get('retrieved_chunks', [])
    )

    # Classify treatment auditability (same measure as control, for symmetry)
    treatment_auditability = classify_control(
        query_id,
        treatment["response_text"],
        config["fidelity"],
        api_caller
    )

    # Classify control
    control = pair['control']
    control_result = classify_control(
        query_id,
        control['response_text'],
        config['fidelity'],
        api_caller
    )

    return {
        "query_id": query_id,
        "query_text": query_text,
        "category": category,
        "timestamp": datetime.now().isoformat(),
        "treatment_fidelity": treatment_result,
        "treatment_auditability": treatment_auditability,
        "control_auditability": control_result
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
    """Print aggregate statistics from completed fidelity checks.

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

    # Treatment statistics
    treatment_stats = defaultdict(int)
    control_stats = defaultdict(int)
    category_stats = defaultdict(lambda: {'treatment': defaultdict(int), 'control': defaultdict(int)})

    for record in records:
        category = record['category']

        # Treatment
        tf = record['treatment_fidelity']['summary']
        for key, val in tf.items():
            treatment_stats[key] += val
            category_stats[category]['treatment'][key] += val

        # Control
        ca = record['control_auditability']['summary']
        for key, val in ca.items():
            control_stats[key] += val
            category_stats[category]['control'][key] += val

    # Overall treatment fidelity
    print("\n## Treatment Fidelity")
    total = treatment_stats['total_claims']
    if total > 0:
        match_rate = treatment_stats['matched'] / total * 100
        calc_correct_rate = treatment_stats['calculation_correct'] / total * 100
        fidelity_score = (treatment_stats['matched'] + treatment_stats['calculation_correct']) / total * 100

        print(f"Total claims: {total}")
        print(f"Matched: {treatment_stats['matched']} ({match_rate:.1f}%)")
        print(f"Mismatched: {treatment_stats['mismatched']}")
        print(f"No source: {treatment_stats['no_source']}")
        print(f"Calculation correct: {treatment_stats['calculation_correct']} ({calc_correct_rate:.1f}%)")
        print(f"Calculation incorrect: {treatment_stats['calculation_incorrect']}")
        print(f"**Fidelity score: {fidelity_score:.1f}%**")
    else:
        print("No treatment claims found.")

    # Overall control auditability
    print("\n## Control Auditability")
    total = control_stats['total_claims']
    if total > 0:
        audit_rate = control_stats['auditable'] / total * 100

        print(f"Total claims: {total}")
        print(f"Auditable: {control_stats['auditable']} ({audit_rate:.1f}%)")
        print(f"Partially auditable: {control_stats['partially_auditable']}")
        print(f"Unauditable: {control_stats['unauditable']}")
        print(f"Non-claims: {control_stats['non_claims']}")
    else:
        print("No control claims found.")

    # Per-category breakdown
    print("\n## Per-Category Breakdown")
    for category in sorted(category_stats.keys()):
        stats = category_stats[category]
        print(f"\n### {category}")

        t_total = stats['treatment']['total_claims']
        c_total = stats['control']['total_claims']

        if t_total > 0:
            t_fidelity = (stats['treatment']['matched'] + stats['treatment']['calculation_correct']) / t_total * 100
            print(f"  Treatment fidelity: {t_fidelity:.1f}% ({t_total} claims)")

        if c_total > 0:
            c_audit = stats['control']['auditable'] / c_total * 100
            print(f"  Control auditability: {c_audit:.1f}% ({c_total} claims)")

    print("\n" + "="*70)


def main():
    """Main entry point for fidelity check pipeline."""
    parser = argparse.ArgumentParser(description="Stage 3: Pipeline Fidelity Verification")
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
    parser.add_argument(
        "--input",
        help="Override input file path (defaults to config stage1_results)"
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

    # Determine input/output paths
    input_path = Path(args.input) if args.input else Path(config['paths']['stage1_results'])
    output_dir = Path(config['paths']['stage3_output_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"fidelity_{timestamp}.jsonl"

    print("="*70)
    print("STAGE 3: PIPELINE FIDELITY VERIFICATION")
    print("="*70)
    print(f"\nInput: {input_path}")
    print(f"Output: {output_path}")
    print(f"Model: {config['fidelity']['model']} ({provider})")

    # Load Stage 1 results
    if not input_path.exists():
        print(f"\nERROR: Input file not found: {input_path}")
        return

    pairs = []
    with open(input_path) as f:
        for line in f:
            pairs.append(json.loads(line))

    print(f"\nLoaded {len(pairs)} query pairs")

    # Apply batch limit if specified
    if args.batch:
        pairs = pairs[:args.batch]
        print(f"Processing first {args.batch} queries only (test mode)")

    # Load existing results for checkpointing
    completed = load_existing_results(output_path)
    if completed:
        print(f"Skipping {len(completed)} already-completed queries")

    # Process each query
    processed = 0
    with open(output_path, 'a') as out_f:
        for i, pair in enumerate(pairs, 1):
            query_id = pair['query_id']

            if query_id in completed:
                continue

            print(f"\n[{i}/{len(pairs)}] {query_id}")

            result = process_query(pair, config, api_caller)

            # Write immediately for checkpointing
            out_f.write(json.dumps(result) + '\n')
            out_f.flush()

            processed += 1

            # Rate limiting
            time.sleep(config['fidelity'].get('rate_limit_delay', 0.5))

    print(f"\n\nProcessed {processed} queries")

    # Print summary statistics
    print_summary_statistics(output_path)

    print(f"\nComplete! Results: {output_path}")


if __name__ == '__main__':
    main()
