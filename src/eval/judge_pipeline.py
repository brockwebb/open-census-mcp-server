"""Judge Scoring Pipeline - Stage 2 of CQS Evaluation.

V2: Pairwise comparison design. Three comparisons scored independently:
  - rag_vs_pragmatics (core research question)
  - control_vs_pragmatics
  - control_vs_rag

Multi-vendor LLM judge panel scores condition_a vs condition_b responses
on 6-dimension Consultation Quality Score (CQS) rubric.

Implements position bias mitigation, test-retest reliability, and
comprehensive checkpointing per author's validated methodology.
"""

import os
import json
import time
import random
import re
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import yaml
from dotenv import load_dotenv
from tqdm import tqdm

from .models import ComparisonPair, ResponseRecord, JudgeRecord, DimensionScore
from .judge_prompts import build_judge_prompt

# Load environment variables
load_dotenv()

# Thread locks for concurrent writes
write_lock = threading.Lock()
checkpoint_lock = threading.Lock()

# Valid comparison names
VALID_COMPARISONS = {'rag_vs_pragmatics', 'control_vs_pragmatics', 'control_vs_rag'}


# =============================================================================
# API CALLERS
# =============================================================================

def call_anthropic(prompt: str, config: Dict, max_retries: int = 5) -> Tuple[str, int, int, float]:
    """Call Anthropic Claude API with exponential backoff.

    Returns:
        (response_text, input_tokens, output_tokens, latency_ms)
    """
    import anthropic

    model = config['model']
    max_tokens = config.get('max_tokens', 4096)
    temperature = config.get('temperature', 0.0)

    client = anthropic.Anthropic(api_key=os.getenv(config['api_key_env']))

    for attempt in range(max_retries):
        try:
            start_time = time.time()
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            latency_ms = (time.time() - start_time) * 1000

            content = response.content[0].text
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens

            return content, input_tokens, output_tokens, latency_ms

        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"  Anthropic error: {str(e)[:80]}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise RuntimeError(f"Anthropic failed after {max_retries} attempts: {e}")

    raise RuntimeError("Unreachable")


def call_openai(prompt: str, config: Dict, max_retries: int = 5) -> Tuple[str, int, int, float]:
    """Call OpenAI API with exponential backoff.

    IMPORTANT: Some OpenAI models don't accept temperature parameter.
    Config specifies whether to include it.

    Returns:
        (response_text, input_tokens, output_tokens, latency_ms)
    """
    from openai import OpenAI

    model = config['model']
    temperature = config.get('temperature')  # May be None
    max_tokens_param = config.get('max_tokens_param', 'max_tokens')
    max_tokens = config.get('max_tokens', 4096)

    client = OpenAI(api_key=os.getenv(config['api_key_env']))

    for attempt in range(max_retries):
        try:
            start_time = time.time()

            # Build kwargs conditionally
            kwargs = {
                'model': model,
                'messages': [
                    {"role": "system", "content": "You are an expert in federal statistical data quality assessment, specializing in Census Bureau methodology."},
                    {"role": "user", "content": prompt}
                ]
            }

            # Add max_tokens with correct parameter name
            kwargs[max_tokens_param] = max_tokens

            # Only add temperature if specified
            if temperature is not None:
                kwargs['temperature'] = temperature

            response = client.chat.completions.create(**kwargs)
            latency_ms = (time.time() - start_time) * 1000

            content = response.choices[0].message.content

            if content is None or content == '':
                raise ValueError(f"Empty response from {model}")

            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens

            return content, input_tokens, output_tokens, latency_ms

        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"  OpenAI error: {str(e)[:80]}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise RuntimeError(f"OpenAI failed after {max_retries} attempts: {e}")

    raise RuntimeError("Unreachable")


