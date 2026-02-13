"""Judge Scoring Pipeline - Stage 2 of CQS Evaluation.

Multi-vendor LLM judge panel scores control vs treatment responses
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

from .models import QueryPair, JudgeRecord, DimensionScore
from .judge_prompts import build_judge_prompt

# Load environment variables
load_dotenv()

# Thread locks for concurrent writes
write_lock = threading.Lock()
checkpoint_lock = threading.Lock()

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

def get_checkpoint_path(config: Dict) -> Path:
    """Get checkpoint file path."""
    checkpoint_dir = Path(config['paths']['checkpoint_dir'])
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    return checkpoint_dir / 'judge_checkpoint.json'


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
# MAIN PIPELINE
# =============================================================================

def load_query_pairs(config: Dict) -> List[QueryPair]:
    """Load Stage 1 query pairs from JSONL."""
    results_path = Path(config['paths']['stage1_results'])

    pairs = []
    with open(results_path) as f:
        for line in f:
            data = json.loads(line)
            # Parse nested ResponseRecords
            pairs.append(QueryPair(**data))

    print(f"Loaded {len(pairs)} query pairs from {results_path}")
    return pairs


# =============================================================================
# CONCURRENT TASK PROCESSING
# =============================================================================

def score_single_task(
    task: Tuple[str, str, str, int],
    config: Dict,
    query_pair_map: Dict[str, QueryPair],
    run_id: str,
    rate_limit_delay: float
) -> Tuple[JudgeRecord, Tuple]:
    """Score a single query pair with one judge.

    Args:
        task: (query_id, judge_key, ordering, pass_num)
        config: Full configuration dict
        query_pair_map: Map of query_id to QueryPair
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

    # Get query pair
    pair = query_pair_map[query_id]

    # Determine A/B assignment
    if ordering == 'control_first':
        response_a = pair.control.response_text
        response_b = pair.treatment.response_text
        label_a = 'control'
        label_b = 'treatment'
    else:
        response_a = pair.treatment.response_text
        response_b = pair.control.response_text
        label_a = 'treatment'
        label_b = 'control'

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
    query_pair_map: Dict[str, QueryPair],
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
        query_pair_map: Map of query_id to QueryPair
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
            return score_single_task(task, config, query_pair_map, run_id, rate_limit_delay)
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


def run_pipeline(config_path: str = 'src/eval/judge_config.yaml'):
    """Main judge scoring pipeline."""

    print("="*60)
    print("JUDGE SCORING PIPELINE - Stage 2")
    print("="*60)

    # Load config
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Setup output directory
    output_dir = Path(config['paths']['output_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f'judge_scores_{timestamp}.jsonl'
    run_id = timestamp

    print(f"\nRun ID: {run_id}")
    print(f"Output: {output_file}")

    # Load query pairs
    query_pairs = load_query_pairs(config)

    # Load checkpoint
    checkpoint_path = get_checkpoint_path(config)
    completed = load_checkpoint(checkpoint_path)
    print(f"\nCheckpoint: {len(completed)} tasks already completed")

    # Seed RNG for reproducibility
    random.seed(config['pipeline']['random_seed'])

    # Build task list with 6-pass design
    num_passes = config['pipeline'].get('num_passes', 6)
    tasks = []
    for pair in query_pairs:
        for judge_key in config['judges'].keys():
            for pass_num in range(1, num_passes + 1):
                # Alternate ordering: odd passes = control_first, even passes = treatment_first
                ordering = 'control_first' if pass_num % 2 == 1 else 'treatment_first'
                tasks.append((pair.query_id, judge_key, ordering, pass_num))

    # Filter to uncompleted tasks
    remaining_tasks = [
        task for task in tasks
        if task not in completed  # Full tuple match including pass_number
    ]

    total_tasks = len(tasks)
    remaining = len(remaining_tasks)

    print(f"\nTotal tasks: {total_tasks}")
    print(f"Remaining: {remaining}")

    if remaining == 0:
        print("\nAll tasks complete!")
        return

    # Process tasks with vendor-level parallelism
    query_pair_map = {pair.query_id: pair for pair in query_pairs}

    # Split tasks by vendor
    vendor_task_map = {judge_key: [] for judge_key in config['judges'].keys()}
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
                    query_pair_map,
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
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Output: {output_file}")
    print(f"Parse success rate: {(successful-failed)/successful*100:.1f}%" if successful > 0 else "N/A")


def main():
    """Entry point."""
    run_pipeline()


if __name__ == '__main__':
    main()
