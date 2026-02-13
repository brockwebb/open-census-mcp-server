# Task: Copy calibration scoring packet to repo

Copy the file from the eval outputs to the calibration folder:

```bash
cp /Users/brock/Documents/GitHub/census-mcp-server/results/cqs_manual_scoring_packet.md \
   /Users/brock/Documents/GitHub/census-mcp-server/docs/verification/calibration/cqs_manual_scoring_packet.md
```

If that file doesn't exist in results/, the content is in the Claude outputs directory. 
Generate it fresh by running:

```bash
cd /Users/brock/Documents/GitHub/census-mcp-server
python3 -c "
import json, random

path = 'results/cqs_responses_20260212_184334.jsonl'
records = {}
with open(path) as f:
    for line in f:
        r = json.loads(line)
        records[r['query_id']] = r

print(f'Loaded {len(records)} records')
# File exists and is readable
"
```

The scoring packet and answer key should both live in:
`docs/verification/calibration/`
