#!/usr/bin/env python3
"""Import staging JSON into Neo4j pragmatics database.

Reads staging JSON files conforming to the Pydantic ContextItem model and
creates/updates Context nodes, Pack nodes, and thread edges in Neo4j.

Supports incremental updates: new items added, existing items updated.
Does NOT delete items unless --purge-domain is specified.

Requirements: FR-EP-002, FR-EP-004, FR-EP-006
See: docs/decisions/ADR-001-neo4j-authoring-sqlite-runtime.md
See: docs/architecture/knowledge_pack_management.md

Usage:
    python scripts/staging_to_neo4j.py staging/acs
    python scripts/staging_to_neo4j.py staging/          # all domains
    python scripts/staging_to_neo4j.py staging/acs --purge-domain
    python scripts/staging_to_neo4j.py staging/acs --dry-run

Requires:
    pip install neo4j pydantic
    NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD environment variables (or .env file)
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv optional

from neo4j import GraphDatabase

# Add src to path for Pydantic model imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from census_mcp.pragmatics.models import ContextItem, PackManifest
from pydantic import ValidationError


def get_driver():
    """Create Neo4j driver from environment variables."""
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("NEO4J_USER", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "")
    if not password:
        print("ERROR: NEO4J_PASSWORD not set", file=sys.stderr)
        sys.exit(1)
    return GraphDatabase.driver(uri, auth=(user, password))


def load_staging_dir(staging_dir: Path) -> tuple[PackManifest | None, list[ContextItem]]:
    """Load and validate all content from a staging directory.
    
    FR-EP-004: validates all items against Pydantic models before writing.
    
    Returns:
        (manifest, items) — manifest may be None if directory has no manifest.json
    """
    manifest = None
    items = []
    errors = []

    # Load manifest if present
    manifest_path = staging_dir / "manifest.json"
    if manifest_path.exists():
        try:
            with open(manifest_path) as f:
                data = json.load(f)
            manifest = PackManifest(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            errors.append(f"manifest.json: {e}")

    # Load all JSON files except manifest
    json_files = sorted(f for f in staging_dir.glob("*.json") if f.name != "manifest.json")
    
    for json_file in json_files:
        try:
            with open(json_file) as f:
                data = json.load(f)

            if not isinstance(data, list):
                errors.append(f"{json_file.name}: Expected list, got {type(data).__name__}")
                continue

            for i, item_data in enumerate(data):
                try:
                    item = ContextItem(**item_data)
                    items.append(item)
                except ValidationError as e:
                    errors.append(f"{json_file.name}[{i}]: {e}")

        except json.JSONDecodeError as e:
            errors.append(f"{json_file.name}: JSON error: {e}")

    if errors:
        print(f"Validation errors in {staging_dir}:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)

    return manifest, items


def upsert_pack(driver, manifest: PackManifest, dry_run: bool = False):
    """Create or update a Pack node in Neo4j."""
    query = """
    USE pragmatics
    MERGE (p:Pack {pack_id: $pack_id})
    SET p.pack_name = $pack_name,
        p.parent_pack = $parent_pack,
        p.version = $version
    RETURN p.pack_id AS pack_id
    """
    params = manifest.model_dump()

    if dry_run:
        print(f"  [DRY RUN] Would upsert Pack: {manifest.pack_id}")
        return

    with driver.session() as session:
        session.run(query, params)
    print(f"  ✓ Pack: {manifest.pack_id}")


def upsert_context(driver, item: ContextItem, dry_run: bool = False):
    """Create or update a Context node in Neo4j.

    Uses canonical Pydantic field names (triggers, not tags).
    Provenance is stored as structured JSON string.
    """
    query = """
    USE pragmatics
    MERGE (c:Context {context_id: $context_id})
    SET c.domain = $domain,
        c.category = $category,
        c.latitude = $latitude,
        c.context_text = $context_text,
        c.triggers = $triggers,
        c.provenance = $provenance
    RETURN c.context_id AS id
    """
    # Remove old 'tags' and 'source' properties if they exist (migration cleanup)
    cleanup_query = """
    USE pragmatics
    MATCH (c:Context {context_id: $context_id})
    REMOVE c.tags, c.source
    """

    provenance_json = json.dumps(item.provenance.model_dump())
    params = {
        "context_id": item.context_id,
        "domain": item.domain,
        "category": item.category,
        "latitude": item.latitude,
        "context_text": item.context_text,
        "triggers": item.triggers,
        "provenance": provenance_json,
    }

    if dry_run:
        print(f"  [DRY RUN] Would upsert Context: {item.context_id}")
        return

    with driver.session() as session:
        session.run(query, params)
        session.run(cleanup_query, {"context_id": item.context_id})


def upsert_thread_edges(driver, item: ContextItem, dry_run: bool = False):
    """Create thread edges from this context item to its targets.
    
    Removes existing outgoing edges first, then recreates from source of truth.
    This ensures edges match staging exactly.
    """
    if not item.thread_edges:
        return

    # Remove existing outgoing edges from this node
    delete_query = """
    USE pragmatics
    MATCH (c:Context {context_id: $context_id})-[r:INHERITS|RELATES_TO|APPLIES_TO]->()
    DELETE r
    """

    if dry_run:
        for edge in item.thread_edges:
            print(f"  [DRY RUN] Would create edge: {item.context_id} -[{edge.edge_type}]-> {edge.target}")
        return

    with driver.session() as session:
        session.run(delete_query, {"context_id": item.context_id})

        for edge in item.thread_edges:
            # Dynamic relationship type based on edge_type
            rel_type = edge.edge_type.upper()  # relates_to → RELATES_TO
            create_query = f"""
            USE pragmatics
            MATCH (source:Context {{context_id: $source_id}})
            MATCH (target:Context {{context_id: $target_id}})
            MERGE (source)-[:{rel_type}]->(target)
            """
            session.run(create_query, {
                "source_id": item.context_id,
                "target_id": edge.target,
            })


def purge_domain(driver, domain: str, dry_run: bool = False):
    """Delete all Context nodes for a domain. Use with caution."""
    count_query = """
    USE pragmatics
    MATCH (c:Context {domain: $domain})
    RETURN count(c) AS count
    """
    delete_query = """
    USE pragmatics
    MATCH (c:Context {domain: $domain})
    DETACH DELETE c
    """

    with driver.session() as session:
        result = session.run(count_query, {"domain": domain})
        count = result.single()["count"]

    if dry_run:
        print(f"  [DRY RUN] Would delete {count} nodes for domain '{domain}'")
        return

    if count == 0:
        print(f"  No nodes found for domain '{domain}'")
        return

    # Confirm
    print(f"  WARNING: About to delete {count} Context nodes for domain '{domain}'")
    response = input("  Type 'yes' to confirm: ")
    if response.strip().lower() != "yes":
        print("  Aborted.")
        sys.exit(0)

    with driver.session() as session:
        session.run(delete_query, {"domain": domain})
    print(f"  ✓ Deleted {count} nodes for domain '{domain}'")


def main():
    parser = argparse.ArgumentParser(
        description="Import staging JSON into Neo4j pragmatics database"
    )
    parser.add_argument(
        "staging_path", type=Path,
        help="Staging directory to import (e.g., 'staging/acs' or 'staging/' for all)"
    )
    parser.add_argument(
        "--purge-domain", action="store_true",
        help="Delete all existing nodes for the domain before importing (FR-EP-006)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be written without writing"
    )
    args = parser.parse_args()

    # Determine which directories to process
    staging_path = args.staging_path
    if staging_path.is_dir() and (staging_path / "manifest.json").exists():
        # Single domain directory
        dirs_to_process = [staging_path]
    elif staging_path.is_dir():
        # Parent directory — find subdirectories with manifests
        dirs_to_process = sorted(
            d for d in staging_path.iterdir()
            if d.is_dir() and (d / "manifest.json").exists()
        )
        if not dirs_to_process:
            print(f"No staging directories with manifest.json found in {staging_path}")
            sys.exit(1)
    else:
        print(f"ERROR: {staging_path} is not a directory", file=sys.stderr)
        sys.exit(1)

    print("Connecting to Neo4j...")
    driver = get_driver()

    try:
        for staging_dir in dirs_to_process:
            domain_name = staging_dir.name
            print(f"\nProcessing {staging_dir}...")

            # Load and validate (FR-EP-004)
            manifest, items = load_staging_dir(staging_dir)
            print(f"  Loaded {len(items)} items" + 
                  (f", manifest: {manifest.pack_id}" if manifest else ""))

            if not items and not manifest:
                print("  Nothing to import, skipping")
                continue

            # Purge if requested (FR-EP-006)
            if args.purge_domain and items:
                purge_domain(driver, items[0].domain, args.dry_run)

            # Upsert pack
            if manifest:
                upsert_pack(driver, manifest, args.dry_run)

            # Upsert context nodes
            for item in items:
                upsert_context(driver, item, args.dry_run)

            # Upsert thread edges (after all nodes exist)
            for item in items:
                upsert_thread_edges(driver, item, args.dry_run)

            print(f"  ✓ {domain_name}: {len(items)} items imported")

        print("\nDone.")

    finally:
        driver.close()


if __name__ == "__main__":
    main()
