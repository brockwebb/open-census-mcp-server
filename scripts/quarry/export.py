"""Export curated harvest results to staging JSON (Layer 4)."""


def export_to_staging(harvest_results_path: str, output_dir: str = "staging/"):
    """Transform curated harvest results into staging JSON conforming to pragmatics schema.

    Args:
        harvest_results_path: Path to curated harvest results JSON
        output_dir: Output directory for staging JSON files

    Raises:
        NotImplementedError: This function is not yet implemented

    NOT YET IMPLEMENTED — depends on harvest curation workflow design.

    The export pipeline will:
    1. Load curated harvest results (ContextItem candidates that passed expert review)
    2. Transform to pragmatics schema (context_id, domain, category, latitude, context_text,
       triggers, thread_edges, provenance)
    3. Write to staging JSON files per domain
    4. Update pack manifests
    5. Enable downstream compilation via compile_pack.py → SQLite packs

    See ADR-010 (harvest curation workflow) when available.
    """
    raise NotImplementedError("Export pipeline pending harvest curation design (ADR-010)")
