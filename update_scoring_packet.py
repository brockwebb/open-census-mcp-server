#!/usr/bin/env python3
"""Update manual scoring packet from v2 to v3.

Changes:
- Remove D6 from all scoring tables (change total from /12 to /10)
- Replace response content with v3 data
- Update header and add Pipeline Fidelity note
"""

import json
import re
from pathlib import Path

# Load v3 responses
queries = {}
with open('results/cqs_responses_20260213_091530.jsonl') as f:
    for line in f:
        pair = json.loads(line)
        queries[pair['query_id']] = pair

# Answer key: which response is treatment/control
answer_key = {
    'NORM-001': {'A': 'treatment', 'B': 'control'},
    'NORM-008': {'A': 'treatment', 'B': 'control'},
    'NORM-015': {'A': 'control', 'B': 'treatment'},
    'GEO-006': {'A': 'treatment', 'B': 'control'},
    'SML-001': {'A': 'treatment', 'B': 'control'},
    'TMP-002': {'A': 'treatment', 'B': 'control'},
    'MIS-002': {'A': 'treatment', 'B': 'control'},
    'AMB-002': {'A': 'treatment', 'B': 'control'},
    'PER-001a': {'A': 'control', 'B': 'treatment'},
}

# Target queries in order
target_queries = ['NORM-001', 'NORM-008', 'NORM-015', 'GEO-006', 'SML-001', 'TMP-002', 'MIS-002', 'AMB-002', 'PER-001a']

# Load original packet
with open('docs/test/cqs_manual_scoring_packet.md') as f:
    content = f.read()

# Update header
content = re.sub(
    r'\*\*Date:\*\* \d{4}-\d{2}-\d{2}',
    '**Date:** 2026-02-13',
    content
)
content = re.sub(
    r'\*\*Battery:\*\* cqs_responses_\d+_\d+\.jsonl',
    '**Battery:** cqs_responses_20260213_091530.jsonl',
    content
)

# Update scoring instructions - change "six" to "five"
content = re.sub(
    r'Score each response independently on the six CQS dimensions',
    'Score each response independently on the five CQS dimensions',
    content
)

# Update The Six Dimensions table - remove D6 row and add note
dimensions_table = '''| Dim | Name | What to Look For |
|---|---|---|
| D1 | Source Selection & Fitness | Right product, vintage, geography for the question? |
| D2 | Methodological Soundness | Correct computation, weights, denominators, formulas? |
| D3 | Uncertainty Communication | MOE/SE provided? Reliability assessed? Proper confidence level? |
| D4 | Definitional Accuracy | Official Census concepts used correctly? Period vs point-in-time? |
| D5 | Reproducibility & Traceability | Table IDs, variable codes, FIPS codes — can you replicate? |

> **Note:** Groundedness/faithfulness (formerly D6) is measured separately via
> automated Pipeline Fidelity verification, not by human raters. This metric
> compares response claims against API tool call logs and is reported independently.'''

old_dimensions_pattern = r'\| Dim \| Name \| What to Look For \|.*?\| D6 \|[^\n]+\|[^\n]+\|'
content = re.sub(old_dimensions_pattern, dimensions_table, content, flags=re.DOTALL)

# Remove D6 gate failure principle
content = re.sub(
    r'\d+\.\s+\*\*D6 = 0 is a gate failure\.\*\*[^\n]+\n',
    '',
    content
)

# Renumber principles if needed
content = re.sub(r'(\d+)\.\s+\*\*Score each response independently', r'2. **Score each response independently', content)
content = re.sub(r'(\d+)\.\s+After scoring both', r'3. After scoring both', content)

# For each query, replace responses and update scoring tables
for query_id in target_queries:
    if query_id not in queries:
        print(f"Warning: {query_id} not found in v3 data")
        continue

    pair = queries[query_id]

    # Get treatment and control responses
    treatment_text = pair['treatment']['response_text']
    control_text = pair['control']['response_text']

    # Map to A/B based on answer key
    if answer_key[query_id]['A'] == 'treatment':
        response_a = treatment_text
        response_b = control_text
    else:
        response_a = control_text
        response_b = treatment_text

    # Find the section for this query
    pattern = rf'(## Query \d+ of 9: {re.escape(query_id)}.*?)(### Response A\n\n)(.*?)(\n\n---\n\n### Response B\n\n)(.*?)(\n\n---\n\n### Scoring)'

    def replace_responses(match):
        return match.group(1) + match.group(2) + response_a + match.group(4) + response_b + match.group(6)

    content = re.sub(pattern, replace_responses, content, flags=re.DOTALL)

    # Update scoring tables for this query - remove D6 rows and change /12 to /10
    # Find both scoring tables for this query
    query_section_pattern = rf'(## Query \d+ of 9: {re.escape(query_id)}.*?)(## Query \d+ of 9:|$)'

    def update_scoring_tables(match):
        section = match.group(1)
        # Remove D6 rows from both tables
        section = re.sub(r'\| D6: Groundedness \|[^\n]+\n', '', section)
        # Change /12 to /10
        section = re.sub(r'/12', '/10', section)
        # Add back the next query marker if it exists
        if match.group(2):
            return section + match.group(2)
        return section

    content = re.sub(query_section_pattern, update_scoring_tables, content, flags=re.DOTALL)

# Write updated packet
with open('docs/test/cqs_manual_scoring_packet.md', 'w') as f:
    f.write(content)

print("✓ Updated scoring packet")

# Update answer key
answer_key_content = """ANSWER KEY — DO NOT SHARE WITH RATERS
==================================================

RUBRIC VERSION: v3 (5-dimension CQS, D1-D5)
STAGE 1 DATA: cqs_responses_20260213_091530.jsonl
DATE GENERATED: 2026-02-13

NOTES:
- D6 (Groundedness) removed from human scoring. Measured via automated
  Pipeline Fidelity (Stage 3).
- Total score per response: /10 (was /12 in v2)

KNOWN ISSUES:
- PER-001a treatment: Reports ~117K for Bozeman city. Actual city pop ~53K.
  This is Gallatin County data. Known FIPS resolution bug in MCP tool.

Random seed: 42

NORM-001: A=treatment, B=control
NORM-008: A=treatment, B=control
NORM-015: A=control, B=treatment
GEO-006: A=treatment, B=control
SML-001: A=treatment, B=control
TMP-002: A=treatment, B=control
MIS-002: A=treatment, B=control
AMB-002: A=treatment, B=control
PER-001a: A=control, B=treatment
"""

with open('docs/test/scoring_answer_key.txt', 'w') as f:
    f.write(answer_key_content)

print("✓ Updated answer key")

# Verification
with open('docs/test/cqs_manual_scoring_packet.md') as f:
    updated_content = f.read()

d6_count = updated_content.count('D6')
print(f"\n Verification:")
print(f"  D6 occurrences: {d6_count} (should be ~1-2 in Pipeline Fidelity note only)")
print(f"  /10 occurrences: {updated_content.count('/10')}")
print(f"  /12 occurrences: {updated_content.count('/12')} (should be 0)")
