#!/usr/bin/env python3
"""Compile a staging directory to a SQLite pack.

Usage:
    python scripts/compile_pack.py staging/acs --output packs/acs.db
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from census_mcp.pragmatics.schema import create_tables
from census_mcp.pragmatics.models import ContextItem, PackManifest
from pydantic import ValidationError


def load_manifest(staging_dir: Path) -> PackManifest:
    """Load and validate pack manifest."""
    manifest_path = staging_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing manifest.json in {staging_dir}")
    
    with open(manifest_path) as f:
        data = json.load(f)
    
    return PackManifest(**data)


def load_context_items(staging_dir: Path) -> list[ContextItem]:
    """Load and validate all context items from JSON files."""
    items = []
    errors = []
    
    # Find all .json files except manifest.json
    json_files = [f for f in staging_dir.glob("*.json") if f.name != "manifest.json"]
    
    for json_file in json_files:
        try:
            with open(json_file) as f:
                data = json.load(f)
            
            # Data should be a list of context items
            if not isinstance(data, list):
                errors.append(f"{json_file.name}: Expected list of context items, got {type(data).__name__}")
                continue
            
            for i, item_data in enumerate(data):
                try:
                    item = ContextItem(**item_data)
                    items.append(item)
                except ValidationError as e:
                    errors.append(f"{json_file.name}[{i}]: {e}")
        
        except json.JSONDecodeError as e:
            errors.append(f"{json_file.name}: JSON decode error: {e}")
        except Exception as e:
            errors.append(f"{json_file.name}: {e}")
    
    if errors:
        print("Validation errors:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)
    
    return items


def compile_pack(staging_dir: Path, output_path: Path, parent_db_path: Path | None = None) -> None:
    """Compile staging directory to SQLite pack.
    
    Args:
        staging_dir: Path to staging directory
        output_path: Path to output .db file
        parent_db_path: Path to parent pack .db (optional, for inheritance verification)
    """
    print(f"Compiling {staging_dir} -> {output_path}")
    
    # Load and validate manifest
    manifest = load_manifest(staging_dir)
    print(f"  Pack: {manifest.pack_name} ({manifest.pack_id}) v{manifest.version}")
    
    # Verify parent pack exists if specified
    if manifest.parent_pack:
        if not parent_db_path or not parent_db_path.exists():
            print(f"  ERROR: Parent pack '{manifest.parent_pack}' not found", file=sys.stderr)
            sys.exit(1)
        print(f"  Parent: {manifest.parent_pack}")
    
    # Load and validate context items
    items = load_context_items(staging_dir)
    print(f"  Loaded {len(items)} context items")
    
    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create SQLite database
    conn = sqlite3.connect(output_path)
    try:
        # Create schema
        create_tables(conn)
        
        # Insert pack metadata
        conn.execute(
            """INSERT INTO packs (pack_id, pack_name, parent_pack, version, compiled_date)
               VALUES (?, ?, ?, ?, ?)""",
            (
                manifest.pack_id,
                manifest.pack_name,
                manifest.parent_pack,
                manifest.version,
                datetime.utcnow().isoformat()
            )
        )
        
        # Insert context items
        for item in items:
            # Serialize triggers and source as JSON
            triggers_json = json.dumps(item.triggers)
            source_json = json.dumps(item.source.model_dump()) if item.source else None
            
            conn.execute(
                """INSERT INTO context (context_id, domain, category, latitude, context_text, triggers, source)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    item.context_id,
                    item.domain,
                    item.category,
                    item.latitude,
                    item.context_text,
                    triggers_json,
                    source_json
                )
            )
            
            # Insert thread edges
            for edge in item.thread_edges:
                conn.execute(
                    """INSERT INTO threads (from_context_id, to_context_id, edge_type)
                       VALUES (?, ?, ?)""",
                    (item.context_id, edge.target, edge.edge_type)
                )
            
            # Insert pack contents
            conn.execute(
                """INSERT INTO pack_contents (pack_id, context_id)
                   VALUES (?, ?)""",
                (manifest.pack_id, item.context_id)
            )
        
        conn.commit()
        print(f"  ✓ Compiled successfully")
    
    except Exception as e:
        conn.rollback()
        print(f"  ERROR: {e}", file=sys.stderr)
        raise
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Compile a staging directory to SQLite pack")
    parser.add_argument("staging_dir", type=Path, help="Path to staging directory")
    parser.add_argument("--output", "-o", type=Path, required=True, help="Output .db file path")
    parser.add_argument("--parent-db", type=Path, help="Parent pack .db for inheritance verification")
    
    args = parser.parse_args()
    
    if not args.staging_dir.is_dir():
        print(f"ERROR: {args.staging_dir} is not a directory", file=sys.stderr)
        sys.exit(1)
    
    compile_pack(args.staging_dir, args.output, args.parent_db)


if __name__ == "__main__":
    main()