def call_google(prompt: str, config: Dict, max_retries: int = 5) -> Tuple[str, int, int, float]:
    """Call Google Gemini API with exponential backoff.

    Returns:
        (response_text, input_tokens, output_tokens, latency_ms)
    """
    try:
        from google import genai
    except ImportError:
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError(
                "Neither google-genai nor google-generativeai is installed. "
                "Run: pip install google-genai"
            )

    model = config['model']
    max_tokens = config.get('max_tokens', 4096)
    temperature = config.get('temperature', 1.0)

    api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY not set")

    client = genai.Client(api_key=api_key)

    for attempt in range(max_retries):
        try:
            start_time = time.time()
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config={
                    'response_mime_type': 'application/json',
                    'max_output_tokens': max_tokens,
                    'temperature': temperature,
                }
            )
            latency_ms = (time.time() - start_time) * 1000

            content = response.text.strip()

            # Check for truncated JSON before returning
            try:
                json.loads(content)
            except json.JSONDecodeError:
                raise ValueError(f"Truncated JSON response ({len(content)} chars)")

            # Gemini doesn't provide token counts in response
            # Rough estimate: 1 token ≈ 4 chars
            input_tokens = len(prompt) // 4
            output_tokens = len(content) // 4

            return content, input_tokens, output_tokens, latency_ms

        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"  Google error: {str(e)[:80]}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise RuntimeError(f"Google failed after {max_retries} attempts: {e}")

    raise RuntimeError("Unreachable")


def get_api_caller(provider: str):
    """Get the appropriate API caller function."""
    callers = {
        'anthropic': call_anthropic,
        'openai': call_openai,
        'google': call_google
    }
    if provider not in callers:
        raise ValueError(f"Unknown provider: {provider}")
    return callers[provider]


# =============================================================================
# JSON PARSING
# =============================================================================

def parse_judge_response(raw_response: str) -> Optional[Dict]:
    """Robust parsing of judge JSON response.

    Tries multiple strategies:
    1. Direct json.loads
    2. Extract from markdown code blocks
    3. Regex extraction of JSON object

    Returns:
        Parsed dict or None if parsing fails
    """
    # Clean control characters
    cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', raw_response)

    # Strategy 1: Direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Extract from markdown code blocks
    if '```json' in cleaned:
        parts = cleaned.split('```json')
        if len(parts) > 1:
            json_part = parts[1].split('```')[0].strip()
            try:
                return json.loads(json_part)
            except json.JSONDecodeError:
                pass

    # Strategy 3: Find first { to last }
    start = cleaned.find('{')
    end = cleaned.rfind('}')
    if start != -1 and end != -1:
        try:
            return json.loads(cleaned[start:end+1])
        except json.JSONDecodeError:
            pass

    return None


def validate_judge_response(data: Dict) -> bool:
    """Validate that parsed JSON has expected structure.

    Required keys:
    - response_a with D1-D6
    - response_b with D1-D6
    - overall_preference
    - preference_reasoning

    Each dimension must have score (0-2), confidence (1-5), and reasoning.
    """
    if not isinstance(data, dict):
        return False

    required_keys = {'response_a', 'response_b', 'overall_preference', 'preference_reasoning'}
    if not required_keys.issubset(data.keys()):
        return False

    dimensions = ['D1', 'D2', 'D3', 'D4', 'D5', 'D6']

    for response_key in ['response_a', 'response_b']:
        response_data = data[response_key]
        if not isinstance(response_data, dict):
            return False

        for dim in dimensions:
            if dim not in response_data:
                return False

            dim_data = response_data[dim]
            if not isinstance(dim_data, dict):
                return False

            if not all(k in dim_data for k in ['score', 'confidence', 'reasoning']):
                return False

            # Validate score range
            if not isinstance(dim_data['score'], int) or dim_data['score'] not in [0, 1, 2]:
                return False

            # Validate confidence range
            if not isinstance(dim_data['confidence'], int) or dim_data['confidence'] not in [1, 2, 3, 4, 5]:
                return False

    return True


# =============================================================================
# CHECKPOINTING
# =============================================================================

def get_checkpoint_path(config: Dict, comparison: str) -> Path:
    """Get checkpoint file path, scoped by comparison name."""
    checkpoint_dir = Path(config['paths']['checkpoint_dir'])
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    return checkpoint_dir / f'judge_checkpoint_{comparison}.json'


