"""PDF → structured chunks using Docling."""

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import List

from docling.document_converter import DocumentConverter
from docling.chunking import HierarchicalChunker
from docling_core.types.doc import ImageRefMode, PictureItem, TableItem

from . import config
from .utils import setup_logging

logger = setup_logging(__name__)


@dataclass
class Chunk:
    """Structured chunk from PDF document."""
    text: str                    # The chunk content (markdown-formatted)
    section_path: List[str]      # e.g., ["Chapter 3", "3.2 Sample Design"]
    page_start: int              # First page of this chunk
    page_end: int                # Last page of this chunk
    content_type: str            # "text", "table", "list"
    source_catalog_id: str       # From config.SOURCE_CATALOG
    chunk_index: int             # Sequential index within document


def chunk_pdf(pdf_path: str, catalog_id: str, max_tokens: int = None) -> List[Chunk]:
    """Parse a PDF with Docling and return structured chunks.

    Args:
        pdf_path: Path to PDF file
        catalog_id: Source catalog ID from config
        max_tokens: Maximum chunk size in tokens (default: config.MAX_CHUNK_TOKENS)

    Returns:
        List of structured chunks
    """
    if max_tokens is None:
        max_tokens = config.MAX_CHUNK_TOKENS

    logger.info(f"Loading PDF: {pdf_path}")

    # 1. Convert PDF with Docling
    converter = DocumentConverter()
    result = converter.convert(pdf_path)
    doc = result.document

    logger.info(f"Converted to Docling document: {len(doc.pages)} pages")

    # 2. Chunk with HierarchicalChunker
    chunker = HierarchicalChunker(
        max_tokens=max_tokens,
        include_page_breaks=False,  # Don't break on page boundaries
        include_section_structure=True,  # Respect section hierarchy
    )

    chunks_output = list(chunker.chunk(doc))
    logger.info(f"Created {len(chunks_output)} chunks")

    # 3. Map Docling chunks to our Chunk dataclass
    result_chunks = []
    for i, doc_chunk in enumerate(chunks_output):
        # Extract section path from chunk headings
        section_path = []
        if hasattr(doc_chunk.meta, "headings") and doc_chunk.meta.headings:
            section_path = doc_chunk.meta.headings if isinstance(doc_chunk.meta.headings, list) else []

        # Get page range
        page_start = doc_chunk.meta.doc_items[0].prov[0].page_no if doc_chunk.meta.doc_items else 1
        page_end = doc_chunk.meta.doc_items[-1].prov[-1].page_no if doc_chunk.meta.doc_items else page_start

        # Determine content type
        content_type = "text"
        if any(isinstance(item.self_ref, TableItem) for item in doc_chunk.meta.doc_items):
            content_type = "table"
        elif any(hasattr(item.self_ref, "enumerated") and item.self_ref.enumerated
                 for item in doc_chunk.meta.doc_items if hasattr(item.self_ref, "enumerated")):
            content_type = "list"

        chunk = Chunk(
            text=doc_chunk.text,
            section_path=section_path,
            page_start=page_start,
            page_end=page_end,
            content_type=content_type,
            source_catalog_id=catalog_id,
            chunk_index=i
        )
        result_chunks.append(chunk)

    return result_chunks


def main():
    """Standalone test: chunk a PDF and print results."""
    parser = argparse.ArgumentParser(description="Chunk a PDF with Docling")
    parser.add_argument("--source", required=True, choices=list(config.SOURCE_CATALOG.keys()),
                       help="Source document key from config")
    parser.add_argument("--limit", type=int, help="Limit number of chunks to display")
    args = parser.parse_args()

    # Get source config
    source = config.SOURCE_CATALOG[args.source]
    pdf_path = config.REPO_ROOT / source["local_path"]

    if not pdf_path.exists():
        logger.error(f"PDF not found: {pdf_path}")
        return 1

    # Chunk the PDF
    chunks = chunk_pdf(str(pdf_path), source["catalog_id"])

    # Print summary
    print(f"\n=== CHUNKING SUMMARY ===")
    print(f"Source: {source['title']}")
    print(f"Chunks: {len(chunks)}")
    print(f"Avg chunk size: {sum(len(c.text) for c in chunks) // len(chunks)} chars")
    print(f"Content types: text={sum(1 for c in chunks if c.content_type == 'text')}, "
          f"table={sum(1 for c in chunks if c.content_type == 'table')}, "
          f"list={sum(1 for c in chunks if c.content_type == 'list')}")

    # Print first N chunks
    limit = args.limit or 3
    print(f"\n=== FIRST {limit} CHUNKS ===")
    for i, chunk in enumerate(chunks[:limit]):
        print(f"\n--- Chunk {i} ---")
        print(f"Section: {' > '.join(chunk.section_path) if chunk.section_path else '(root)'}")
        print(f"Pages: {chunk.page_start}-{chunk.page_end}")
        print(f"Type: {chunk.content_type}")
        print(f"Text ({len(chunk.text)} chars): {chunk.text[:200]}...")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
