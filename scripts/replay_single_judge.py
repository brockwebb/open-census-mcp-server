#!/usr/bin/env python3
"""Replay a single failed judge task for completeness.

NORM-008, pass 2, treatment_first failed to parse (GPT-5.2 omitted response_b).
This script replays that single task to achieve 702/702 completeness.
"""

import json
import yaml
from pathlib import Path
from datetime import datetime

from eval.judge_pipeline import (
    call_openai, parse_judge_response, validate_judge_response,
    load_query_pairs
)
from eval.judge_prompts import build_judge_prompt
from eval.models import JudgeRecord, DimensionScore


def main():
    # Load config
    with open('src/eval/judge_config.yaml') as f:
        config = yaml.safe_load(f)

    # Load query pairs
    query_pairs = load_query_pairs(config)
    pair = next(p for p in query_pairs if p.query_id == 'NORM-008')

    print(f"Replaying: NORM-008, pass 2, treatment_first")
    print(f"Query: {pair.query_text[:80]}...")

    # Build prompt: treatment_first means treatment=A, control=B
    prompt = build_judge_prompt(
        pair.query_text,
        pair.treatment.response_text,  # response_a
        pair.control.response_text     # response_b
    )

    # Call OpenAI
    openai_config = config['judges']['openai'].copy()
    openai_config['max_tokens'] = config['pipeline'].get('max_tokens', 4096)

    for attempt in range(3):
        print(f"\nAttempt {attempt + 1}/3...")
        raw, in_tok, out_tok, latency = call_openai(prompt, openai_config)

        parsed = parse_judge_response(raw)
        if parsed and validate_judge_response(parsed):
            print(f"✅ Success! Latency: {latency:.0f}ms, Tokens: {in_tok}/{out_tok}")

            # Build scores
            scores_a = {dim: DimensionScore(**parsed['response_a'][dim])
                       for dim in ['D1','D2','D3','D4','D5','D6']}
            scores_b = {dim: DimensionScore(**parsed['response_b'][dim])
                       for dim in ['D1','D2','D3','D4','D5','D6']}

            record = JudgeRecord(
                query_id='NORM-008',
                judge_model=openai_config['model'],
                judge_vendor='openai',
                presentation_order='treatment_first',
                scores_response_a=scores_a,
                scores_response_b=scores_b,
                preference=parsed.get('overall_preference', 'tie'),
                preference_reasoning=parsed.get('preference_reasoning', ''),
                response_a_label='treatment',
                response_b_label='control',
                latency_ms=latency,
                input_tokens=in_tok,
                output_tokens=out_tok,
                timestamp=datetime.now(),
                run_id='20260213_125057',
                raw_response=raw[:10000],
                parse_success=True,
                pass_number=2
            )

            # Append to the v3 file
            output = Path('results/stage2/judge_scores_20260213_125057.jsonl')
            with open(output, 'a') as f:
                f.write(record.model_dump_json() + '\n')

            print(f"\n✅ Appended to {output}")
            print(f"📊 File now has {sum(1 for _ in open(output))} records")
            return

        else:
            print(f"❌ Parse/validation failed, retrying...")

    print("\n❌ FAILED after 3 attempts")
    raise RuntimeError("Failed to replay judge task after 3 attempts")


if __name__ == '__main__':
    main()