def load_checkpoint(checkpoint_path: Path) -> set:
    """Load checkpoint - returns set of completed (query_id, judge_key, ordering, pass_number) tuples."""
    if checkpoint_path.exists():
        try:
            with open(checkpoint_path) as f:
                data = json.load(f)
                return set(tuple(item) for item in data.get('completed', []))
        except Exception as e:
            print(f"Warning: Corrupted checkpoint, starting fresh: {e}")
            return set()
    return set()


def save_checkpoint(checkpoint_path: Path, completed: set):
    """Save checkpoint."""
    with open(checkpoint_path, 'w') as f:
        json.dump({
            'completed': [list(item) for item in completed],
            'last_updated': datetime.utcnow().isoformat()
        }, f)


# =============================================================================
# V2 DATA LOADING
# =============================================================================

def load_comparison_pairs(config: Dict, comparison: str) -> List[ComparisonPair]:
    """Load V2 comparison pairs from two condition files + battery.

    Reads:
    - Two JSONL response files (one per condition)
    - queries.yaml for query text and metadata

    Joins on query_id. Validates all 39 queries present in both files.

    Returns:
        List of ComparisonPair objects
    """
    comp_config = config['comparisons'][comparison]
    file_a = Path(comp_config['file_a'])
    file_b = Path(comp_config['file_b'])
    condition_a_name = comp_config['condition_a']
    condition_b_name = comp_config['condition_b']

    # Load battery for query metadata
    battery_path = Path(config['paths']['battery'])
    with open(battery_path) as f:
        battery = yaml.safe_load(f)

    query_meta = {}
    for q in battery['queries']:
        query_meta[q['id']] = {
            'text': q['text'],
            'category': q['category'],
            'difficulty': q['difficulty'],
        }

    # Load condition A responses
    responses_a = {}
    with open(file_a) as f:
        for line in f:
            record = ResponseRecord(**json.loads(line))
            responses_a[record.query_id] = record

    # Load condition B responses
    responses_b = {}
    with open(file_b) as f:
        for line in f:
            record = ResponseRecord(**json.loads(line))
            responses_b[record.query_id] = record

    # Validate completeness
    all_query_ids = set(query_meta.keys())
    missing_a = all_query_ids - set(responses_a.keys())
    missing_b = all_query_ids - set(responses_b.keys())

    if missing_a:
        print(f"WARNING: {len(missing_a)} queries missing from {condition_a_name}: {sorted(missing_a)}")
    if missing_b:
        print(f"WARNING: {len(missing_b)} queries missing from {condition_b_name}: {sorted(missing_b)}")

    # Build pairs (only for queries present in both files)
    common_ids = set(responses_a.keys()) & set(responses_b.keys()) & all_query_ids
    pairs = []
    for qid in sorted(common_ids):
        meta = query_meta[qid]
        pairs.append(ComparisonPair(
            query_id=qid,
            query_text=meta['text'],
            category=meta['category'],
            difficulty=meta['difficulty'],
            condition_a=responses_a[qid],
            condition_b=responses_b[qid],
            condition_a_name=condition_a_name,
            condition_b_name=condition_b_name,
        ))

    print(f"Loaded {len(pairs)} comparison pairs for {comparison}")
    print(f"  {condition_a_name}: {file_a}")
    print(f"  {condition_b_name}: {file_b}")

    return pairs


# =============================================================================
# CONCURRENT TASK PROCESSING
# =============================================================================

