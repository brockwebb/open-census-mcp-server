#!/usr/bin/env python3
"""Clear all checkpoint entries to force full re-run of all judges.

This clears ALL vendor entries (Anthropic, OpenAI, Google) from the checkpoint,
forcing a complete re-run of the entire judge panel on the next pipeline execution.
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

original_count = len(data.get('completed', []))
print(f"Clearing {original_count} checkpoint entries")

# Clear all completed entries
data['completed'] = []

# Write updated checkpoint
with open(checkpoint_path, 'w') as f:
    json.dump(data, f, indent=2)

print(f"Checkpoint cleared: {checkpoint_path}")
print(f"Pipeline will re-run all {original_count} judge calls")
