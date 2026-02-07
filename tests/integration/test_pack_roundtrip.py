"""Integration test for complete pack pipeline round-trip."""

import pytest
from pathlib import Path

from census_mcp.pragmatics.pack import PackLoader


@pytest.mark.integration
def test_pack_roundtrip():
    """Test complete pipeline: staging JSON → SQLite → runtime query.
    
    This test assumes packs have been compiled via compile_all.py.
    Run: python scripts/compile_all.py before running this test.
    """
    packs_dir = Path("packs")
    
    # Check that packs exist
    required_packs = ["general_statistics.db", "census.db", "acs.db"]
    for pack_file in required_packs:
        pack_path = packs_dir / pack_file
        if not pack_path.exists():
            pytest.skip(f"Pack not compiled: {pack_path}. Run: python scripts/compile_all.py")
    
    with PackLoader(packs_dir=packs_dir) as loader:
        # Load ACS pack (should load parent chain)
        loader.load_pack("acs")
        
        # Verify all packs in chain are loaded
        assert "acs" in loader.loaded_packs
        assert "census" in loader.loaded_packs
        assert "general_statistics" in loader.loaded_packs
        
        # Test 1: Query by trigger - ACS population threshold
        results = loader.get_context_by_triggers(["population_threshold"])
        assert len(results) >= 1
        acs_context = next((r for r in results if r["context_id"] == "ACS-POP-001"), None)
        assert acs_context is not None
        assert "65,000" in acs_context["context_text"]
        assert acs_context["latitude"] == "none"
        
        # Test 2: Query by trigger - Virginia geography
        results = loader.get_context_by_triggers(["virginia"])
        assert len(results) >= 1
        va_context = next((r for r in results if r["context_id"] == "CEN-GEO-001"), None)
        assert va_context is not None
        assert "independent cities" in va_context["context_text"]
        
        # Test 3: Query by ID
        gen_context = loader.get_context_by_id("GEN-TV-001")
        assert gen_context is not None
        assert gen_context["domain"] == "general_statistics"
        assert "temporal_validity" in gen_context["category"]
        
        # Test 4: Thread traversal - from ACS-POP-001 to CEN-GEO-001
        threads = loader.traverse_threads("ACS-POP-001")
        assert len(threads) >= 1
        related_context = next((t for t in threads if t["context_id"] == "CEN-GEO-001"), None)
        assert related_context is not None
        assert related_context["_edge_type"] == "relates_to"
        
        # Test 5: Thread traversal - from CEN-GEO-001 to GEN-TV-001
        threads = loader.traverse_threads("CEN-GEO-001")
        assert len(threads) >= 1
        inherited_context = next((t for t in threads if t["context_id"] == "GEN-TV-001"), None)
        assert inherited_context is not None
        assert inherited_context["_edge_type"] == "inherits"
        
        # Test 6: Transitive thread traversal - from ACS to GEN via CEN
        threads = loader.traverse_threads("ACS-POP-001", max_depth=3)
        # Should reach GEN-TV-001 through CEN-GEO-001
        gen_reached = any(t["context_id"] == "GEN-TV-001" for t in threads)
        assert gen_reached, "Failed to reach GEN-TV-001 through transitive traversal"
        
        print("\n✓ All round-trip tests passed:")
        print("  - Pack loading with inheritance chain")
        print("  - Trigger-based retrieval")
        print("  - ID-based retrieval")
        print("  - Thread traversal (direct and transitive)")
