#!/usr/bin/env python3
"""Remove Google entries from checkpoint to force re-run of all Google judge calls.

This script removes all checkpoint entries for the 'google' judge, forcing them
to be re-run on the next pipeline execution. Anthropic and OpenAI entries are
preserved.
"""

import json
from pathlib import Path

checkpoint_path = Path('results/stage2/checkpoints/judge_checkpoint.json')

if not checkpoint_path.exists():
    print(f"ERROR: Checkpoint file not found at {checkpoint_path}")
    exit(1)

# Load checkpoint
with open(checkpoint_path) as f:
    data = json.load(f)

print(f"Original checkpoint state:")
print(f"  Total completed entries: {len(data['completed'])}")

# Count by vendor (judge_key is at index 1 in tuple)
vendor_counts = {}
for entry in data['completed']:
    vendor = entry[1]  # (query_id, judge_key, ordering, pass_number)
    vendor_counts[vendor] = vendor_counts.get(vendor, 0) + 1

print(f"  By vendor: {vendor_counts}")

# Remove google entries
original_count = len(data['completed'])
data['completed'] = [t for t in data['completed'] if t[1] != 'google']
removed_count = original_count - len(data['completed'])

print(f"\nRemoved {removed_count} Google checkpoint entries")
print(f"Remaining checkpoint entries: {len(data['completed'])}")

# Count remaining by vendor
vendor_counts_after = {}
for entry in data['completed']:
    vendor = entry[1]
    vendor_counts_after[vendor] = vendor_counts_after.get(vendor, 0) + 1

print(f"  By vendor: {vendor_counts_after}")

# Write updated checkpoint
with open(checkpoint_path, 'w') as f:
    json.dump(data, f, indent=2)

print(f"\nCheckpoint updated: {checkpoint_path}")
