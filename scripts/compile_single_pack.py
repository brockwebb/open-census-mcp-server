#!/usr/bin/env python3
"""Compile a single-file pack JSON to SQLite.

Usage:
    python scripts/compile_single_pack.py staging/acs.json
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from census_mcp.pragmatics.schema import create_tables


def compile_pack(json_path: Path):
    """Compile single JSON file to SQLite pack."""
    
    print(f"Reading {json_path}...")
    with open(json_path) as f:
        data = json.load(f)
    
    # Validate structure
    required = ['pack_id', 'pack_name', 'version', 'contexts']
    for field in required:
        if field not in data:
            print(f"ERROR: Missing required field '{field}'")
            sys.exit(1)
    
    pack_id = data['pack_id']
    output_path = Path(f"packs/{pack_id}.db")
    
    print(f"Compiling {pack_id} -> {output_path}")
    print(f"  Pack: {data['pack_name']} v{data['version']}")
    print(f"  Contexts: {len(data['contexts'])}")
    print(f"  Threads: {len(data.get('threads', []))}")
    
    # Create output directory
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Remove existing DB if present
    if output_path.exists():
        output_path.unlink()
    
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
                data['pack_id'],
                data['pack_name'],
                data.get('parent_pack'),
                data['version'],
                datetime.utcnow().isoformat()
            )
        )
        
        # Insert contexts
        for ctx in data['contexts']:
            # Serialize tags as JSON
            tags_json = json.dumps(ctx.get('tags', []))
            source_json = json.dumps({'document': ctx['source']}) if ctx.get('source') else None
            
            conn.execute(
                """INSERT INTO context (context_id, domain, category, latitude, context_text, triggers, source)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    ctx['context_id'],
                    ctx['domain'],
                    ctx.get('category', ''),
                    ctx['latitude'],
                    ctx['context_text'],
                    tags_json,  # Store tags in triggers field for now
                    source_json
                )
            )
            
            # Insert pack contents
            conn.execute(
                """INSERT INTO pack_contents (pack_id, context_id)
                   VALUES (?, ?)""",
                (data['pack_id'], ctx['context_id'])
            )
        
        # Insert threads
        for thread in data.get('threads', []):
            conn.execute(
                """INSERT INTO threads (from_context_id, to_context_id, edge_type)
                   VALUES (?, ?, ?)""",
                (
                    thread['from_context'],
                    thread['to_context'],
                    thread['edge_type']
                )
            )
        
        conn.commit()
        
        # Verify
        cursor = conn.execute("SELECT count(*) FROM context")
        ctx_count = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT count(*) FROM threads")
        thread_count = cursor.fetchone()[0]
        
        print(f"\n✓ Compiled successfully:")
        print(f"  - {ctx_count} contexts")
        print(f"  - {thread_count} threads")
        print(f"  - Output: {output_path}")
        
    except Exception as e:
        conn.rollback()
        print(f"ERROR: {e}", file=sys.stderr)
        raise
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Compile single-file pack JSON to SQLite")
    parser.add_argument("json_file", type=Path, help="Path to pack JSON file")
    
    args = parser.parse_args()
    
    if not args.json_file.exists():
        print(f"ERROR: {args.json_file} not found", file=sys.stderr)
        sys.exit(1)
    
    compile_pack(args.json_file)


if __name__ == "__main__":
    main()
