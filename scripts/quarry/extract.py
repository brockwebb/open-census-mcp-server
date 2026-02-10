"""Main extraction pipeline: PDF → chunks → LLM → Neo4j quarry."""

import argparse
import json
import sys
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from . import config
from .chunk import chunk_pdf
from .prompts import build_extraction_prompt, build_batch_extraction_prompt
from .utils import get_anthropic_client, get_neo4j_driver, parse_llm_json, setup_logging, validate_extraction

logger = setup_logging(__name__)


def get_processed_chunks(driver, catalog_id):
    """Get set of chunk indexes already processed for this document.

    Args:
        driver: Neo4j driver
        catalog_id: Source document catalog_id

    Returns:
        Set of chunk indexes already processed
    """
    with driver.session(database=config.NEO4J_DATABASE) as session:
        result = session.run("""
            MATCH (n)-[sf:SOURCED_FROM]->(sd:SourceDocument {catalog_id: $catalog_id})
            WHERE sf.chunk_index IS NOT NULL
            RETURN DISTINCT sf.chunk_index AS idx
        """, {"catalog_id": catalog_id})
        return {r["idx"] for r in result}


def get_existing_entities(driver):
    """Query quarry for existing Layer 0 entity names for MERGE targets.

    Returns:
        Dict of entity type -> list of names
    """
    entities = {}

    with driver.session(database=config.NEO4J_DATABASE) as session:
        # DataProducts
        result = session.run("MATCH (n:DataProduct) RETURN n.name AS name ORDER BY name")
        entities["DataProduct"] = [r["name"] for r in result if r["name"] is not None]

        # CanonicalConcepts
        result = session.run("MATCH (n:CanonicalConcept) RETURN n.name AS name ORDER BY name")
        entities["CanonicalConcept"] = [r["name"] for r in result if r["name"] is not None]

        # SurveyProcesses
        result = session.run("MATCH (n:SurveyProcess) RETURN n.name AS name ORDER BY name")
        entities["SurveyProcess"] = [r["name"] for r in result if r["name"] is not None]

    logger.info(f"Existing entities: {len(entities['DataProduct'])} DataProducts, "
                f"{len(entities['CanonicalConcept'])} CanonicalConcepts, "
                f"{len(entities['SurveyProcess'])} SurveyProcesses")

    return entities


def write_node_to_neo4j(session, node, catalog_id):
    """Write a node to Neo4j using MERGE.

    Returns:
        Dict with created/matched status
    """
    node_type = node["type"]
    node_id = node["id"]
    props = node.get("properties", {})

    # Build MERGE query based on node type
    if node_type == "QualityAttribute":
        # QualityAttribute: MERGE on name + dimension
        query = """
        MERGE (n:QualityAttribute {name: $name, dimension: $dimension})
        ON CREATE SET n.id = $id,
                      n.value_type = $value_type,
                      n.value_number = $value_number,
                      n.value_string = $value_string
        ON MATCH SET n.value_type = COALESCE(n.value_type, $value_type),
                     n.value_number = COALESCE(n.value_number, $value_number),
                     n.value_string = COALESCE(n.value_string, $value_string)
        RETURN id(n) AS node_id, n.name AS matched_name
        """
        params = {
            "id": node_id,
            "name": props.get("name"),
            "dimension": props.get("dimension"),
            "value_type": props.get("value_type"),
            "value_number": props.get("value_number"),
            "value_string": props.get("value_string"),
        }
    elif node_type in ["DataProduct", "CanonicalConcept", "SurveyProcess"]:
        # Reference nodes: MERGE on name only (should already exist from Layer 0)
        query = f"""
        MERGE (n:{node_type} {{name: $name}})
        ON CREATE SET n.id = $id
        RETURN id(n) AS node_id, n.name AS matched_name
        """
        params = {"id": node_id, "name": props.get("name", node_id)}
    elif node_type == "SourceDocument":
        # SourceDocument: MERGE on catalog_id
        query = """
        MERGE (n:SourceDocument {catalog_id: $catalog_id})
        ON CREATE SET n.id = $id,
                      n.title = $title,
                      n.year = $year,
                      n.survey = $survey,
                      n.local_path = $local_path
        RETURN id(n) AS node_id, n.catalog_id AS matched_name
        """
        params = {
            "id": node_id,
            "catalog_id": props.get("catalog_id", catalog_id),
            "title": props.get("title"),
            "year": props.get("year"),
            "survey": props.get("survey"),
            "local_path": props.get("local_path"),
        }
    else:
        # All other nodes: MERGE on id
        prop_set = ", ".join(f"n.{k} = ${k}" for k in props.keys())
        query = f"""
        MERGE (n:{node_type} {{id: $id}})
        ON CREATE SET {prop_set if prop_set else 'n.created = timestamp()'}
        RETURN id(n) AS node_id, n.id AS matched_name
        """
        params = {"id": node_id, **props}

    result = session.run(query, params)
    record = result.single()
    summary = result.consume()

    return {
        "neo4j_id": record["node_id"] if record else None,
        "created": summary.counters.nodes_created > 0,
        "type": node_type
    }


