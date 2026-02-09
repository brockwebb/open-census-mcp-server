"""Unit tests for PackLoader."""

import json
import sqlite3
import tempfile
from pathlib import Path

import pytest

from census_mcp.pragmatics.schema import create_tables
from census_mcp.pragmatics.pack import PackLoader


@pytest.fixture
def test_pack_db(tmp_path):
    """Create a test pack database."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    
    create_tables(conn)
    
    # Insert test data
    conn.execute(
        """INSERT INTO packs (pack_id, pack_name, parent_pack, version, compiled_date)
           VALUES ('test', 'Test Pack', NULL, '1.0.0', '2024-01-01')"""
    )
    
    conn.execute(
        """INSERT INTO context (context_id, domain, category, latitude, context_text, triggers, provenance)
           VALUES ('TST-001', 'test', 'test_cat', 'none', 'Test context', ?, NULL)""",
        (json.dumps(["trigger1", "trigger2"]),)
    )
    
    conn.execute(
        """INSERT INTO context (context_id, domain, category, latitude, context_text, triggers, provenance)
           VALUES ('TST-002', 'test', 'test_cat', 'narrow', 'Another context', ?, NULL)""",
        (json.dumps(["trigger3"]),)
    )
    
    conn.execute(
        """INSERT INTO threads (from_context_id, to_context_id, edge_type)
           VALUES ('TST-001', 'TST-002', 'relates_to')"""
    )
    
    conn.execute(
        """INSERT INTO pack_contents (pack_id, context_id) VALUES ('test', 'TST-001')"""
    )
    conn.execute(
        """INSERT INTO pack_contents (pack_id, context_id) VALUES ('test', 'TST-002')"""
    )
    
    conn.commit()
    conn.close()
    
    return db_path


def test_pack_loading(test_pack_db, tmp_path):
    """Test pack loading."""
    loader = PackLoader(packs_dir=tmp_path)
    loader.load_pack("test")
    
    assert "test" in loader.loaded_packs
    assert "test" in loader.connections
    
    loader.close()


def test_pack_not_found():
    """Test error when pack not found."""
    with tempfile.TemporaryDirectory() as tmpdir:
        loader = PackLoader(packs_dir=tmpdir)
        
        with pytest.raises(FileNotFoundError):
            loader.load_pack("nonexistent")


def test_get_context_by_triggers(test_pack_db, tmp_path):
    """Test trigger-based retrieval."""
    with PackLoader(packs_dir=tmp_path) as loader:
        loader.load_pack("test")
        
        # Match trigger1
        results = loader.get_context_by_triggers(["trigger1"])
        assert len(results) == 1
        assert results[0]["context_id"] == "TST-001"
        assert results[0]["triggers"] == ["trigger1", "trigger2"]
        
        # Match trigger3
        results = loader.get_context_by_triggers(["trigger3"])
        assert len(results) == 1
        assert results[0]["context_id"] == "TST-002"
        
        # Match multiple
        results = loader.get_context_by_triggers(["trigger1", "trigger3"])
        assert len(results) == 2
        
        # No match
        results = loader.get_context_by_triggers(["nonexistent"])
        assert len(results) == 0


def test_get_context_by_id(test_pack_db, tmp_path):
    """Test ID-based retrieval."""
    with PackLoader(packs_dir=tmp_path) as loader:
        loader.load_pack("test")
        
        item = loader.get_context_by_id("TST-001")
        assert item is not None
        assert item["context_id"] == "TST-001"
        assert item["context_text"] == "Test context"
        
        # Not found
        item = loader.get_context_by_id("NONEXISTENT")
        assert item is None


def test_traverse_threads(test_pack_db, tmp_path):
    """Test thread traversal."""
    with PackLoader(packs_dir=tmp_path) as loader:
        loader.load_pack("test")
        
        # Traverse from TST-001
        results = loader.traverse_threads("TST-001")
        assert len(results) == 1
        assert results[0]["context_id"] == "TST-002"
        assert results[0]["_edge_type"] == "relates_to"
        assert results[0]["_depth"] == 1
        
        # Traverse from TST-002 (no outgoing edges)
        results = loader.traverse_threads("TST-002")
        assert len(results) == 0


def test_context_manager():
    """Test context manager."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with PackLoader(packs_dir=tmpdir) as loader:
            assert len(loader.connections) == 0
        
        # Should be closed after exit
        assert len(loader.connections) == 0