def score_single_task(
    task: Tuple[str, str, str, int],
    config: Dict,
    pair_map: Dict[str, ComparisonPair],
    comparison: str,
    run_id: str,
    rate_limit_delay: float
) -> Tuple[JudgeRecord, Tuple]:
    """Score a single comparison pair with one judge.

    Args:
        task: (query_id, judge_key, ordering, pass_num)
        config: Full configuration dict
        pair_map: Map of query_id to ComparisonPair
        comparison: Comparison name (e.g., 'rag_vs_pragmatics')
        run_id: Run identifier
        rate_limit_delay: Delay between API calls (seconds)

    Returns:
        (JudgeRecord, task_tuple) for checkpointing
    """
    query_id, judge_key, ordering, pass_num = task

    # Get config for this judge
    judge_config = config['judges'][judge_key].copy()
    # Per-vendor max_output_tokens overrides pipeline default
    judge_config['max_tokens'] = judge_config.get('max_output_tokens',
        config['pipeline'].get('max_tokens', 4096))

    # Get comparison pair
    pair = pair_map[query_id]

    # Determine A/B assignment based on ordering
    if ordering == 'condition_a_first':
        response_a = pair.condition_a.response_text
        response_b = pair.condition_b.response_text
        label_a = pair.condition_a_name
        label_b = pair.condition_b_name
    else:  # condition_b_first
        response_a = pair.condition_b.response_text
        response_b = pair.condition_a.response_text
        label_a = pair.condition_b_name
        label_b = pair.condition_a_name

    # Build prompt
    prompt = build_judge_prompt(pair.query_text, response_a, response_b)

    # Call API
    api_caller = get_api_caller(judge_config['provider'])
    raw_response, input_tokens, output_tokens, latency_ms = api_caller(prompt, judge_config)

    # Parse response
    parsed = parse_judge_response(raw_response)
    parse_success = parsed is not None and validate_judge_response(parsed)

    if parse_success:
        # Convert to DimensionScore objects
        scores_a = {}
        scores_b = {}
        for dim in ['D1', 'D2', 'D3', 'D4', 'D5', 'D6']:
            scores_a[dim] = DimensionScore(**parsed['response_a'][dim])
            scores_b[dim] = DimensionScore(**parsed['response_b'][dim])

        preference = parsed.get('overall_preference', 'tie')
        preference_reasoning = parsed.get('preference_reasoning', '')
    else:
        # Failed parse - store empty scores
        scores_a = {}
        scores_b = {}
        preference = 'parse_failed'
        preference_reasoning = 'JSON parse failed'

    # Create JudgeRecord
    record = JudgeRecord(
        query_id=query_id,
        judge_model=judge_config['model'],
        judge_vendor=judge_config['provider'],
        presentation_order=ordering,
        scores_response_a=scores_a,
        scores_response_b=scores_b,
        preference=preference,
        preference_reasoning=preference_reasoning,
        response_a_label=label_a,
        response_b_label=label_b,
        comparison=comparison,
        latency_ms=latency_ms,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        timestamp=datetime.utcnow(),
        run_id=run_id,
        raw_response=raw_response[:10000],  # Truncate for storage
        parse_success=parse_success,
        pass_number=pass_num
    )

    # Rate limiting (per-vendor)
    time.sleep(rate_limit_delay)

    return record, task


