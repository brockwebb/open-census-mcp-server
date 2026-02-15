#!/usr/bin/env python3
"""Build RAG index from Census methodology source documents.

Uses Docling extraction (same as quarry pipeline) for controlled comparison.
The RAG and Pragmatics conditions must differ ONLY in knowledge representation
(raw chunks vs curated judgment), not in extraction methodology.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path for quarry imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.quarry.chunk import chunk_pdf, Chunk
from scripts.quarry.config import SOURCE_CATALOG, MAX_CHUNK_TOKENS, REPO_ROOT

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from typing import List


# Source documents for RAG ablation — must match pragmatics provenance
RAG_SOURCES = [
    "acs_general_handbook",        # ACS-GEN-001 — primary
    "acs_design_methodology",      # ACS-DM-2024 — primary
]

# Additional sources not in quarry catalog yet
ADDITIONAL_SOURCES = [
    {
        "catalog_id": "acs_geography_handbook_2020",
        "title": "ACS Geography Handbook 2020",
        "local_path": "knowledge-base/source-docs/OtherACS/acs_geography_handbook_2020.pdf"
    },
    {
        "catalog_id": "acs_accuracy_2023",
        "title": "ACS Accuracy of Data 2023",
        "local_path": "knowledge-base/source-docs/OtherACS/ACS_Accuracy_of_Data_2023.pdf"
    },
    {
        "catalog_id": "multiyear_accuracy_2023",
        "title": "Multiyear ACS Accuracy 2023",
        "local_path": "knowledge-base/source-docs/OtherACS/MultiyearACSAccuracyofData2023.pdf"
    },
    {
        "catalog_id": "understanding_acs_data",
        "title": "Understanding and Using ACS Data",
        "local_path": "knowledge-base/source-docs/OtherACS/Understanding and Using ACS Data_ What All Data Users Need to Know.pdf"
    },
]

# Merging parameters for RAG-friendly chunks
MIN_CHUNK_CHARS = 400  # ~100 tokens minimum
TARGET_CHUNK_CHARS = 2400  # ~600 tokens target (balances size and specificity)


def merge_small_chunks(chunks: List[Chunk]) -> List[Chunk]:
    """Merge small Docling chunks into larger RAG-friendly chunks.

    HierarchicalChunker creates many micro-chunks (section headers, page numbers).
    This post-processing merges consecutive chunks from the same source until
    they reach a minimum size, preserving Docling's quality while creating
    useful retrieval units.

    Args:
        chunks: List of Chunk objects from Docling extraction

    Returns:
        List of merged Chunk objects
    """
    if not chunks:
        return []

    merged = []
    current_merge = {
        "text": chunks[0].text,
        "source_catalog_id": chunks[0].source_catalog_id,
        "section_path": chunks[0].section_path,
        "page_start": chunks[0].page_start,
        "page_end": chunks[0].page_end,
        "content_type": chunks[0].content_type,
    }

    for i in range(1, len(chunks)):
        chunk = chunks[i]
        current_len = len(current_merge["text"])

        # Merge if: same source AND (under target size OR tiny current chunk)
        should_merge = (
            chunk.source_catalog_id == current_merge["source_catalog_id"]
            and (
                current_len < TARGET_CHUNK_CHARS
                or len(chunk.text) < MIN_CHUNK_CHARS
            )
        )

        if should_merge:
            # Merge into current
            current_merge["text"] += "\n\n" + chunk.text
            current_merge["page_end"] = chunk.page_end  # Update end page
            # Combine section paths (keep unique)
            if chunk.section_path and chunk.section_path != current_merge["section_path"]:
                # Use the more specific section path (longer)
                if len(chunk.section_path) > len(current_merge["section_path"] or []):
                    current_merge["section_path"] = chunk.section_path
        else:
            # Emit current merge
            merged.append(Chunk(
                text=current_merge["text"],
                section_path=current_merge["section_path"],
                page_start=current_merge["page_start"],
                page_end=current_merge["page_end"],
                content_type=current_merge["content_type"],
                source_catalog_id=current_merge["source_catalog_id"],
                chunk_index=len(merged)
            ))

            # Start new merge
            current_merge = {
                "text": chunk.text,
                "source_catalog_id": chunk.source_catalog_id,
                "section_path": chunk.section_path,
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "content_type": chunk.content_type,
            }

    # Emit final merge
    merged.append(Chunk(
        text=current_merge["text"],
        section_path=current_merge["section_path"],
        page_start=current_merge["page_start"],
        page_end=current_merge["page_end"],
        content_type=current_merge["content_type"],
        source_catalog_id=current_merge["source_catalog_id"],
        chunk_index=len(merged)
    ))

    return merged


def main():
    """Build RAG index with Docling extraction."""
    print("=" * 70)
    print("RAG INDEX BUILDER (Docling Extraction)")
    print("=" * 70)
    print()

    output_dir = Path("results/rag_ablation/index")
    output_dir.mkdir(parents=True, exist_ok=True)

    all_chunks = []
    sources_used = []

    # Process quarry catalog sources
    print("📚 Processing quarry catalog sources...")
    for key in RAG_SOURCES:
        if key not in SOURCE_CATALOG:
            print(f"ERROR: {key} not found in SOURCE_CATALOG")
            return 1

        source = SOURCE_CATALOG[key]
        pdf_path = REPO_ROOT / source["local_path"]
        if not pdf_path.exists():
            print(f"ERROR: PDF not found: {pdf_path}")
            return 1

        print(f"\n  Processing: {source['title']}")
        print(f"  Path: {pdf_path}")
        chunks = chunk_pdf(str(pdf_path), source["catalog_id"], max_tokens=MAX_CHUNK_TOKENS)
        all_chunks.extend(chunks)
        sources_used.append({
            "catalog_id": source["catalog_id"],
            "title": source["title"],
            "path": str(pdf_path),
            "chunks": len(chunks)
        })
        print(f"  ✓ {len(chunks)} chunks extracted")

    # Process additional sources
    print("\n📚 Processing additional sources...")
    for source in ADDITIONAL_SOURCES:
        pdf_path = REPO_ROOT / source["local_path"]
        if not pdf_path.exists():
            print(f"ERROR: PDF not found: {pdf_path}")
            return 1

        print(f"\n  Processing: {source['title']}")
        print(f"  Path: {pdf_path}")
        chunks = chunk_pdf(str(pdf_path), source["catalog_id"], max_tokens=MAX_CHUNK_TOKENS)
        all_chunks.extend(chunks)
        sources_used.append({
            "catalog_id": source["catalog_id"],
            "title": source["title"],
            "path": str(pdf_path),
            "chunks": len(chunks)
        })
        print(f"  ✓ {len(chunks)} chunks extracted")

    print()
    print("=" * 70)
    print(f"Raw Docling chunks: {len(all_chunks)}")
    print("=" * 70)

    # Merge small chunks for RAG-friendly retrieval units
    print("\n🔗 Merging small chunks for RAG retrieval...")
    print(f"  Target size: ~{TARGET_CHUNK_CHARS} chars (~{TARGET_CHUNK_CHARS//4} tokens)")
    print(f"  Minimum size: ~{MIN_CHUNK_CHARS} chars (~{MIN_CHUNK_CHARS//4} tokens)")
    merged_chunks = merge_small_chunks(all_chunks)
    all_chunks = merged_chunks
    print(f"  ✓ Merged to {len(all_chunks)} chunks")

    print()
    print("=" * 70)
    print(f"Final chunks: {len(all_chunks)}")
    print(f"Total source documents: {len(sources_used)}")
    print("=" * 70)
    print()

    # Write chunks.jsonl with quarry-compatible schema
    print("💾 Writing chunks.jsonl...")
    chunks_path = output_dir / "chunks.jsonl"
    with open(chunks_path, "w") as f:
        for i, chunk in enumerate(all_chunks):
            record = {
                "chunk_id": i,
                "source": chunk.source_catalog_id,
                "section_path": chunk.section_path,
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "content_type": chunk.content_type,
                "text": chunk.text,
                "char_length": len(chunk.text),
            }
            f.write(json.dumps(record) + "\n")
    print(f"  ✓ Wrote {len(all_chunks)} chunks to {chunks_path}")

    # Build FAISS index
    print("\n🔍 Building FAISS index...")
    print("  Loading embedding model: all-MiniLM-L6-v2")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    print(f"  Encoding {len(all_chunks)} chunks...")
    texts = [c.text for c in all_chunks]
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)

    print("  Normalizing embeddings...")
    faiss.normalize_L2(embeddings)

    print("  Building FAISS index...")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    index_path = output_dir / "faiss_index.bin"
    faiss.write_index(index, str(index_path))
    print(f"  ✓ Wrote index to {index_path}")

    # Content type breakdown
    content_types = {}
    for chunk in all_chunks:
        content_types[chunk.content_type] = content_types.get(chunk.content_type, 0) + 1

    # Write metadata
    metadata = {
        "extraction_method": "docling_hierarchical_chunker",
        "max_chunk_tokens": MAX_CHUNK_TOKENS,
        "embedding_model": "all-MiniLM-L6-v2",
        "embedding_dimension": dimension,
        "n_chunks": len(all_chunks),
        "n_source_docs": len(sources_used),
        "index_type": "FAISS IndexFlatIP (cosine similarity)",
        "build_date": datetime.now().isoformat(),
        "content_type_breakdown": content_types,
        "note": "Same extraction as quarry pipeline (Docling). See scripts/quarry/chunk.py"
    }
    metadata_path = output_dir / "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"\n✅ Wrote metadata to {metadata_path}")

    # Write sources list
    sources_path = output_dir / "sources.txt"
    with open(sources_path, "w") as f:
        f.write("# Source Documents for RAG Ablation\n")
        f.write(f"# Extraction: Docling HierarchicalChunker (max_tokens={MAX_CHUNK_TOKENS})\n")
        f.write(f"# Build Date: {datetime.now().isoformat()}\n\n")
        for s in sources_used:
            f.write(f"{s['catalog_id']}: {s['path']} ({s['chunks']} chunks)\n")
    print(f"✅ Wrote source list to {sources_path}")

    # Summary
    print()
    print("=" * 70)
    print("INDEX BUILD COMPLETE")
    print("=" * 70)
    print()
    print("Summary:")
    print(f"  Chunks: {len(all_chunks)}")
    print(f"  Documents: {len(sources_used)}")
    print(f"  Extraction: Docling HierarchicalChunker")
    print(f"  Max chunk tokens: {MAX_CHUNK_TOKENS}")
    print(f"  Embedding: all-MiniLM-L6-v2 ({dimension}-dim)")
    print(f"  Content types: {content_types}")
    print()
    print("Outputs:")
    print(f"  {chunks_path}")
    print(f"  {index_path}")
    print(f"  {metadata_path}")
    print(f"  {sources_path}")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
