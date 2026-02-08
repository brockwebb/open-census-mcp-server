#!/usr/bin/env python3
"""Export pragmatics from Neo4j to staging JSON.

Reads Context nodes, Pack nodes, and thread edges from the Neo4j `pragmatics`
database and writes staging JSON conforming to the Pydantic ContextItem model.

Output is organized by domain subdirectory with items grouped by category.

Requirements: FR-EP-001, FR-EP-003, FR-EP-005
See: docs/decisions/ADR-001-neo4j-authoring-sqlite-runtime.md
See: docs/architecture/knowledge_pack_management.md

Usage:
    python scripts/neo4j_to_staging.py --output staging/
    python scripts/neo4j_to_staging.py --output staging/ --domain acs
    python scripts/neo4j_to_staging.py --output staging/ --dry-run

Requires:
    pip install neo4j pydantic
    NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD environment variables (or .env file)
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv optional

from neo4j import GraphDatabase

# Add src to path for Pydantic model imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from census_mcp.pragmatics.models import ContextItem, ThreadEdge, Source, Provenance, PackManifest


def get_driver():
    """Create Neo4j driver from environment variables."""
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("NEO4J_USER", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "")
    if not password:
        print("ERROR: NEO4J_PASSWORD not set", file=sys.stderr)
        sys.exit(1)
    return GraphDatabase.driver(uri, auth=(user, password))


def export_packs(driver) -> dict[str, dict]:
    """Export Pack nodes from Neo4j."""
    query = """
    USE pragmatics
    MATCH (p:Pack)
    RETURN p.pack_id AS pack_id,
           p.pack_name AS pack_name, 
           p.parent_pack AS parent_pack,
           p.version AS version,
           p.description AS description
    ORDER BY p.pack_id
    """
    packs = {}
    with driver.session() as session:
        result = session.run(query)
        for record in result:
            packs[record["pack_id"]] = {
                "pack_id": record["pack_id"],
                "pack_name": record["pack_name"],
                "parent_pack": record["parent_pack"],
                "version": record["version"] or "1.0.0",
            }
    return packs


def export_thread_edges(driver) -> dict[str, list[dict]]:
    """Export thread edges, keyed by source context_id."""
    query = """
    USE pragmatics
    MATCH (c:Context)-[r]->(t:Context)
    RETURN c.context_id AS source_id,
           t.context_id AS target_id,
           type(r) AS edge_type
    ORDER BY c.context_id, t.context_id
    """
    edges = defaultdict(list)
    with driver.session() as session:
        result = session.run(query)
        for record in result:
            # Normalize edge type: NEO4J RELATES_TO → pydantic relates_to
            edge_type = record["edge_type"].lower()
            edges[record["source_id"]].append({
                "target": record["target_id"],
                "edge_type": edge_type,
            })
    return dict(edges)


def export_contexts(driver, domain_filter: str | None = None) -> list[dict]:
    """Export Context nodes from Neo4j."""
    if domain_filter:
        query = """
        USE pragmatics
        MATCH (c:Context {domain: $domain})
        RETURN properties(c) AS props
        ORDER BY c.context_id
        """
        params = {"domain": domain_filter}
    else:
        query = """
        USE pragmatics
        MATCH (c:Context)
        RETURN properties(c) AS props
        ORDER BY c.context_id
        """
        params = {}

    contexts = []
    with driver.session() as session:
        result = session.run(query, params)
        for record in result:
            contexts.append(dict(record["props"]))
    return contexts


def neo4j_to_pydantic(raw: dict, edges: dict[str, list[dict]]) -> ContextItem:
    """Convert a raw Neo4j node dict to a validated Pydantic ContextItem.

    Handles schema migration from old format (tags, flat source string)
    to canonical format (triggers, structured Provenance object).
    """
    context_id = raw["context_id"]

    # Migrate tags → triggers
    triggers = raw.get("triggers") or raw.get("tags") or []

    # Migrate source → provenance (handles all legacy formats)
    raw_prov = raw.get("provenance") or raw.get("source")
    provenance = None
    if raw_prov:
        if isinstance(raw_prov, str):
            try:
                raw_prov = json.loads(raw_prov)
            except json.JSONDecodeError:
                # Legacy flat string like "ACS-GEN-001, Ch. 7"
                parts = [p.strip() for p in raw_prov.split(",", 1)]
                raw_prov = None
                provenance = Provenance(
                    sources=[Source(document=parts[0],
                                   section=parts[1] if len(parts) > 1 else None,
                                   extraction_method="manual")],
                    confidence="grounded",
                )
        if raw_prov and isinstance(raw_prov, dict):
            if "sources" in raw_prov:
                provenance = Provenance(**raw_prov)
            else:
                # Old single-source format
                provenance = Provenance(
                    sources=[Source(**raw_prov)],
                    confidence="grounded",
                )
    if provenance is None:
        provenance = Provenance(
            sources=[Source(document="NEEDS-CITATION")],
            confidence="grounded",
            limitations="MIGRATION: No source existed.",
        )

    # Derive category from context_id if not set
    # ACS-MOE-001 → margin_of_error (based on ID convention)
    category = raw.get("category")
    if not category:
        category = _infer_category(context_id)

    # Get thread edges for this node
    thread_edges = [ThreadEdge(**e) for e in edges.get(context_id, [])]

    return ContextItem(
        context_id=context_id,
        domain=raw["domain"],
        category=category,
        latitude=raw["latitude"],
        context_text=raw["context_text"],
        triggers=triggers,
        thread_edges=thread_edges,
        provenance=provenance,
    )


# Map ID prefix abbreviations to category names
_CATEGORY_MAP = {
    "POP": "population_threshold",
    "MOE": "margin_of_error",
    "CMP": "comparison",
    "PER": "period_estimate",
    "DOL": "dollar_values",
    "GEO": "geography",
    "BRK": "break_in_series",
    "SUP": "suppression",
    "DIS": "disclosure_avoidance",
    "THR": "threshold",
    "EQV": "geographic_equivalence",
    "IND": "independent_cities",
    "TV": "temporal_validity",
    "UNC": "uncertainty",
    "SIG": "significance",
}


def _infer_category(context_id: str) -> str:
    """Infer category from context_id convention: ACS-MOE-001 → margin_of_error."""
    parts = context_id.split("-")
    if len(parts) >= 2:
        abbrev = parts[1]
        return _CATEGORY_MAP.get(abbrev, abbrev.lower())
    return "uncategorized"


def write_staging(output_dir: Path, items_by_domain: dict[str, list[ContextItem]], 
                  packs: dict[str, dict], dry_run: bool = False):
    """Write validated items to staging directory structure.
    
    FR-EP-003: organized by domain subdirectory, grouped by category.
    FR-EP-005: idempotent — deterministic output.
    """
    for domain, items in sorted(items_by_domain.items()):
        domain_dir = output_dir / domain
        
        # Write manifest
        if domain in packs:
            manifest = PackManifest(**packs[domain])
            manifest_path = domain_dir / "manifest.json"
            if dry_run:
                print(f"  [DRY RUN] Would write {manifest_path}")
            else:
                domain_dir.mkdir(parents=True, exist_ok=True)
                with open(manifest_path, "w") as f:
                    json.dump(manifest.model_dump(), f, indent=2)
                    f.write("\n")
                print(f"  ✓ {manifest_path}")

        # Group items by category
        by_category: dict[str, list[ContextItem]] = defaultdict(list)
        for item in items:
            by_category[item.category].append(item)

        # Write one file per category
        for category, cat_items in sorted(by_category.items()):
            # Deterministic order (FR-EP-005)
            cat_items.sort(key=lambda x: x.context_id)
            
            filename = f"{category}.json"
            filepath = domain_dir / filename
            
            serialized = [item.model_dump(mode="json") for item in cat_items]
            
            if dry_run:
                print(f"  [DRY RUN] Would write {filepath} ({len(cat_items)} items)")
            else:
                domain_dir.mkdir(parents=True, exist_ok=True)
                with open(filepath, "w") as f:
                    json.dump(serialized, f, indent=2)
                    f.write("\n")
                print(f"  ✓ {filepath} ({len(cat_items)} items)")


def main():
    parser = argparse.ArgumentParser(
        description="Export Neo4j pragmatics database to staging JSON"
    )
    parser.add_argument(
        "--output", "-o", type=Path, default=Path("staging"),
        help="Output staging directory (default: staging/)"
    )
    parser.add_argument(
        "--domain", "-d", type=str, default=None,
        help="Export only this domain (e.g., 'acs')"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be written without writing"
    )
    args = parser.parse_args()

    print("Connecting to Neo4j...")
    driver = get_driver()

    try:
        # Export packs
        print("Exporting Pack nodes...")
        packs = export_packs(driver)
        print(f"  Found {len(packs)} packs: {list(packs.keys())}")

        # Export thread edges
        print("Exporting thread edges...")
        edges = export_thread_edges(driver)
        total_edges = sum(len(v) for v in edges.values())
        print(f"  Found {total_edges} edges from {len(edges)} source nodes")

        # Export contexts
        print(f"Exporting Context nodes{f' (domain={args.domain})' if args.domain else ''}...")
        raw_contexts = export_contexts(driver, args.domain)
        print(f"  Found {len(raw_contexts)} context nodes")

        # Convert to Pydantic models (validates + migrates schema)
        print("Validating against Pydantic models...")
        items_by_domain: dict[str, list[ContextItem]] = defaultdict(list)
        errors = []
        for raw in raw_contexts:
            try:
                item = neo4j_to_pydantic(raw, edges)
                items_by_domain[item.domain].append(item)
            except Exception as e:
                errors.append(f"  {raw.get('context_id', '???')}: {e}")

        if errors:
            print(f"Validation errors ({len(errors)}):", file=sys.stderr)
            for err in errors:
                print(err, file=sys.stderr)
            sys.exit(1)

        print(f"  All {len(raw_contexts)} items valid")

        # Write staging files
        print(f"Writing to {args.output}/...")
        write_staging(args.output, items_by_domain, packs, args.dry_run)

        print("Done.")

    finally:
        driver.close()


if __name__ == "__main__":
    main()
