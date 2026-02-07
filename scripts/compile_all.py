#!/usr/bin/env python3
"""Compile all staging directories to SQLite packs in dependency order.

Usage:
    python scripts/compile_all.py
"""

import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from compile_pack import compile_pack


def get_pack_dependencies() -> dict[str, str | None]:
    """Get pack dependencies from manifests.
    
    Returns:
        Dict mapping pack_id to parent_pack (or None if no parent)
    """
    staging_dir = Path("staging")
    dependencies = {}
    
    for manifest_path in staging_dir.glob("*/manifest.json"):
        with open(manifest_path) as f:
            manifest = json.load(f)
        dependencies[manifest["pack_id"]] = manifest.get("parent_pack")
    
    return dependencies


def topological_sort(dependencies: dict[str, str | None]) -> list[str]:
    """Sort packs in dependency order (parents before children).
    
    Args:
        dependencies: Dict mapping pack_id to parent_pack
        
    Returns:
        List of pack_ids in compilation order
    """
    # Build adjacency list (child -> parent edges)
    graph = {pack_id: [] for pack_id in dependencies}
    in_degree = {pack_id: 0 for pack_id in dependencies}
    
    for pack_id, parent in dependencies.items():
        if parent:
            graph[parent].append(pack_id)
            in_degree[pack_id] += 1
    
    # Kahn's algorithm
    queue = [pack_id for pack_id, degree in in_degree.items() if degree == 0]
    result = []
    
    while queue:
        # Sort for deterministic order
        queue.sort()
        pack_id = queue.pop(0)
        result.append(pack_id)
        
        for child in graph[pack_id]:
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)
    
    if len(result) != len(dependencies):
        raise ValueError("Circular dependency detected in pack inheritance")
    
    return result


def main():
    """Compile all packs in dependency order."""
    print("=== Compiling all packs ===")
    
    # Get dependencies
    dependencies = get_pack_dependencies()
    print(f"\nFound {len(dependencies)} packs")
    
    # Sort by dependency order
    pack_order = topological_sort(dependencies)
    print(f"Compilation order: {' -> '.join(pack_order)}\n")
    
    # Compile each pack
    compiled_packs = {}
    for pack_id in pack_order:
        staging_path = Path(f"staging/{pack_id}")
        output_path = Path(f"packs/{pack_id}.db")
        
        parent_pack = dependencies[pack_id]
        parent_db = Path(f"packs/{parent_pack}.db") if parent_pack else None
        
        compile_pack(staging_path, output_path, parent_db)
        compiled_packs[pack_id] = output_path
    
    print(f"\n✓ Successfully compiled {len(compiled_packs)} packs")
    for pack_id, db_path in compiled_packs.items():
        size_kb = db_path.stat().st_size / 1024
        print(f"  - {pack_id}: {db_path} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
