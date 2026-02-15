#!/usr/bin/env python3
"""QC Gate Check for RAG Index.

Validates index quality before proceeding with RAG ablation experiment.
Checks chunk statistics and runs retrieval smoke tests.

Exit codes:
    0 - PASS (all checks passed)
    1 - WARN (some checks flagged but usable)
    2 - FAIL (critical issues found, do not proceed)
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

# Lazy imports
def lazy_imports():
    """Import heavy dependencies only when needed."""
    global SentenceTransformer, faiss
    from sentence_transformers import SentenceTransformer
    import faiss
    return SentenceTransformer, faiss


# Test queries from DOE gate check
TEST_QUERIES = [
    ("NORM-001", "What is the population of California?"),
    ("GEO-002", "Compare poverty rates between Baltimore City and Baltimore County"),
    ("SML-002", "What is the poverty rate in Mercer, PA at the tract level?"),
    ("AMB-001", "What is the median household income in Portland?"),
    ("NORM-008", "What is the unemployment rate in my county?"),
]


def load_chunks(index_dir: Path):
    """Load chunks from JSONL."""
    chunks_path = index_dir / 'chunks.jsonl'
    chunks = []
    with open(chunks_path) as f:
        for line in f:
            chunks.append(json.loads(line))
    return chunks


def check_chunk_statistics(chunks):
    """Check 2a: Chunk statistics."""
    print("\n" + "="*60)
    print("CHECK 2a: CHUNK STATISTICS")
    print("="*60)

    total_chunks = len(chunks)
    print(f"\nTotal chunks: {total_chunks}")

    # Chunks per source
    source_counts = defaultdict(int)
    for chunk in chunks:
        source_counts[chunk.get('source', 'unknown')] += 1

    print(f"\nChunks per source document:")
    for source, count in sorted(source_counts.items()):
        print(f"  {source}: {count}")

    # Content type breakdown (Docling-specific)
    content_types = defaultdict(int)
    for chunk in chunks:
        content_types[chunk.get('content_type', 'unknown')] += 1

    print(f"\nContent type breakdown:")
    for ctype, count in sorted(content_types.items()):
        print(f"  {ctype}: {count}")

    # Section path population
    sections_populated = sum(1 for c in chunks if c.get('section_path') and any(c.get('section_path', [])))
    print(f"\nSection paths populated: {sections_populated}/{total_chunks} ({100*sections_populated/total_chunks:.1f}%)")

    # Chunk size statistics
    lengths = [len(chunk['text']) for chunk in chunks]
    min_len = min(lengths)
    max_len = max(lengths)
    mean_len = sum(lengths) / len(lengths)
    median_len = sorted(lengths)[len(lengths) // 2]

    # Estimate tokens (rough: 4 chars per token)
    min_tok = min_len // 4
    max_tok = max_len // 4
    mean_tok = mean_len // 4
    median_tok = median_len // 4

    print(f"\nChunk size statistics:")
    print(f"  Min: {min_len} chars (~{min_tok} tokens)")
    print(f"  Max: {max_len} chars (~{max_tok} tokens)")
    print(f"  Mean: {mean_len:.0f} chars (~{mean_tok:.0f} tokens)")
    print(f"  Median: {median_len} chars (~{median_tok} tokens)")

    # Flag problems
    warnings = []
    errors = []

    # Empty or near-empty chunks
    empty_chunks = [i for i, chunk in enumerate(chunks) if len(chunk['text']) < 50]
    if empty_chunks:
        warnings.append(f"Found {len(empty_chunks)} near-empty chunks (< 50 chars)")
        print(f"\n⚠️  WARN: {len(empty_chunks)} near-empty chunks")
        for i in empty_chunks[:5]:  # Show first 5
            print(f"    Chunk {i}: {len(chunks[i]['text'])} chars, source={chunks[i].get('source', 'unknown')}")

    # Oversized chunks (Docling uses 2000 token max, ~8000 chars)
    oversized_chunks = [i for i, chunk in enumerate(chunks) if len(chunk['text']) > 10000]
    if oversized_chunks:
        warnings.append(f"Found {len(oversized_chunks)} oversized chunks (> 10000 chars)")
        print(f"\n⚠️  WARN: {len(oversized_chunks)} oversized chunks")
        for i in oversized_chunks[:5]:  # Show first 5
            print(f"    Chunk {i}: {len(chunks[i]['text'])} chars, source={chunks[i].get('source', 'unknown')}")

    # Chunk count range check
    if total_chunks < 50:
        errors.append(f"Too few chunks: {total_chunks} (expected 50-1000)")
    elif total_chunks > 1000:
        errors.append(f"Too many chunks: {total_chunks} (expected 50-1000)")

    # Check for section path issues
    if sections_populated < total_chunks * 0.3:
        warnings.append(f"Low section path population: {sections_populated}/{total_chunks}")

    return {
        'total_chunks': total_chunks,
        'source_counts': dict(source_counts),
        'content_types': dict(content_types),
        'sections_populated': sections_populated,
        'min_len': min_len,
        'max_len': max_len,
        'mean_len': mean_len,
        'median_len': median_len,
        'warnings': warnings,
        'errors': errors
    }


def check_retrieval_smoke_test(index_dir: Path, chunks):
    """Check 2b: Retrieval smoke test."""
    print("\n" + "="*60)
    print("CHECK 2b: RETRIEVAL SMOKE TEST")
    print("="*60)

    SentenceTransformer, faiss = lazy_imports()

    # Load retriever components
    model = SentenceTransformer('all-MiniLM-L6-v2')
    index = faiss.read_index(str(index_dir / 'faiss_index.bin'))

    results = []

    for qid, query in TEST_QUERIES:
        print(f"\n{'='*60}")
        print(f"Query: {qid} — {query}")

        # Embed and retrieve
        query_embedding = model.encode([query])
        faiss.normalize_L2(query_embedding)
        scores, indices = index.search(query_embedding, 5)

        retrieved_chunks = []
        for i, idx in enumerate(indices[0]):
            chunk = chunks[idx]
            page_start = chunk.get('page_start')
            page_end = chunk.get('page_end')
            if page_start and page_end:
                page_label = f"{page_start}-{page_end}" if page_start != page_end else str(page_start)
            else:
                page_label = "?"

            retrieved_chunks.append({
                'chunk_id': idx,
                'score': float(scores[0][i]),
                'source': chunk.get('source', 'unknown'),
                'page_label': page_label,
                'text': chunk['text']
            })

        print(f"Retrieved {len(retrieved_chunks)} chunks, total {sum(len(c['text']) for c in retrieved_chunks)} chars")

        # Show top 3
        for i, chunk in enumerate(retrieved_chunks[:3]):
            print(f"\n  Chunk {i+1}: score={chunk['score']:.3f}, source={chunk['source']}, pp.{chunk['page_label']}")
            print(f"  Text: {chunk['text'][:150]}...")

        results.append({
            'qid': qid,
            'query': query,
            'retrieved_chunks': retrieved_chunks
        })

    return results


def assess_relevance(retrieval_results):
    """Check 2c: Relevance assessment."""
    print("\n" + "="*60)
    print("CHECK 2c: RELEVANCE ASSESSMENT")
    print("="*60)

    # Relevance keywords for each query
    relevance_criteria = {
        "NORM-001": ["population", "estimate", "count", "total", "acs", "decennial"],
        "GEO-002": ["poverty", "compare", "comparison", "geography", "county", "city"],
        "SML-002": ["small area", "reliability", "moe", "margin of error", "tract", "unreliable"],
        "AMB-001": ["income", "median household", "earnings", "wages"],
        "NORM-008": ["unemployment", "employment", "labor force", "jobless"],
    }

    assessments = []

    for result in retrieval_results:
        qid = result['qid']
        top_chunk = result['retrieved_chunks'][0]
        text_lower = top_chunk['text'].lower()

        # Check if any relevance keyword appears
        keywords = relevance_criteria.get(qid, [])
        matches = [kw for kw in keywords if kw in text_lower]

        relevant = len(matches) > 0
        status = "✅ RELEVANT" if relevant else "❌ IRRELEVANT"

        # Try to extract topic
        topic = "general census methodology"
        if "population" in text_lower:
            topic = "population estimates"
        elif "poverty" in text_lower:
            topic = "poverty measurement"
        elif "reliability" in text_lower or "margin of error" in text_lower:
            topic = "data reliability/MOEs"
        elif "income" in text_lower or "earnings" in text_lower:
            topic = "income/earnings"
        elif "employment" in text_lower or "labor" in text_lower:
            topic = "employment/labor force"
        elif "geography" in text_lower:
            topic = "geographic concepts"

        print(f"\n{qid}: {status} - top chunk about {topic}")
        if matches:
            print(f"  Matched keywords: {', '.join(matches)}")

        assessments.append({
            'qid': qid,
            'relevant': relevant,
            'topic': topic,
            'matched_keywords': matches
        })

    return assessments


def generate_qc_report(stats, assessments, output_path):
    """Generate QC summary report."""
    print("\n" + "="*60)
    print("QC SUMMARY")
    print("="*60)

    report_lines = []

    # Chunk statistics
    report_lines.append("CHUNK STATISTICS:")
    report_lines.append(f"  Total chunks: {stats['total_chunks']}")
    report_lines.append("\n  Chunks per document:")
    for source, count in sorted(stats['source_counts'].items()):
        report_lines.append(f"    {source}: {count}")
    report_lines.append(f"\n  Content types:")
    for ctype, count in sorted(stats.get('content_types', {}).items()):
        report_lines.append(f"    {ctype}: {count}")
    report_lines.append(f"\n  Section paths populated: {stats.get('sections_populated', 0)}/{stats['total_chunks']}")
    report_lines.append(f"\n  Chunk size range: {stats['min_len']}-{stats['max_len']} chars (mean: {stats['mean_len']:.0f})")

    if stats['warnings']:
        report_lines.append("\n  WARNINGS:")
        for warning in stats['warnings']:
            report_lines.append(f"    ⚠️  {warning}")

    if stats['errors']:
        report_lines.append("\n  ERRORS:")
        for error in stats['errors']:
            report_lines.append(f"    ❌ {error}")

    # Retrieval smoke test results
    report_lines.append("\n\nRETRIEVAL SMOKE TEST:")
    relevant_count = sum(1 for a in assessments if a['relevant'])
    for assessment in assessments:
        status = "RELEVANT" if assessment['relevant'] else "IRRELEVANT"
        report_lines.append(f"  {assessment['qid']}: {status} - top chunk about {assessment['topic']}")

    # Pass/fail determination
    report_lines.append("\n\nOVERALL ASSESSMENT:")

    fail_conditions = []
    warn_conditions = []

    if stats['total_chunks'] < 50 or stats['total_chunks'] > 1000:
        fail_conditions.append(f"Chunk count out of range: {stats['total_chunks']}")
    if stats['errors']:
        fail_conditions.extend(stats['errors'])
    if relevant_count < 3:
        fail_conditions.append(f"Too many irrelevant retrievals: {5 - relevant_count}/5 missed")

    if stats['warnings']:
        warn_conditions.extend(stats['warnings'])
    if relevant_count == 3 or relevant_count == 4:
        warn_conditions.append(f"{5 - relevant_count} retrieval test(s) missed")

    if fail_conditions:
        report_lines.append("  ❌ FAIL")
        for condition in fail_conditions:
            report_lines.append(f"    - {condition}")
        verdict = "FAIL"
    elif warn_conditions:
        report_lines.append("  ⚠️  WARN (usable but has issues)")
        for condition in warn_conditions:
            report_lines.append(f"    - {condition}")
        verdict = "WARN"
    else:
        report_lines.append("  ✅ PASS")
        report_lines.append(f"    - {stats['total_chunks']} chunks in expected range")
        report_lines.append(f"    - All {relevant_count}/5 retrieval tests returned relevant chunks")
        verdict = "PASS"

    # Print to console
    for line in report_lines:
        print(line)

    # Write to file
    with open(output_path, 'w') as f:
        f.write("RAG INDEX QC REPORT\n")
        f.write("="*60 + "\n\n")
        f.write("\n".join(report_lines))
        f.write("\n")

    print(f"\n📄 QC report written to {output_path}")

    return verdict


def main():
    index_dir = Path('results/rag_ablation/index')

    print("="*60)
    print("RAG INDEX QC GATE CHECK")
    print("="*60)

    # Load chunks
    print("\n📚 Loading index...")
    chunks = load_chunks(index_dir)
    print(f"  Loaded {len(chunks)} chunks")

    # Check 2a: Chunk statistics
    stats = check_chunk_statistics(chunks)

    # Check 2b: Retrieval smoke test
    retrieval_results = check_retrieval_smoke_test(index_dir, chunks)

    # Check 2c: Relevance assessment
    assessments = assess_relevance(retrieval_results)

    # Generate QC report
    report_path = index_dir / 'qc_report.txt'
    verdict = generate_qc_report(stats, assessments, report_path)

    # Exit with appropriate code
    if verdict == "PASS":
        print("\n✅ QC PASSED - Safe to proceed with RAG ablation")
        return 0
    elif verdict == "WARN":
        print("\n⚠️  QC WARNING - Index is usable but has issues")
        return 1
    else:
        print("\n❌ QC FAILED - Do NOT proceed with RAG ablation")
        return 2


if __name__ == '__main__':
    sys.exit(main())
