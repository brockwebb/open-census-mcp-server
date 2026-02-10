"""Backfill page-level provenance on SOURCED_FROM relationships.

Re-chunks PDFs to extract page metadata, then updates existing SOURCED_FROM
relationships in the quarry with page_start, page_end, and source_section.
"""

import argparse
from pathlib import Path

from . import config
from .chunk import chunk_pdf
from .utils import get_neo4j_driver, setup_logging

logger = setup_logging(__name__)


def backfill_document_provenance(driver, source_key: str, dry_run: bool = False):
    """Backfill provenance for a single source document.

    Args:
        driver: Neo4j driver
        source_key: Source document key from config.SOURCE_CATALOG
        dry_run: If True, show changes without applying them

    Returns:
        Dict with update statistics
    """
    source = config.SOURCE_CATALOG[source_key]
    catalog_id = source["catalog_id"]
    pdf_path = config.REPO_ROOT / source["local_path"]

    logger.info(f"Processing: {source['title']} ({catalog_id})")

    # Verify PDF exists
    if not pdf_path.exists():
        logger.error(f"PDF not found: {pdf_path}")
        return {"error": "PDF not found", "updated": 0}

    # Re-chunk PDF to get metadata
    logger.info(f"Re-chunking PDF: {pdf_path}")
    chunks = chunk_pdf(str(pdf_path), catalog_id)
    logger.info(f"Created {len(chunks)} chunks")

    # Build chunk_index -> metadata map
    chunk_metadata = {}
    for chunk in chunks:
        chunk_metadata[chunk.chunk_index] = {
            "page_start": chunk.page_start,
            "page_end": chunk.page_end,
            "source_section": " > ".join(chunk.section_path) if chunk.section_path else None,
        }

    # Query relationships that need updating
    with driver.session(database=config.NEO4J_DATABASE) as session:
        result = session.run("""
            MATCH (n)-[r:SOURCED_FROM]->(doc:SourceDocument {catalog_id: $catalog_id})
            WHERE r.chunk_index IS NOT NULL
            RETURN r, r.chunk_index AS chunk_idx, n.id AS node_id
        """, {"catalog_id": catalog_id})

        relationships = [(record["r"], record["chunk_idx"], record["node_id"]) for record in result]
        logger.info(f"Found {len(relationships)} SOURCED_FROM relationships to update")

        # Update relationships
        updated = 0
        missing_chunks = []

        for rel, chunk_idx, node_id in relationships:
            if chunk_idx not in chunk_metadata:
                missing_chunks.append(chunk_idx)
                continue

            metadata = chunk_metadata[chunk_idx]

            if dry_run:
                logger.info(f"Would update {node_id[:50]} chunk {chunk_idx}: pages {metadata['page_start']}-{metadata['page_end']}")
            else:
                # Update relationship properties
                session.run("""
                    MATCH (n {id: $node_id})-[r:SOURCED_FROM]->(doc:SourceDocument {catalog_id: $catalog_id})
                    WHERE r.chunk_index = $chunk_idx
                    SET r.page_start = $page_start,
                        r.page_end = $page_end,
                        r.source_section = $source_section
                """, {
                    "node_id": node_id,
                    "catalog_id": catalog_id,
                    "chunk_idx": chunk_idx,
                    "page_start": metadata["page_start"],
                    "page_end": metadata["page_end"],
                    "source_section": metadata["source_section"],
                })
                updated += 1

        if missing_chunks:
            logger.warning(f"Missing chunk metadata for {len(missing_chunks)} relationships: {missing_chunks[:10]}")

        logger.info(f"Updated {updated} relationships for {catalog_id}")

        return {
            "catalog_id": catalog_id,
            "chunks": len(chunks),
            "relationships": len(relationships),
            "updated": updated,
            "missing": len(missing_chunks),
        }


def verify_provenance_coverage(driver):
    """Check current provenance coverage across all documents."""
    with driver.session(database=config.NEO4J_DATABASE) as session:
        # Total SOURCED_FROM relationships
        result = session.run("""
            MATCH ()-[r:SOURCED_FROM]->()
            RETURN count(r) AS total
        """)
        total = result.single()["total"]

        # With page_start
        result = session.run("""
            MATCH ()-[r:SOURCED_FROM]->()
            WHERE r.page_start IS NOT NULL
            RETURN count(r) AS with_page
        """)
        with_page = result.single()["with_page"]

        # With source_section
        result = session.run("""
            MATCH ()-[r:SOURCED_FROM]->()
            WHERE r.source_section IS NOT NULL
            RETURN count(r) AS with_section
        """)
        with_section = result.single()["with_section"]

        # By document
        result = session.run("""
            MATCH ()-[r:SOURCED_FROM]->(doc:SourceDocument)
            WITH doc.catalog_id AS catalog_id,
                 count(r) AS total,
                 sum(CASE WHEN r.page_start IS NOT NULL THEN 1 ELSE 0 END) AS with_page
            RETURN catalog_id, total, with_page
            ORDER BY catalog_id
        """)
        by_doc = list(result)

        return {
            "total": total,
            "with_page": with_page,
            "with_section": with_section,
            "by_document": by_doc,
        }


def main():
    """CLI for backfilling provenance."""
    parser = argparse.ArgumentParser(description="Backfill page-level provenance on SOURCED_FROM relationships")
    parser.add_argument("--source", choices=list(config.SOURCE_CATALOG.keys()),
                       help="Backfill a specific source document (default: all)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show changes without applying them")
    parser.add_argument("--verify", action="store_true",
                       help="Check current provenance coverage and exit")
    args = parser.parse_args()

    driver = get_neo4j_driver()

    try:
        # Verification mode
        if args.verify:
            logger.info("Checking current provenance coverage...")
            coverage = verify_provenance_coverage(driver)

            print("\n=== PROVENANCE COVERAGE ===\n")
            print(f"Total SOURCED_FROM relationships: {coverage['total']:,}")
            print(f"With page_start: {coverage['with_page']:,} ({coverage['with_page']/coverage['total']*100:.1f}%)")
            print(f"With source_section: {coverage['with_section']:,} ({coverage['with_section']/coverage['total']*100:.1f}%)")

            print("\n=== BY DOCUMENT ===\n")
            for doc in coverage["by_document"]:
                pct = doc["with_page"] / doc["total"] * 100 if doc["total"] > 0 else 0
                print(f"{doc['catalog_id']:40} {doc['with_page']:5,}/{doc['total']:5,} ({pct:5.1f}%)")

            return 0

        # Backfill mode
        if args.dry_run:
            logger.info("DRY RUN mode - no changes will be made")

        sources = [args.source] if args.source else list(config.SOURCE_CATALOG.keys())

        results = []
        for source_key in sources:
            result = backfill_document_provenance(driver, source_key, dry_run=args.dry_run)
            results.append(result)

        # Summary
        print("\n=== BACKFILL SUMMARY ===\n")
        total_updated = sum(r.get("updated", 0) for r in results)
        total_missing = sum(r.get("missing", 0) for r in results)

        for result in results:
            if "error" in result:
                print(f"❌ {result.get('catalog_id', 'unknown')}: {result['error']}")
            else:
                print(f"✅ {result['catalog_id']:40} {result['updated']:5,} relationships updated")

        print(f"\nTotal updated: {total_updated:,}")
        if total_missing > 0:
            print(f"Total missing chunks: {total_missing:,}")

        if not args.dry_run and total_updated > 0:
            print("\n✅ Backfill complete! Run with --verify to check coverage.")

        return 0

    finally:
        driver.close()


if __name__ == "__main__":
    import sys
    sys.exit(main())
