#!/usr/bin/env python3
"""Print provenance catalog coverage report from compiled packs.

Usage:
    python scripts/catalog_report.py                    # all packs
    python scripts/catalog_report.py packs/acs.db       # single pack
    python scripts/catalog_report.py --document ACS-GEN-001  # filter by doc
"""

import argparse
import sqlite3
import sys
from pathlib import Path


def report_pack(db_path: Path, document_filter: str | None = None):
    """Print coverage report for a single pack."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    print(f"\n{'='*60}")
    print(f"Pack: {db_path.name}")
    print(f"{'='*60}")

    # Summary by document
    query = """
        SELECT document,
               COUNT(DISTINCT context_id) AS items,
               COUNT(DISTINCT section) AS sections,
               COUNT(DISTINCT page) AS pages,
               COUNT(*) AS citations
        FROM provenance_catalog
    """
    params = []
    if document_filter:
        query += " WHERE document = ?"
        params.append(document_filter)
    query += " GROUP BY document ORDER BY document"

    rows = conn.execute(query, params).fetchall()
    if not rows:
        print("  No provenance catalog entries found.")
        conn.close()
        return

    print(f"\n  {'Document':<20} {'Items':>6} {'Sections':>9} {'Pages':>6} {'Citations':>10}")
    print(f"  {'-'*20} {'-'*6} {'-'*9} {'-'*6} {'-'*10}")
    for r in rows:
        print(f"  {r['document']:<20} {r['items']:>6} {r['sections']:>9} {r['pages']:>6} {r['citations']:>10}")

    # Confidence breakdown
    conf_rows = conn.execute("""
        SELECT confidence, COUNT(DISTINCT context_id) AS items
        FROM provenance_catalog
        GROUP BY confidence ORDER BY confidence
    """).fetchall()
    print(f"\n  Confidence: ", end="")
    print(", ".join(f"{r['confidence']}={r['items']}" for r in conf_rows))

    # Multi-source synthesized items
    synth = conn.execute("""
        SELECT context_id, synthesis_note, COUNT(*) AS source_count
        FROM provenance_catalog
        WHERE synthesis_note IS NOT NULL
        GROUP BY context_id
        HAVING source_count > 1
    """).fetchall()
    if synth:
        print(f"\n  Synthesized items ({len(synth)}):")
        for s in synth:
            print(f"    {s['context_id']} ({s['source_count']} sources): {s['synthesis_note'][:80]}")

    # Items needing citation
    needs = conn.execute("""
        SELECT context_id, document FROM provenance_catalog
        WHERE document = 'NEEDS-CITATION'
    """).fetchall()
    if needs:
        print(f"\n  ⚠ NEEDS CITATION ({len(needs)}):")
        for n in needs:
            print(f"    {n['context_id']}")

    # Expert judgments needing verification
    expert = conn.execute("""
        SELECT DISTINCT context_id, limitations FROM provenance_catalog
        WHERE confidence = 'expert_judgment'
    """).fetchall()
    if expert:
        print(f"\n  ⚠ Expert judgments ({len(expert)}) — verify against source docs:")
        for e in expert:
            lim = f" — {e['limitations']}" if e['limitations'] else ""
            print(f"    {e['context_id']}{lim}")

    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Provenance catalog coverage report")
    parser.add_argument("pack_db", type=Path, nargs="?", default=None,
                        help="Specific pack .db file (default: all in packs/)")
    parser.add_argument("--document", "-d", type=str, default=None,
                        help="Filter by source document ID")
    args = parser.parse_args()

    if args.pack_db:
        if not args.pack_db.exists():
            print(f"ERROR: {args.pack_db} not found", file=sys.stderr)
            sys.exit(1)
        report_pack(args.pack_db, args.document)
    else:
        packs_dir = Path("packs")
        dbs = sorted(packs_dir.glob("*.db"))
        if not dbs:
            print("No compiled packs found in packs/")
            sys.exit(1)
        for db in dbs:
            report_pack(db, args.document)

    print()


if __name__ == "__main__":
    main()
