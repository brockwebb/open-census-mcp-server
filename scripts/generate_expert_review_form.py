"""Generate blinded expert review form content.

Creates randomized A/B/C presentation of Control/RAG/Pragmatics responses
for 20 selected queries. Strips any tells that would reveal conditions.

Usage:
    python scripts/generate_expert_review_form.py
"""

import json
import yaml
import random
import re
from pathlib import Path
from typing import Dict, List


# Selected queries for review (20 total, balanced across categories)
SELECTED_QUERIES = [
    # Normal (8)
    'NORM-001', 'NORM-002', 'NORM-005', 'NORM-008', 'NORM-010',
    'NORM-012', 'NORM-014', 'NORM-015',
    # Geographic edge (4)
    'GEO-002', 'GEO-003', 'GEO-005', 'GEO-006',
    # Small area (3)
    'SML-001', 'SML-002', 'SML-004',
    # Temporal (2)
    'TMP-001', 'TMP-002',
    # Ambiguity (2)
    'AMB-001', 'AMB-003',
    # Persona (1)
    'PER-001b'
]


def load_responses():
    """Load responses from all three data sources."""
    # Load control + pragmatics pairs
    pairs = {}
    with open('results/cqs_responses_20260213_091530.jsonl') as f:
        for line in f:
            pair = json.loads(line)
            qid = pair['query_id']
            pairs[qid] = {
                'control': pair['control']['response_text'],
                'pragmatics': pair['treatment']['response_text']
            }

    # Load RAG responses
    rag_responses = {}
    with open('results/rag_ablation/stage1/rag_responses_20260215_143919.jsonl') as f:
        for line in f:
            rec = json.loads(line)
            qid = rec['query_id']
            rag_responses[qid] = rec['response_text']

    # Load query texts
    with open('src/eval/battery/queries.yaml') as f:
        queries_data = yaml.safe_load(f)
        query_texts = {q['id']: q['text'] for q in queries_data['queries']}

    # Combine into single structure
    responses = {}
    for qid in SELECTED_QUERIES:
        if qid not in pairs or qid not in rag_responses:
            print(f"WARNING: {qid} missing from data sources")
            continue

        responses[qid] = {
            'query_text': query_texts[qid],
            'control': pairs[qid]['control'],
            'rag': rag_responses[qid],
            'pragmatics': pairs[qid]['pragmatics']
        }

    return responses


def strip_markdown(text: str) -> str:
    """Strip markdown formatting from text."""
    # Remove headers
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    # Remove bold/italic
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)

    # Convert bullets to plain text with dashes
    text = re.sub(r'^\s*[-*+]\s+', '- ', text, flags=re.MULTILINE)

    # Remove code blocks
    text = re.sub(r'```[^`]*```', '', text, flags=re.DOTALL)
    text = re.sub(r'`([^`]+)`', r'\1', text)

    return text


def strip_tells(text: str, condition: str) -> str:
    """Remove any tells that would reveal which condition this is."""

    # RAG tells - references to "provided materials"
    # Be more specific with patterns to avoid awkward substitutions
    rag_patterns = [
        (r'the reference materials provided to me focus on', 'Census methodology documentation focuses on'),
        (r'based on the reference materials provided to me', 'according to Census methodology documentation'),
        (r'the reference materials provided to me', 'Census methodology documentation'),
        (r'the reference materials provided', 'Census methodology documentation'),
        (r'based on the methodology documentation provided to me', 'according to Census methodology documentation'),
        (r'based on the methodology documentation provided', 'according to Census methodology documentation'),
        (r'the methodology documentation provided to me', 'Census methodology documentation'),
        (r'the documentation provided to me', 'Census methodology documentation'),
        (r'from the materials provided to me', 'according to Census methodology documentation'),
        (r'from the materials provided', 'according to Census methodology documentation'),
        (r'according to the reference materials', 'according to Census methodology documentation'),
        (r'the reference materials', 'Census methodology documentation'),
    ]

    for pattern, replacement in rag_patterns:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # Pragmatics tells - tool call references
    pragmatics_tells = [
        r'using the get_methodology_guidance tool',
        r'calling get_methodology_guidance',
        r'I called the methodology guidance tool',
        r'the tool returned',
        r'using the Census MCP tools',
    ]

    for pattern in pragmatics_tells:
        # Just remove these phrases
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # Control tells - mentions of no access to tools
    control_patterns = [
        (r"I don't have access to current", 'Based on general knowledge, I do not have current'),
        (r"I don't have access to", 'Based on general knowledge,'),
        (r"I cannot access", 'Based on general knowledge,'),
        (r"I'm unable to retrieve", 'Based on general knowledge,'),
        (r"without access to specific tools", 'based on general knowledge'),
    ]

    for pattern, replacement in control_patterns:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # Clean up any double spaces or line breaks from removals
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)

    return text.strip()


def truncate_response(text: str, max_words: int = 800) -> str:
    """Truncate response at max_words if longer."""
    words = text.split()
    if len(words) <= max_words:
        return text

    truncated = ' '.join(words[:max_words])
    return truncated + "\n\n[Response truncated for review]"


def generate_randomization(selected_queries: List[str], seed: int = 42) -> Dict:
    """Generate randomized A/B/C assignments for each query."""
    random.seed(seed)

    randomization_key = {}
    conditions = ['control', 'rag', 'pragmatics']

    for i, qid in enumerate(selected_queries):
        shuffled = conditions.copy()
        random.shuffle(shuffled)

        randomization_key[qid] = {
            'query_number': i + 1,
            'A': shuffled[0],
            'B': shuffled[1],
            'C': shuffled[2]
        }

    return randomization_key


