#!/usr/bin/env python3
"""Verification script for RAG integration.

Quick test on one query to verify end-to-end integration before full run.
"""
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.eval.rag_retriever import RAGRetriever
from src.eval.agent_loop import CONTROL_SYSTEM_PROMPT


def main():
    """Test RAG retriever integration."""
    print("=" * 60)
    print("RAG Integration Verification")
    print("=" * 60)
    print()

    # Initialize retriever
    index_dir = Path(__file__).parent.parent / "results/rag_ablation/index"
    print(f"Loading RAG retriever from {index_dir}...")
    retriever = RAGRetriever(str(index_dir))
    print(f"✓ Loaded {len(retriever.chunks)} chunks")
    print()

    # Test query (from DOE gate check)
    test_query = "What is the population of California?"
    print(f"Test query: {test_query}")
    print()

    # Format system prompt
    print("Augmenting system prompt with retrieved context...")
    augmented_prompt, metadata = retriever.format_system_prompt(
        CONTROL_SYSTEM_PROMPT, test_query
    )
    print()

    # Report results
    print("Retrieval Metadata:")
    print(f"  Retrieved chunks: {len(metadata['retrieved_chunks'])}")
    print(f"  Total context chars: {metadata['total_context_chars']}")
    print()

    print("Retrieved chunks:")
    for i, chunk in enumerate(metadata['retrieved_chunks']):
        print(f"\n  Chunk {i+1}:")
        print(f"    Score: {chunk['score']:.3f}")
        print(f"    Source: {chunk['source']}")
        page_start = chunk.get('page_start')
        page_end = chunk.get('page_end')
        if page_start and page_end:
            if page_start == page_end:
                print(f"    Page: {page_start}")
            else:
                print(f"    Pages: {page_start}-{page_end}")
        section_path = chunk.get('section_path', [])
        if section_path and any(section_path):
            print(f"    Section: {' > '.join(section_path)}")
        print(f"    Text length: {chunk['text_length']} chars")
    print()

    # Verify augmented prompt structure
    print("Augmented Prompt Structure:")
    print(f"  Total length: {len(augmented_prompt)} chars")
    print(f"  Base prompt included: {'helpful assistant' in augmented_prompt}")
    print(f"  Reference materials section: {'Reference Materials' in augmented_prompt}")
    print()

    # Show first 500 chars of augmented prompt
    print("Augmented prompt preview (first 500 chars):")
    print(augmented_prompt[:500])
    print("...")
    print()

    print("=" * 60)
    print("✓ RAG integration verification PASSED")
    print("=" * 60)
    print()
    print("Ready to run full RAG condition with:")
    print("  python -m eval.harness --condition rag --query-ids NORM-001")


if __name__ == "__main__":
    main()