def write_relationship_to_neo4j(session, rel, node_map):
    """Write a relationship to Neo4j using MERGE.

    Args:
        session: Neo4j session
        rel: Relationship dict with source, target, type, properties
        node_map: Dict mapping node IDs to Neo4j internal IDs

    Returns:
        Dict with created/matched status
    """
    source_id = node_map.get(rel["source"])
    target_id = node_map.get(rel["target"])

    if not source_id or not target_id:
        logger.warning(f"Skipping relationship {rel['type']}: missing node mapping")
        return {"created": False, "type": rel["type"], "error": "missing_node"}

    rel_type = rel["type"]
    props = rel.get("properties", {})

    # Build property SET clause
    prop_set = ", ".join(f"r.{k} = ${k}" for k in props.keys()) if props else ""

    query = f"""
    MATCH (source) WHERE id(source) = $source_id
    MATCH (target) WHERE id(target) = $target_id
    MERGE (source)-[r:{rel_type}]->(target)
    {f"SET {prop_set}" if prop_set else ""}
    RETURN id(r) AS rel_id
    """

    params = {"source_id": source_id, "target_id": target_id, **props}

    result = session.run(query, params)
    record = result.single()
    summary = result.consume()

    return {
        "created": summary.counters.relationships_created > 0,
        "type": rel_type
    }


def extract_chunk(client, chunk, source_doc, existing_entities, dry_run=False):
    """Extract structured knowledge from a single chunk.

    Returns:
        Extraction result dict or None on failure
    """
    # Build prompt
    prompt = build_extraction_prompt(
        chunk_text=chunk.text,
        section_path=chunk.section_path,
        source_doc=source_doc,
        existing_entities=existing_entities
    )

    if dry_run:
        return {"prompt": prompt, "response": None, "parsed": None}

    # Call Anthropic API
    try:
        message = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=4096,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text
        tokens_used = {"input": message.usage.input_tokens, "output": message.usage.output_tokens}

    except Exception as e:
        logger.error(f"API call failed for chunk {chunk.chunk_index}: {e}")
        return None

    # Parse JSON
    try:
        data = parse_llm_json(response_text)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse failed for chunk {chunk.chunk_index}: {e}")
        return {"raw": response_text, "error": "parse_failed", "tokens": tokens_used}

    # Validate with evolutionary vocabulary
    is_valid, errors, corrections = validate_extraction(data, source_doc["catalog_id"])
    if not is_valid:
        logger.warning(f"Validation failed for chunk {chunk.chunk_index}: {errors[:3]}")

    # Apply corrections to data (reclassified nodes)
    for correction in corrections.get("reclassified_nodes", []):
        for node in data["nodes"]:
            if node["id"] == correction["node_id"]:
                node["type"] = correction["new_type"]
                # Remove fact_category property if reclassifying
                if "properties" in node and "fact_category" in node["properties"]:
                    del node["properties"]["fact_category"]

    return {
        "data": data,
        "valid": is_valid,
        "errors": errors if not is_valid else [],
        "corrections": corrections,
        "tokens": tokens_used
    }


