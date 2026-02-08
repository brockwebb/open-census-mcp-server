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
        
        # Test 2: Query by trigger - independent city (principle-based)
        results = loader.get_context_by_triggers(["independent_city"])
        assert len(results) >= 1
        ic_context = next((r for r in results if r["context_id"] == "CEN-GEO-001"), None)
        assert ic_context is not None
        assert "county-equivalent" in ic_context["context_text"].lower()
        
        # Test 3: Query by ID - general statistics
        gen_context = loader.get_context_by_id("GEN-TV-001")
        assert gen_context is not None
        assert gen_context["domain"] == "general_statistics"
        assert "temporal_validity" in gen_context["category"]
        
        # Test 4: Thread traversal - CEN-GEO-001 inherits from GEN-TV-001
        threads = loader.traverse_threads("CEN-GEO-001")
        assert len(threads) >= 1
        inherited_context = next((t for t in threads if t["context_id"] == "GEN-TV-001"), None)
        assert inherited_context is not None
        assert inherited_context["_edge_type"] == "inherits"
        
        # Test 5: Thread traversal - ACS MOE chain (MOE-001 → MOE-002 → MOE-003)
        threads = loader.traverse_threads("ACS-MOE-001")
        assert len(threads) >= 1
        moe2 = next((t for t in threads if t["context_id"] == "ACS-MOE-002"), None)
        assert moe2 is not None
        assert moe2["_edge_type"] == "relates_to"
        
        # Test 6: Transitive thread traversal - MOE chain reaches MOE-003
        threads = loader.traverse_threads("ACS-MOE-001", max_depth=3)
        moe3_reached = any(t["context_id"] == "ACS-MOE-003" for t in threads)
        assert moe3_reached, "Failed to reach ACS-MOE-003 through transitive traversal"
        
        # Test 7: New content - disclosure avoidance
        results = loader.get_context_by_triggers(["disclosure_avoidance"])
        assert len(results) >= 1
        dis_context = next((r for r in results if r["context_id"] == "ACS-DIS-002"), None)
        assert dis_context is not None
        assert "differential privacy" in dis_context["context_text"].lower()
        assert dis_context["latitude"] == "none"
        
        # Test 8: New content - independent cities in ACS pack
        results = loader.get_context_by_triggers(["independent_cities"])
        assert len(results) >= 1
        ind_context = next((r for r in results if r["context_id"] == "ACS-IND-001"), None)
        assert ind_context is not None
        assert "county-equivalent" in ind_context["context_text"].lower()
        
        print("\n✓ All round-trip tests passed:")
        print("  - Pack loading with inheritance chain")
        print("  - Trigger-based retrieval (population, independent cities, disclosure)")
        print("  - ID-based retrieval")
        print("  - Thread traversal (inherits and relates_to)")
        print("  - Transitive traversal (MOE chain)")
        print("  - New G.10/G.11/G.7 content accessible")
