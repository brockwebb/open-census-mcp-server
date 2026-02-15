#!/usr/bin/env python3
"""Build RAG index from Census methodology source documents.

Creates a FAISS vector index of document chunks for the RAG ablation condition.
Uses section-level chunking with boring defaults - no optimization.

Outputs to results/rag_ablation/index/:
- chunks.jsonl: Chunked documents with metadata
- faiss_index.bin: FAISS vector index
- metadata.json: Build configuration and statistics
- sources.txt: List of source documents used
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import argparse

# Lazy imports for optional dependencies
def lazy_imports():
    """Import heavy dependencies only when needed."""
    global SentenceTransformer, faiss, PdfReader
    from sentence_transformers import SentenceTransformer
    import faiss
    from pypdf import PdfReader
    return SentenceTransformer, faiss, PdfReader


# Source documents (same ones used to build pragmatics)
SOURCE_DOCUMENTS = [
    # Primary sources
    "knowledge-base/source-docs/OtherACS/acs_general_handbook_2020.pdf",
    "knowledge-base/source-docs/census-methodology/acs_design_methodology_report_2024.pdf",
    "knowledge-base/source-docs/OtherACS/acs_geography_handbook_2020.pdf",
    # Secondary sources
    "knowledge-base/source-docs/OtherACS/Understanding and Using ACS Data_ What All Data Users Need to Know.pdf",
    "knowledge-base/source-docs/OtherACS/ACS_Accuracy_of_Data_2023.pdf",
    "knowledge-base/source-docs/OtherACS/MultiyearACSAccuracyofData2023.pdf",
]


def extract_text_from_pdf(pdf_path: Path) -> List[Dict[str, Any]]:
    """Extract text from PDF with basic section detection.

    Returns list of pages with text and metadata.
    """
    _, _, PdfReader = lazy_imports()

    reader = PdfReader(str(pdf_path))
    pages = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text.strip():
            pages.append({
                'source': pdf_path.name,
                'page': i + 1,
                'text': text
            })

    return pages


def chunk_pages(pages: List[Dict], chunk_size: int = 600, overlap: int = 100) -> List[Dict]:
    """Chunk pages into ~chunk_size token chunks with overlap.

    Simple token-based chunking. No optimization.
    Preserves source and page metadata.
    """
    chunks = []
    chunk_id = 0

    for page in pages:
        text = page['text']
        # Rough token estimation: ~4 chars per token
        char_chunk_size = chunk_size * 4
        char_overlap = overlap * 4

        # Split into sentences for better boundary handling
        sentences = re.split(r'(?<=[.!?])\s+', text)

        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            if current_length + sentence_length > char_chunk_size and current_chunk:
                # Emit chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'chunk_id': chunk_id,
                    'source': page['source'],
                    'page': page['page'],
                    'section': None,  # Basic chunking doesn't detect sections
                    'text': chunk_text,
                    'char_length': len(chunk_text)
                })
                chunk_id += 1

                # Keep overlap
                overlap_text = chunk_text[-char_overlap:] if len(chunk_text) > char_overlap else chunk_text
                overlap_sentences = overlap_text.split()
                current_chunk = overlap_sentences
                current_length = len(' '.join(current_chunk))

            current_chunk.append(sentence)
            current_length += sentence_length + 1  # +1 for space

        # Emit remaining chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                'chunk_id': chunk_id,
                'source': page['source'],
                'page': page['page'],
                'section': None,
                'text': chunk_text,
                'char_length': len(chunk_text)
            })
            chunk_id += 1

    return chunks


def build_index(chunks: List[Dict], output_dir: Path) -> Dict[str, Any]:
    """Build FAISS index from chunks.

    Returns metadata about the build.
    """
    SentenceTransformer, faiss, _ = lazy_imports()

    print(f"\n📊 Building FAISS index...")
    print(f"  Chunks: {len(chunks)}")

    # Load embedding model
    print(f"  Loading embedding model: all-MiniLM-L6-v2")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Encode chunks
    print(f"  Encoding {len(chunks)} chunks...")
    texts = [c['text'] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)

    # Normalize for cosine similarity via inner product
    print(f"  Normalizing embeddings...")
    faiss.normalize_L2(embeddings)

    # Build index
    print(f"  Building FAISS index...")
    dimension = embeddings.shape[1]  # Should be 384 for all-MiniLM-L6-v2
    index = faiss.IndexFlatIP(dimension)  # Inner product (cosine after normalization)
    index.add(embeddings)

    # Write index
    index_path = output_dir / 'faiss_index.bin'
    print(f"  Writing index to {index_path}")
    faiss.write_index(index, str(index_path))

    # Write chunks
    chunks_path = output_dir / 'chunks.jsonl'
    print(f"  Writing chunks to {chunks_path}")
    with open(chunks_path, 'w') as f:
        for chunk in chunks:
            f.write(json.dumps(chunk) + '\n')

    return {
        'embedding_model': 'all-MiniLM-L6-v2',
        'embedding_dimension': dimension,
        'chunk_size_tokens': 600,
        'overlap_tokens': 100,
        'n_chunks': len(chunks),
        'index_type': 'FAISS IndexFlatIP (cosine similarity)',
        'build_date': datetime.now().isoformat()
    }


def main():
    parser = argparse.ArgumentParser(description='Build RAG index for ablation experiment')
    parser.add_argument('--output-dir', default='results/rag_ablation/index',
                       help='Output directory for index files')
    parser.add_argument('--chunk-size', type=int, default=600,
                       help='Target chunk size in tokens (default: 600)')
    parser.add_argument('--overlap', type=int, default=100,
                       help='Overlap between chunks in tokens (default: 100)')

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*70)
    print("RAG INDEX BUILDER")
    print("="*70)

    # Check source documents
    print(f"\n📚 Checking source documents...")
    available_sources = []
    missing_sources = []

    for src in SOURCE_DOCUMENTS:
        src_path = Path(src)
        if src_path.exists():
            available_sources.append(src_path)
            print(f"  ✅ {src_path.name}")
        else:
            missing_sources.append(src)
            print(f"  ❌ {src} (not found)")

    if missing_sources:
        print(f"\n❌ Missing {len(missing_sources)} source documents")
        print("Cannot proceed without all source documents.")
        return 1

    # Write sources list
    sources_path = output_dir / 'sources.txt'
    with open(sources_path, 'w') as f:
        f.write("# Source Documents for RAG Ablation\n\n")
        for src in available_sources:
            f.write(f"{src}\n")
    print(f"\n✅ Wrote source list to {sources_path}")

    # Extract text from PDFs
    print(f"\n📄 Extracting text from {len(available_sources)} PDFs...")
    all_pages = []
    for src_path in available_sources:
        print(f"  Processing {src_path.name}...")
        pages = extract_text_from_pdf(src_path)
        all_pages.extend(pages)
        print(f"    {len(pages)} pages extracted")

    print(f"\n  Total pages: {len(all_pages)}")

    # Chunk pages
    print(f"\n✂️  Chunking pages (size={args.chunk_size}, overlap={args.overlap})...")
    chunks = chunk_pages(all_pages, chunk_size=args.chunk_size, overlap=args.overlap)
    print(f"  Created {len(chunks)} chunks")

    # Build index
    metadata = build_index(chunks, output_dir)
    metadata['n_source_docs'] = len(available_sources)
    metadata['n_pages'] = len(all_pages)
    metadata['chunk_size_tokens'] = args.chunk_size
    metadata['overlap_tokens'] = args.overlap

    # Write metadata
    metadata_path = output_dir / 'metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"\n✅ Wrote metadata to {metadata_path}")

    print("\n" + "="*70)
    print("INDEX BUILD COMPLETE")
    print("="*70)
    print(f"\nOutputs in {output_dir}:")
    print(f"  - chunks.jsonl ({len(chunks)} chunks)")
    print(f"  - faiss_index.bin ({metadata['embedding_dimension']}-dim)")
    print(f"  - metadata.json")
    print(f"  - sources.txt ({len(available_sources)} docs)")

    return 0


if __name__ == '__main__':
    exit(main())