def process_vendor(
    vendor_key: str,
    vendor_tasks: List[Tuple],
    config: Dict,
    pair_map: Dict[str, ComparisonPair],
    comparison: str,
    run_id: str,
    output_file: Path,
    completed: set,
    checkpoint_path: Path
) -> Tuple[int, int]:
    """Process all tasks for one vendor with concurrent workers.

    Args:
        vendor_key: Judge vendor name (anthropic, openai, google)
        vendor_tasks: List of tasks for this vendor
        config: Full configuration dict
        pair_map: Map of query_id to ComparisonPair
        comparison: Comparison name
        run_id: Run identifier
        output_file: Path to output JSONL
        completed: Set of completed task tuples
        checkpoint_path: Path to checkpoint file

    Returns:
        (successful_count, failed_count)
    """
    max_workers = config['pipeline'].get('max_workers_per_vendor', 3)
    rate_limit_delay = config['pipeline'].get('rate_limit_delay', 1.0)
    checkpoint_interval = config['pipeline'].get('checkpoint_interval', 10)

    successful = 0
    failed = 0

    def process_task_wrapper(task):
        """Wrapper for score_single_task."""
        try:
            return score_single_task(task, config, pair_map, comparison, run_id, rate_limit_delay)
        except Exception as e:
            query_id, judge_key, ordering, pass_num = task
            print(f"\n{vendor_key} failed: {query_id}, {ordering}, pass {pass_num}: {str(e)[:80]}")
            return None, task

    print(f"\n{vendor_key}: Processing {len(vendor_tasks)} tasks with {max_workers} workers...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_task = {
            executor.submit(process_task_wrapper, task): task
            for task in vendor_tasks
        }

        with tqdm(total=len(vendor_tasks), desc=f"  {vendor_key}") as pbar:
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    record, task_tuple = future.result()

                    if record is not None:
                        # Thread-safe JSONL write
                        with write_lock:
                            with open(output_file, 'a') as f:
                                f.write(record.model_dump_json() + '\n')

                        # Thread-safe checkpoint update
                        with checkpoint_lock:
                            completed.add(task_tuple)
                            successful += 1

                            if successful % checkpoint_interval == 0:
                                save_checkpoint(checkpoint_path, completed)
                    else:
                        failed += 1

                except Exception as e:
                    print(f"\n{vendor_key} exception: {str(e)[:80]}")
                    failed += 1

                pbar.update(1)

    # Final checkpoint for this vendor
    with checkpoint_lock:
        save_checkpoint(checkpoint_path, completed)

    print(f"\n{vendor_key} complete: {successful} successful, {failed} failed")
    return successful, failed