def generate_form_content(responses: Dict, randomization_key: Dict) -> str:
    """Generate markdown form content."""
    lines = []
    lines.append("# Expert Review Form — Census Data Assistance Systems")
    lines.append("")
    lines.append("**Instructions:** For each query, rank the three responses from ")
    lines.append("best (1) to worst (3) for a data user making a policy decision. ")
    lines.append("Responses are presented in randomized order.")
    lines.append("")
    lines.append("="*70)
    lines.append("")

    for qid in SELECTED_QUERIES:
        if qid not in responses:
            continue

        mapping = randomization_key[qid]
        query_num = mapping['query_number']
        query_text = responses[qid]['query_text']

        lines.append(f"## Query {query_num} of 20")
        lines.append("")
        lines.append(f'**Question asked:** "{query_text}"')
        lines.append("")

        # Add each response in randomized order
        for label in ['A', 'B', 'C']:
            condition = mapping[label]
            response_text = responses[qid][condition]

            # Process response
            response_text = strip_markdown(response_text)
            response_text = strip_tells(response_text, condition)
            response_text = truncate_response(response_text, max_words=800)

            lines.append(f"### Response {label}")
            lines.append("")
            lines.append(response_text)
            lines.append("")

        lines.append("**Rank these responses from best (1) to worst (3) for a data user making a policy decision:**")
        lines.append("- Response A: ___")
        lines.append("- Response B: ___")
        lines.append("- Response C: ___")
        lines.append("")
        lines.append("**Any concerns about these responses?** (optional)")
        lines.append("")
        lines.append("[Free text response]")
        lines.append("")
        lines.append("---")
        lines.append("")

    return '\n'.join(lines)


def generate_key_json(randomization_key: Dict, seed: int) -> Dict:
    """Generate JSON key file."""
    return {
        'randomization_seed': seed,
        'total_queries': len(randomization_key),
        'queries': randomization_key
    }


def generate_key_markdown(randomization_key: Dict) -> str:
    """Generate human-readable key file."""
    lines = []
    lines.append("# Expert Review Key")
    lines.append("")
    lines.append("**CONFIDENTIAL — Do not share with reviewers until after data collection**")
    lines.append("")
    lines.append("This key maps the randomized A/B/C labels to actual conditions.")
    lines.append("")
    lines.append(f"{'Query':<12} {'Num':<5} {'A':<12} {'B':<12} {'C':<12}")
    lines.append("-" * 60)

    for qid in SELECTED_QUERIES:
        if qid not in randomization_key:
            continue
        mapping = randomization_key[qid]
        lines.append(f"{qid:<12} {mapping['query_number']:<5} "
                    f"{mapping['A']:<12} {mapping['B']:<12} {mapping['C']:<12}")

    lines.append("")
    lines.append("## Legend")
    lines.append("- **control**: Bare LLM (no tools, no retrieval)")
    lines.append("- **rag**: Retrieval-augmented generation from source documents")
    lines.append("- **pragmatics**: Structured pragmatic context via MCP tools")
    lines.append("")

    return '\n'.join(lines)


def main():
    print("="*70)
    print("EXPERT REVIEW FORM GENERATOR")
    print("="*70)

    # Load responses
    print("\nLoading responses...")
    responses = load_responses()
    print(f"  ✅ Loaded responses for {len(responses)} queries")

    # Generate randomization
    print("\nGenerating randomization (seed=42)...")
    randomization_key = generate_randomization(SELECTED_QUERIES, seed=42)
    print(f"  ✅ Randomized {len(randomization_key)} queries")

    # Show sample randomization
    print("\n  Sample randomizations:")
    for qid in list(randomization_key.keys())[:3]:
        mapping = randomization_key[qid]
        print(f"    {qid}: A={mapping['A']}, B={mapping['B']}, C={mapping['C']}")

    # Generate form content
    print("\nGenerating form content...")
    form_content = generate_form_content(responses, randomization_key)

    form_path = Path('talks/fcsm_2026/expert_review_form.md')
    form_path.parent.mkdir(parents=True, exist_ok=True)
    with open(form_path, 'w') as f:
        f.write(form_content)
    print(f"  ✅ {form_path}")

    # Generate JSON key
    print("\nGenerating key files...")
    key_json = generate_key_json(randomization_key, seed=42)

    key_json_path = Path('talks/fcsm_2026/expert_review_key.json')
    with open(key_json_path, 'w') as f:
        json.dump(key_json, f, indent=2)
    print(f"  ✅ {key_json_path}")

    # Generate markdown key
    key_md = generate_key_markdown(randomization_key)

    key_md_path = Path('talks/fcsm_2026/expert_review_key.md')
    with open(key_md_path, 'w') as f:
        f.write(key_md)
    print(f"  ✅ {key_md_path}")

    print("\n" + "="*70)
    print("VERIFICATION")
    print("="*70)
    print("\nManually check:")
    print("  1. All three responses present for Q1 and Q20")
    print("  2. No condition labels visible in responses")
    print("  3. No obvious tells remaining (check for 'provided materials', 'tool calls')")
    print("  4. Responses are substantively different")
    print("")
    print(f"Form ready at: {form_path}")
    print(f"Key stored at: {key_json_path} and {key_md_path}")
    print("")
    print("⚠️  KEEP KEY FILES CONFIDENTIAL until after review collection")


if __name__ == '__main__':
    main()
