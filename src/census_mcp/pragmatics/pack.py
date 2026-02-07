"""Runtime pack loading and querying."""

import json
import sqlite3
from pathlib import Path
from typing import Any


class PackLoader:
    """Load and query compiled pragmatic context packs."""
    
    def __init__(self, packs_dir: str | Path = "packs"):
        """Initialize with packs directory.
        
        Args:
            packs_dir: Directory containing compiled .db pack files
        """
        self.packs_dir = Path(packs_dir)
        self.connections: dict[str, sqlite3.Connection] = {}
        self.loaded_packs: set[str] = set()
    
    def close(self) -> None:
        """Close all database connections."""
        for conn in self.connections.values():
            conn.close()
        self.connections.clear()
        self.loaded_packs.clear()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def load_pack(self, pack_id: str) -> None:
        """Load a pack and its parent chain.
        
        Args:
            pack_id: Pack identifier
            
        Raises:
            FileNotFoundError: If pack .db file not found
        """
        if pack_id in self.loaded_packs:
            return  # Already loaded
        
        db_path = self.packs_dir / f"{pack_id}.db"
        if not db_path.exists():
            raise FileNotFoundError(f"Pack not found: {db_path}")
        
        # Connect to database
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row  # Enable column access by name
        self.connections[pack_id] = conn
        self.loaded_packs.add(pack_id)
        
        # Load parent pack if it exists
        cursor = conn.execute("SELECT parent_pack FROM packs WHERE pack_id = ?", (pack_id,))
        row = cursor.fetchone()
        if row and row["parent_pack"]:
            self.load_pack(row["parent_pack"])
    
    def get_context_by_triggers(
        self,
        triggers: list[str],
        domain: str | None = None
    ) -> list[dict[str, Any]]:
        """Get context items matching any trigger.
        
        Searches across all loaded packs (including inherited packs).
        
        Args:
            triggers: List of trigger strings to match
            domain: Optional domain filter
            
        Returns:
            List of matching context items as dicts
        """
        results = []
        
        for pack_id, conn in self.connections.items():
            query = "SELECT * FROM context WHERE 1=1"
            params = []
            
            if domain:
                query += " AND domain = ?"
                params.append(domain)
            
            cursor = conn.execute(query, params)
            
            for row in cursor.fetchall():
                # Parse triggers JSON
                row_triggers = json.loads(row["triggers"]) if row["triggers"] else []
                
                # Check if any trigger matches
                if any(trigger in row_triggers for trigger in triggers):
                    item = dict(row)
                    # Parse JSON fields
                    item["triggers"] = row_triggers
                    item["source"] = json.loads(row["source"]) if row["source"] else None
                    item["_pack_id"] = pack_id  # Add pack provenance
                    results.append(item)
        
        return results
    
    def get_context_by_id(self, context_id: str) -> dict[str, Any] | None:
        """Get a specific context item by ID.
        
        Searches across all loaded packs.
        
        Args:
            context_id: Context identifier (e.g., "ACS-POP-001")
            
        Returns:
            Context item dict or None if not found
        """
        for pack_id, conn in self.connections.items():
            cursor = conn.execute(
                "SELECT * FROM context WHERE context_id = ?",
                (context_id,)
            )
            row = cursor.fetchone()
            if row:
                item = dict(row)
                item["triggers"] = json.loads(row["triggers"]) if row["triggers"] else []
                item["source"] = json.loads(row["source"]) if row["source"] else None
                item["_pack_id"] = pack_id
                return item
        
        return None
    
    def traverse_threads(
        self,
        from_context_id: str,
        edge_types: list[str] | None = None,
        max_depth: int = 3
    ) -> list[dict[str, Any]]:
        """Traverse thread edges from a context item.
        
        Args:
            from_context_id: Starting context ID
            edge_types: Optional filter for edge types
            max_depth: Maximum traversal depth
            
        Returns:
            List of reachable context items
        """
        visited = set()
        results = []
        
        def _traverse(context_id: str, depth: int):
            if depth > max_depth or context_id in visited:
                return
            
            visited.add(context_id)
            
            # Get edges from all loaded packs
            for conn in self.connections.values():
                query = "SELECT to_context_id, edge_type FROM threads WHERE from_context_id = ?"
                params = [context_id]
                
                if edge_types:
                    placeholders = ",".join(["?" for _ in edge_types])
                    query += f" AND edge_type IN ({placeholders})"
                    params.extend(edge_types)
                
                cursor = conn.execute(query, params)
                
                for row in cursor.fetchall():
                    target_id = row["to_context_id"]
                    edge_type = row["edge_type"]
                    
                    # Get target context
                    target = self.get_context_by_id(target_id)
                    if target and target_id not in visited:
                        target["_edge_type"] = edge_type  # Add edge provenance
                        target["_depth"] = depth + 1
                        results.append(target)
                        _traverse(target_id, depth + 1)
        
        _traverse(from_context_id, 0)
        return results