def run_pipeline(
    config_path: str = 'src/eval/judge_config.yaml',
    comparison: str = 'rag_vs_pragmatics',
    vendor_filter: Optional[set] = None,
    batch_limit: Optional[int] = None,
):
    """Main judge scoring pipeline.

    Args:
        config_path: Path to YAML config file
        comparison: Which pairwise comparison to run
        vendor_filter: If set, only run these vendors (e.g., {'anthropic', 'openai'})
        batch_limit: Max number of tasks to run (None = all)
    """

    if comparison not in VALID_COMPARISONS:
        print(f"ERROR: Invalid comparison '{comparison}'. Valid: {sorted(VALID_COMPARISONS)}")
        return

    print("="*60)
    print(f"JUDGE SCORING PIPELINE - Stage 2 (V2)")
    print(f"Comparison: {comparison}")
    print("="*60)

    # Load config
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Validate comparison exists in config
    if comparison not in config.get('comparisons', {}):
        print(f"ERROR: Comparison '{comparison}' not found in config. "
              f"Available: {list(config.get('comparisons', {}).keys())}")
        return

    comp_config = config['comparisons'][comparison]
    print(f"\n  {comp_config['condition_a']} vs {comp_config['condition_b']}")
    if comp_config.get('notes'):
        print(f"  Note: {comp_config['notes']}")

    # Setup output directory
    output_dir = Path(config['paths']['output_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f'{comparison}_{timestamp}.jsonl'
    run_id = f"{comparison}_{timestamp}"

    print(f"\nRun ID: {run_id}")
    print(f"Output: {output_file}")

    # Load comparison pairs
    pairs = load_comparison_pairs(config, comparison)

    if not pairs:
        print("ERROR: No comparison pairs loaded. Check file paths.")
        return

    # Load checkpoint (scoped by comparison)
    checkpoint_path = get_checkpoint_path(config, comparison)
    completed = load_checkpoint(checkpoint_path)
    print(f"\nCheckpoint: {len(completed)} tasks already completed")

    # Seed RNG for reproducibility
    random.seed(config['pipeline']['random_seed'])

    # Determine active judges
    active_judges = set(config['judges'].keys())
    if vendor_filter:
        active_judges = active_judges & vendor_filter
        if not active_judges:
            print(f"\nERROR: No matching judges. Available: {list(config['judges'].keys())}")
            return
        print(f"Vendor filter: {sorted(active_judges)}")

    # Build task list with 6-pass design
    num_passes = config['pipeline'].get('num_passes', 6)
    tasks = []
    for pair in pairs:
        for judge_key in active_judges:
            for pass_num in range(1, num_passes + 1):
                # Alternate ordering: odd = condition_a_first, even = condition_b_first
                ordering = 'condition_a_first' if pass_num % 2 == 1 else 'condition_b_first'
                tasks.append((pair.query_id, judge_key, ordering, pass_num))

    # Filter to uncompleted tasks
    remaining_tasks = [
        task for task in tasks
        if task not in completed  # Full tuple match including pass_number
    ]

    # Apply batch limit
    if batch_limit and batch_limit < len(remaining_tasks):
        remaining_tasks = remaining_tasks[:batch_limit]
        print(f"Batch limit: {batch_limit} tasks")

    total_tasks = len(tasks)
    remaining = len(remaining_tasks)

    print(f"\nTotal tasks: {total_tasks}")
    print(f"Remaining: {remaining}")

    if remaining == 0:
        print("\nAll tasks complete!")
        return

    # Process tasks with vendor-level parallelism
    pair_map = {pair.query_id: pair for pair in pairs}

    # Split tasks by vendor
    vendor_task_map = {judge_key: [] for judge_key in active_judges}
    for task in remaining_tasks:
        query_id, judge_key, ordering, pass_num = task
        vendor_task_map[judge_key].append(task)

    print(f"\nTasks per vendor:")
    for vendor_key, vendor_tasks in vendor_task_map.items():
        print(f"  {vendor_key}: {len(vendor_tasks)}")

    # Process each vendor in parallel
    successful = 0
    failed = 0

    with ThreadPoolExecutor(max_workers=3) as vendor_executor:
        vendor_futures = {}
        for vendor_key, vendor_tasks in vendor_task_map.items():
            if len(vendor_tasks) > 0:
                future = vendor_executor.submit(
                    process_vendor,
                    vendor_key,
                    vendor_tasks,
                    config,
                    pair_map,
                    comparison,
                    run_id,
                    output_file,
                    completed,
                    checkpoint_path
                )
                vendor_futures[future] = vendor_key

        # Wait for all vendors to complete
        for future in as_completed(vendor_futures):
            vendor_key = vendor_futures[future]
            try:
                vendor_successful, vendor_failed = future.result()
                successful += vendor_successful
                failed += vendor_failed
            except Exception as e:
                print(f"\n{vendor_key} vendor executor failed: {str(e)[:100]}")

    # Final checkpoint
    with checkpoint_lock:
        save_checkpoint(checkpoint_path, completed)

    print(f"\n{'='*60}")
    print("PIPELINE COMPLETE")
    print(f"{'='*60}")
    print(f"Comparison: {comparison}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Output: {output_file}")
    if successful > 0:
        print(f"Parse success rate: {(successful-failed)/successful*100:.1f}%")


def main():
    """Entry point with CLI arguments."""
    import argparse

    parser = argparse.ArgumentParser(description='Judge Scoring Pipeline - Stage 2 (V2)')
    parser.add_argument('--config', default='src/eval/judge_config.yaml',
                        help='Path to judge config YAML')
    parser.add_argument('--comparison', required=True,
                        choices=sorted(VALID_COMPARISONS),
                        help='Which pairwise comparison to run')
    parser.add_argument('--anthropic', action='store_true',
                        help='Run Anthropic judge only')
    parser.add_argument('--openai', action='store_true',
                        help='Run OpenAI judge only')
    parser.add_argument('--google', action='store_true',
                        help='Run Google judge only')
    parser.add_argument('--batch', type=int, default=None,
                        help='Max tasks to run (default: all remaining)')

    args = parser.parse_args()

    # Determine which vendors to run
    vendor_filter = set()
    if args.anthropic:
        vendor_filter.add('anthropic')
    if args.openai:
        vendor_filter.add('openai')
    if args.google:
        vendor_filter.add('google')
    # Empty means all

    run_pipeline(
        config_path=args.config,
        comparison=args.comparison,
        vendor_filter=vendor_filter if vendor_filter else None,
        batch_limit=args.batch,
    )


if __name__ == '__main__':
    main()