def extract_batch(client, chunks, source_doc, existing_entities, dry_run=False):
    """Extract structured knowledge from a batch of chunks in one API call.

    Args:
        client: Anthropic client
        chunks: List of chunks to process together
        source_doc: Source document metadata
        existing_entities: Existing entity names for MERGE
        dry_run: If True, return prompt without calling API

    Returns:
        List of extraction results (one per chunk) or None on failure
    """
    if not chunks:
        return []

    # Build batch prompt using the proper template
    batch_prompt = build_batch_extraction_prompt(chunks, source_doc, existing_entities)

    if dry_run:
        return [{"prompt": batch_prompt, "response": None, "parsed": None} for _ in chunks]

    # Call API
    try:
        message = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=8192,  # Larger for batch responses
            temperature=0,
            messages=[{"role": "user", "content": batch_prompt}]
        )
        response_text = message.content[0].text
        tokens_used = {"input": message.usage.input_tokens, "output": message.usage.output_tokens}
    except Exception as e:
        logger.error(f"API call failed for batch of {len(chunks)} chunks: {e}")
        return None

    # Parse JSON array
    try:
        batch_data = parse_llm_json(response_text)
        if not isinstance(batch_data, list):
            # Try wrapping in array if single object returned
            batch_data = [batch_data]
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse failed for batch: {e}")
        return [{"raw": response_text, "error": "parse_failed", "tokens": tokens_used} for _ in chunks]

    # Validate and process each extraction
    results = []
    for i, chunk in enumerate(chunks):
        if i < len(batch_data):
            data = batch_data[i]
            is_valid, errors, corrections = validate_extraction(data, source_doc["catalog_id"])

            if not is_valid:
                logger.warning(f"Validation failed for chunk {chunk.chunk_index}: {errors[:3]}")

            # Apply corrections
            for correction in corrections.get("reclassified_nodes", []):
                for node in data.get("nodes", []):
                    if node.get("id") == correction["node_id"]:
                        node["type"] = correction["new_type"]
                        if "properties" in node and "fact_category" in node["properties"]:
                            del node["properties"]["fact_category"]

            results.append({
                "data": data,
                "valid": is_valid,
                "errors": errors if not is_valid else [],
                "corrections": corrections,
                "tokens": {"input": tokens_used["input"] // len(chunks), "output": tokens_used["output"] // len(chunks)}
            })
        else:
            # Missing extraction for this chunk
            results.append(None)

    return results


def process_chunk_batch(chunks, client, source_doc, existing_entities, dry_run, driver, total_chunks, batch_size=1):
    """Process a batch of chunks (worker function for parallel extraction).

    Args:
        chunks: List of chunks to process (can be 1 for single-chunk mode)
        batch_size: Number of chunks per API call (1 = single mode, >1 = batch mode)

    Returns:
        List of tuples: [(chunk_index, result_dict, stats_update), ...]
    """
    if not chunks:
        return []

    # Single chunk or batch?
    if batch_size == 1 or len(chunks) == 1:
        # Single-chunk mode (original behavior)
        chunk = chunks[0]
        chunk_idx = chunk.chunk_index + 1
        logger.info(f"Processing chunk {chunk_idx}/{total_chunks}: "
                   f"{' > '.join(chunk.section_path[:2]) if chunk.section_path else '(root)'}")
        result = extract_chunk(client, chunk, source_doc, existing_entities, dry_run)
        results = [result] if result else [None]
    else:
        # Batch mode
        chunk_indices = [c.chunk_index + 1 for c in chunks]
        logger.info(f"Processing batch {chunk_indices[0]}-{chunk_indices[-1]}/{total_chunks} ({len(chunks)} chunks)")
        results = extract_batch(client, chunks, source_doc, existing_entities, dry_run)

    # Process results for each chunk
    batch_results = []
    for i, (chunk, result) in enumerate(zip(chunks, results)):
        chunk_idx = chunk.chunk_index + 1

        if not result:
            batch_results.append((chunk_idx, None, {"chunks_failed": 1}))
            continue

        if dry_run:
            batch_results.append((chunk_idx, result, {}))
            continue

        # Stats for this chunk
        stats_update = {
            "chunks_processed": 1,
            "total_input_tokens": result["tokens"]["input"],
            "total_output_tokens": result["tokens"]["output"],
            "validation_errors": 1 if not result.get("valid") else 0,
            "nodes_created": Counter(),
            "nodes_matched": Counter(),
            "relationships_created": Counter(),
            "relationships_matched": Counter(),
        }

        data = result["data"]

        # Write to Neo4j
        with driver.session(database=config.NEO4J_DATABASE) as session:
            # Ensure SourceDocument exists
            session.run("""
                MERGE (sd:SourceDocument {catalog_id: $catalog_id})
                ON CREATE SET sd.title = $title, sd.year = $year,
                             sd.survey = $survey, sd.local_path = $local_path
            """, {
                "catalog_id": source_doc["catalog_id"],
                "title": source_doc["title"],
                "year": source_doc["year"],
                "survey": source_doc["survey"],
                "local_path": source_doc["local_path"]
            })

            # Write nodes
            node_map = {}
            for node in data.get("nodes", []):
                write_result = write_node_to_neo4j(session, node, source_doc["catalog_id"])
                node_map[node["id"]] = write_result["neo4j_id"]

                if write_result["created"]:
                    stats_update["nodes_created"][write_result["type"]] += 1
                else:
                    stats_update["nodes_matched"][write_result["type"]] += 1

            # Write relationships
            for rel in data.get("relationships", []):
                write_result = write_relationship_to_neo4j(session, rel, node_map)
                if write_result.get("created"):
                    stats_update["relationships_created"][write_result["type"]] += 1
                else:
                    stats_update["relationships_matched"][write_result["type"]] += 1

            # Link nodes to SourceDocument with chunk_index
            for neo4j_id in node_map.values():
                if neo4j_id:
                    session.run("""
                        MATCH (n) WHERE id(n) = $node_id
                        MATCH (sd:SourceDocument {catalog_id: $catalog_id})
                        MERGE (n)-[sf:SOURCED_FROM]->(sd)
                        ON CREATE SET sf.chunk_index = $chunk_index
                    """, {
                        "node_id": neo4j_id,
                        "catalog_id": source_doc["catalog_id"],
                        "chunk_index": chunk.chunk_index
                    })

        batch_results.append((chunk_idx, result, stats_update))

    return batch_results


def run_extraction(source_key, dry_run=False, limit=None, workers=1, resume=False, batch_size=1):
    """Run full extraction pipeline with optional parallel workers and batching.

    Args:
        source_key: Key in SOURCE_CATALOG
        dry_run: If True, show extraction output without writing to Neo4j
        limit: Limit number of chunks to process
        workers: Number of parallel workers (1-5, default 1)
        resume: If True, skip chunks that have already been processed
        batch_size: Number of chunks per API call (default 1, recommended 3)

    Returns:
        Exit code (0 = success)
    """
    # Validate workers
    if workers < 1 or workers > 5:
        logger.error(f"Invalid workers count: {workers}. Must be 1-5.")
        return 1
    # Get source config
    if source_key not in config.SOURCE_CATALOG:
        logger.error(f"Unknown source: {source_key}")
        return 1

    source_doc = config.SOURCE_CATALOG[source_key]
    pdf_path = config.REPO_ROOT / source_doc["local_path"]

    if not pdf_path.exists():
        logger.error(f"PDF not found: {pdf_path}")
        return 1

    logger.info(f"Processing: {source_doc['title']}")

    # Initialize clients
    client = None if dry_run else get_anthropic_client()
    driver = get_neo4j_driver()

    try:
        # Get existing entities
        existing_entities = get_existing_entities(driver)

        # Chunk PDF
        chunks = chunk_pdf(str(pdf_path), source_doc["catalog_id"])
        if limit:
            chunks = chunks[:limit]
            logger.info(f"Limited to first {limit} chunks")

        # Resume: skip already-processed chunks
        if resume:
            processed_chunks = get_processed_chunks(driver, source_doc["catalog_id"])
            original_count = len(chunks)
            chunks = [c for c in chunks if c.chunk_index not in processed_chunks]
            skipped = original_count - len(chunks)
            if skipped > 0:
                logger.info(f"Resume mode: skipping {skipped} already-processed chunks ({len(chunks)} remaining)")
            else:
                logger.info(f"Resume mode: no chunks to skip, processing all {len(chunks)}")

        # Metrics (thread-safe with lock)
        stats_lock = threading.Lock()
        stats = {
            "chunks_processed": 0,
            "chunks_failed": 0,
            "nodes_created": Counter(),
            "nodes_matched": Counter(),
            "relationships_created": Counter(),
            "relationships_matched": Counter(),
            "validation_errors": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
        }

        # Group chunks into batches
        batches = []
        for i in range(0, len(chunks), batch_size):
            batches.append(chunks[i:i+batch_size])

        total_chunks = len(chunks)
        if batch_size > 1:
            logger.info(f"Batch mode: {len(batches)} batches of up to {batch_size} chunks ({total_chunks} total chunks)")

        # Process batches (parallel or sequential based on workers count)
        if dry_run or workers == 1:
            # Sequential mode for dry-run or single worker
            for batch in batches:
                batch_results = process_chunk_batch(
                    batch, client, source_doc, existing_entities, dry_run, driver, total_chunks, batch_size
                )

                for chunk_idx, result, stats_update in batch_results:
                    if result is None:
                        stats["chunks_failed"] += 1
                        continue

                    if dry_run:
                        print(f"\n=== CHUNK {chunk_idx} ===")
                        print(f"Prompt length: {len(result['prompt'])} chars" if 'prompt' in result else "Batch result")
                        continue

                    # Update stats
                    with stats_lock:
                        for key in ["chunks_processed", "total_input_tokens", "total_output_tokens", "validation_errors"]:
                            stats[key] += stats_update[key]
                        for key in ["nodes_created", "nodes_matched", "relationships_created", "relationships_matched"]:
                            stats[key] += stats_update[key]
        else:
            # Parallel mode
            logger.info(f"Using {workers} parallel workers with {len(batches)} batches")
            with ThreadPoolExecutor(max_workers=workers) as executor:
                # Submit all batches
                futures = {
                    executor.submit(
                        process_chunk_batch,
                        batch, client, source_doc, existing_entities, dry_run, driver, total_chunks, batch_size
                    ): batch
                    for batch in batches
                }

                # Collect results as they complete
                for future in as_completed(futures):
                    try:
                        batch_results = future.result()

                        for chunk_idx, result, stats_update in batch_results:
                            if result is None:
                                with stats_lock:
                                    stats["chunks_failed"] += 1
                                continue

                            # Update stats (thread-safe)
                            with stats_lock:
                                for key in ["chunks_processed", "total_input_tokens", "total_output_tokens", "validation_errors"]:
                                    stats[key] += stats_update[key]
                                for key in ["nodes_created", "nodes_matched", "relationships_created", "relationships_matched"]:
                                    stats[key] += stats_update[key]

                    except Exception as e:
                        batch = futures[future]
                        first_chunk_idx = batch[0].chunk_index if batch else "unknown"
                        logger.error(f"Batch starting at chunk {first_chunk_idx} failed with error: {e}")
                        with stats_lock:
                            stats["chunks_failed"] += len(batch)

        # Create SourceDocument
        if not dry_run:
            with driver.session(database=config.NEO4J_DATABASE) as session:
                # SourceDocument is created per-chunk now with SOURCED_FROM edges
                # No bulk linking needed - all done in process_single_chunk
                pass

        # Report metrics
        logger.info("\n=== EXTRACTION COMPLETE ===")
        logger.info(f"Chunks: {stats['chunks_processed']} processed, {stats['chunks_failed']} failed")
        logger.info(f"Nodes created: {dict(stats['nodes_created'])}")
        logger.info(f"Nodes matched: {dict(stats['nodes_matched'])}")
        logger.info(f"Relationships created: {dict(stats['relationships_created'])}")
        logger.info(f"Relationships matched: {dict(stats['relationships_matched'])}")
        logger.info(f"Validation errors: {stats['validation_errors']}")
        logger.info(f"API usage: {stats['total_input_tokens']} input + {stats['total_output_tokens']} output tokens")

        # Cost estimate (Sonnet 4.5: $3/MTok input, $15/MTok output)
        cost = (stats['total_input_tokens'] * 3 + stats['total_output_tokens'] * 15) / 1_000_000
        logger.info(f"Estimated cost: ${cost:.2f}")

        return 0

    finally:
        driver.close()


def main():
    """Extract structured knowledge from PDF to quarry."""
    parser = argparse.ArgumentParser(description="Extract knowledge from PDF to quarry")
    parser.add_argument("--source", required=True, choices=list(config.SOURCE_CATALOG.keys()),
                       help="Source document key from config")
    parser.add_argument("--dry-run", action="store_true", help="Show extraction without writing to Neo4j")
    parser.add_argument("--limit", type=int, help="Limit number of chunks to process")
    parser.add_argument("--workers", type=int, default=1,
                       help="Number of parallel workers (1-5, default 1)")
    parser.add_argument("--resume", action="store_true",
                       help="Resume from previous extraction, skipping already-processed chunks")
    parser.add_argument("--batch-size", type=int, default=1,
                       help="Number of chunks per API call (default 1, recommended 3 for large docs)")
    args = parser.parse_args()

    return run_extraction(args.source, dry_run=args.dry_run, limit=args.limit, workers=args.workers,
                         resume=args.resume, batch_size=args.batch_size)


if __name__ == "__main__":
    sys.exit(main())
