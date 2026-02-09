"""Pragmatics retrieval layer - thin wrapper around PackLoader."""

from typing import Any
from pathlib import Path

from census_mcp.pragmatics.pack import PackLoader


class PragmaticsRetriever:
    """Retrieve pragmatic context from compiled packs."""
    
    def __init__(self, loader: PackLoader):
        """Initialize with a PackLoader instance.
        
        Args:
            loader: Initialized PackLoader with packs already loaded
        """
        self.loader = loader
    
    def get_guidance_by_topics(
        self,
        topics: list[str],
        domain: str | None = None
    ) -> dict[str, Any]:
        """Tag lookup against loaded packs + thread traversal for related context.
        
        Args:
            topics: trigger tags e.g. ["small_area", "margin_of_error"]
            domain: optional domain filter e.g. "acs"
        
        Returns:
            {
                "guidance": [{"context_id": ..., "text": ..., "latitude": ..., "provenance": ...}, ...],
                "related": [{"context_id": ..., "text": ..., "edge_type": ..., "depth": ...}, ...],
                "sources": [{"document": ..., "section": ...}, ...]
            }
        """
        # Get direct matches by triggers (stored in triggers field)
        guidance = []
        related = []
        sources_set = set()
        
        # Query each loaded pack
        for pack_id, conn in self.loader.connections.items():
            # Filter by domain if specified
            if domain and pack_id != domain:
                continue
            
            # Build query for any trigger match
            cursor = conn.execute("SELECT * FROM context")
            for row in cursor.fetchall():
                context_dict = dict(row)
                
                # Parse triggers from JSON
                import json
                triggers = json.loads(context_dict.get('triggers', '[]'))
                
                # Check if any topic matches triggers
                if any(topic in triggers for topic in topics):
                    guidance_item = {
                        "context_id": context_dict['context_id'],
                        "text": context_dict['context_text'],
                        "latitude": context_dict['latitude'],
                        "provenance": context_dict.get('provenance'),
                        "tags": triggers
                    }
                    guidance.append(guidance_item)

                    # Track source documents from provenance.sources list
                    if context_dict.get('provenance'):
                        provenance_data = json.loads(context_dict['provenance'])
                        if isinstance(provenance_data, dict):
                            # New schema: provenance has sources list
                            for src in provenance_data.get('sources', []):
                                if isinstance(src, dict):
                                    sources_set.add(
                                        (src.get('document'), src.get('section'))
                                    )
                    
                    # For each matched context, traverse threads to find related
                    related_contexts = self.loader.traverse_threads(
                        context_dict['context_id'],
                        max_depth=2
                    )
                    for rel in related_contexts:
                        related_item = {
                            "context_id": rel['context_id'],
                            "text": rel['context_text'],
                            "edge_type": rel.get('_edge_type'),
                            "depth": rel.get('_depth')
                        }
                        related.append(related_item)
        
        # Build sources list
        sources = [
            {"document": doc, "section": sec}
            for doc, sec in sources_set
            if doc is not None
        ]
        
        return {
            "guidance": guidance,
            "related": related,
            "sources": sources
        }
    
    def get_guidance_by_parameters(
        self,
        product: str,
        geo_level: str,
        variables: list[str],
        year: int
    ) -> dict[str, Any]:
        """Match pragmatics against request parameters for auto-bundling with data.
        
        Logic (parameter-based filtering, NOT reasoning):
            - product == "acs1" → triggers: ["population_threshold", "1yr_acs"]
            - geo_level in ("tract", "block_group") → triggers: ["small_area", "block_group"]
            - product == "acs5" → triggers: ["period_estimate"]
            - any variable in income/dollar tables → triggers: ["dollar_values", "inflation"]
            - year near known break points → triggers: ["break_in_series"]
            - always include: ["margin_of_error", "reliability"]
        
        Returns same structure as get_guidance_by_topics.
        """
        triggers = []
        
        # Product-specific triggers
        if product == "acs1":
            triggers.extend(["population_threshold", "1yr_acs", "1-year"])
        elif product == "acs5":
            triggers.extend(["period_estimate", "5-year"])
        
        # Geography-specific triggers
        if geo_level in ("tract", "block_group"):
            triggers.extend(["small_area", "block_group"])
        
        # Variable-specific triggers (check for income/dollar tables)
        # B19* tables are income, B25* are housing values
        dollar_table_prefixes = ("B19", "B25")
        if any(var.startswith(dollar_table_prefixes) for var in variables):
            triggers.extend(["dollar_values", "inflation"])
        
        # Year-specific triggers (known break points)
        if year in (2009, 2010):
            triggers.append("break_in_series")
        
        # Always include MOE/reliability guidance
        triggers.extend(["margin_of_error", "reliability"])
        
        # Get guidance using the assembled triggers
        return self.get_guidance_by_topics(triggers, domain="acs")


def create_retriever(packs_dir: str | Path = "packs") -> PragmaticsRetriever:
    """Create and initialize a PragmaticsRetriever with loaded packs.
    
    Args:
        packs_dir: Directory containing compiled pack .db files
        
    Returns:
        Initialized PragmaticsRetriever
    """
    loader = PackLoader(packs_dir)
    loader.load_pack("acs")  # Loads acs + census + general_statistics via inheritance
    return PragmaticsRetriever(loader)
