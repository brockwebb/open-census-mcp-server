#!/usr/bin/env python3
"""Spot-check: which 7 pragmatics queries didn't call get_methodology_guidance?"""
import json, glob

files = glob.glob("results/v2_redo/stage1/pragmatics_responses_*.jsonl")
if not files:
    print("No pragmatics response files found")
    exit(1)

with open(files[0]) as f:
    for line in f:
        rec = json.loads(line)
        tools = [tc['tool_name'] for tc in rec.get('tool_calls', [])]
        if 'get_methodology_guidance' not in tools:
            print(f"{rec['query_id']}")
            print(f"  tools used: {tools}")
            print(f"  response (first 200): {rec['response_text'][:200]}")
            print(f"  tool_rounds: {rec.get('tool_rounds_used', '?')}")
            print()
