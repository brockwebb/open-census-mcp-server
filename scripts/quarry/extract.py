"""Main extraction pipeline: PDF → chunks → LLM → Neo4j quarry."""

import argparse
import json
import sys
from collections import Counter
from datetime import datetime

from . import config
from .chunk import chunk_pdf
from .prompts import build_extraction_prompt
from .utils import get_anthropic_client, get_neo4j_driver, parse_llm_json, setup_logging, validate_extraction

logger = setup_logging(__name__)


def get_existing_entities(driver):
    """Query quarry for existing Layer 0 entity names for MERGE targets.

    Returns:
        Dict of entity type -> list of names
    """
    entities = {}

    with driver.session(database=config.NEO4J_DATABASE) as session:
        # DataProducts
        result = session.run("MATCH (n:DataProduct) RETURN n.name AS name ORDER BY name")
        entities["DataProduct"] = [r["name"] for r in result]

        # CanonicalConcepts
        result = session.run("MATCH (n:CanonicalConcept) RETURN n.name AS name ORDER BY name")
        entities["CanonicalConcept"] = [r["name"] for r in result]

        # SurveyProcesses
        result = session.run("MATCH (n:SurveyProcess) RETURN n.name AS name ORDER BY name")
        entities["SurveyProcess"] = [r["name"] for r in result]

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

    # Validate
    is_valid, errors = validate_extraction(data)
    if not is_valid:
        logger.warning(f"Validation failed for chunk {chunk.chunk_index}: {errors[:3]}")

    return {
        "data": data,
        "valid": is_valid,
        "errors": errors if not is_valid else [],
        "tokens": tokens_used
    }


def run_extraction(source_key, dry_run=False, limit=None):
    """Run full extraction pipeline.

    Args:
        source_key: Key in SOURCE_CATALOG
        dry_run: If True, show extraction output without writing to Neo4j
        limit: Limit number of chunks to process

    Returns:
        Exit code (0 = success)
    """
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
    client = get_anthropic_client()
    driver = get_neo4j_driver()

    try:
        # Get existing entities
        existing_entities = get_existing_entities(driver)

        # Chunk PDF
        chunks = chunk_pdf(str(pdf_path), source_doc["catalog_id"])
        if limit:
            chunks = chunks[:limit]
            logger.info(f"Limited to first {limit} chunks")

        # Metrics
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

        # Process chunks
        with driver.session(database=config.NEO4J_DATABASE) as session:
            for chunk in chunks:
                logger.info(f"Processing chunk {chunk.chunk_index + 1}/{len(chunks)}: "
                           f"{' > '.join(chunk.section_path[:2]) if chunk.section_path else '(root)'}")

                # Extract
                result = extract_chunk(client, chunk, source_doc, existing_entities, dry_run)

                if not result:
                    stats["chunks_failed"] += 1
                    continue

                if dry_run:
                    print(f"\n=== CHUNK {chunk.chunk_index} ===")
                    print(f"Prompt length: {len(result['prompt'])} chars")
                    if result["response"]:
                        print(f"Response:\n{result['response'][:500]}...")
                    continue

                stats["chunks_processed"] += 1
                stats["total_input_tokens"] += result["tokens"]["input"]
                stats["total_output_tokens"] += result["tokens"]["output"]

                if not result.get("valid"):
                    stats["validation_errors"] += 1

                data = result["data"]

                # Write nodes
                node_map = {}  # Map extraction IDs to Neo4j internal IDs
                for node in data.get("nodes", []):
                    write_result = write_node_to_neo4j(session, node, source_doc["catalog_id"])
                    node_map[node["id"]] = write_result["neo4j_id"]

                    if write_result["created"]:
                        stats["nodes_created"][write_result["type"]] += 1
                    else:
                        stats["nodes_matched"][write_result["type"]] += 1

                # Write relationships
                for rel in data.get("relationships", []):
                    write_result = write_relationship_to_neo4j(session, rel, node_map)
                    if write_result.get("created"):
                        stats["relationships_created"][write_result["type"]] += 1
                    else:
                        stats["relationships_matched"][write_result["type"]] += 1

        # Create SourceDocument
        if not dry_run:
            with driver.session(database=config.NEO4J_DATABASE) as session:
                session.run("""
                    MERGE (sd:SourceDocument {catalog_id: $catalog_id})
                    SET sd.title = $title, sd.year = $year,
                        sd.survey = $survey, sd.local_path = $local_path
                """, {
                    "catalog_id": source_doc["catalog_id"],
                    "title": source_doc["title"],
                    "year": source_doc["year"],
                    "survey": source_doc["survey"],
                    "local_path": source_doc["local_path"]
                })

                # Link extracted nodes to SourceDocument
                session.run("""
                    MATCH (sd:SourceDocument {catalog_id: $catalog_id})
                    MATCH (n)
                    WHERE NOT n:SourceDocument AND NOT n:AnalysisTask
                      AND NOT (n)-[:SOURCED_FROM]->()
                    MERGE (n)-[:SOURCED_FROM]->(sd)
                """, {"catalog_id": source_doc["catalog_id"]})

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
    args = parser.parse_args()

    return run_extraction(args.source, dry_run=args.dry_run, limit=args.limit)


if __name__ == "__main__":
    sys.exit(main())
