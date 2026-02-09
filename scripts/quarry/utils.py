"""Shared utilities for quarry toolkit."""

import json
import logging
import re
from typing import Any

from anthropic import Anthropic
from neo4j import GraphDatabase

from . import config


def get_neo4j_driver():
    """Get configured Neo4j driver."""
    return GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
    )


def get_anthropic_client():
    """Get configured Anthropic client."""
    if not config.ANTHROPIC_API_KEY:
        raise ValueError(
            "ANTHROPIC_API_KEY environment variable not set. "
            "Get your key from https://console.anthropic.com"
        )
    return Anthropic(api_key=config.ANTHROPIC_API_KEY)


def parse_llm_json(text: str) -> dict:
    """Parse JSON from LLM output, stripping markdown fences if present.

    Args:
        text: Raw LLM output text

    Returns:
        Parsed JSON as dict

    Raises:
        json.JSONDecodeError: If parsing fails
    """
    # Strip markdown fences if present
    text = text.strip()
    if text.startswith("```"):
        # Remove opening fence (```json or just ```)
        text = re.sub(r"^```(?:json)?", "", text)
        # Remove closing fence
        text = re.sub(r"```$", "", text)
        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logging.error(f"JSON parse error: {e}")
        logging.error(f"Raw text: {text[:500]}...")
        raise


def setup_logging(name: str) -> logging.Logger:
    """Setup consistent logging format.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger
    """
    logging.basicConfig(
        format=config.LOG_FORMAT,
        level=getattr(logging, config.LOG_LEVEL.upper())
    )
    return logging.getLogger(name)


def validate_extraction(data: dict, catalog_id: str = "") -> tuple[bool, list[str], dict]:
    """Validate extracted JSON against schema constraints with three-tier vocabulary validation.

    Three-tier validation (ADR-010):
    1. Core term (in FACT_CATEGORIES etc.) → accept silently
    2. Provisional term (in VOCABULARY_EXTENSIONS) → accept, INFO log, increment count
    3. Rejected term (in VOCABULARY_REJECTIONS) → apply correction, WARN log
    4. Unknown term → accept, WARN log, auto-add to provisional

    Args:
        data: Extraction output with 'nodes' and 'relationships' keys
        catalog_id: Source document catalog_id for provisional tracking

    Returns:
        (is_valid, warnings, corrections)

        corrections dict has structure:
        {
            "remapped_values": [{"node_id": ..., "field": ..., "old": ..., "new": ...}],
            "reclassified_nodes": [{"node_id": ..., "old_type": ..., "new_type": ...}]
        }
    """
    import datetime

    logger = logging.getLogger(__name__)
    errors = []
    corrections = {"remapped_values": [], "reclassified_nodes": []}

    # Check structure
    if "nodes" not in data:
        errors.append("Missing 'nodes' key")
    if "relationships" not in data:
        errors.append("Missing 'relationships' key")
    if errors:
        return False, errors, corrections

    # Helper to validate vocabulary term
    def validate_vocab_term(field: str, term: str, node_id: str, node_idx: int) -> str:
        """Validate a vocabulary term and return corrected value (or original if valid)."""
        # Get core vocabulary for this field
        core_vocab = {
            "fact_category": config.FACT_CATEGORIES,
            "dimension": config.DIMENSIONS,
            "value_type": config.VALUE_TYPES,
            "assertion_type": config.ASSERTION_TYPES,
            "latitude": config.LATITUDES,
        }.get(field)

        if not core_vocab:
            return term  # Not a controlled field

        # Tier 1: Core vocabulary - accept silently
        if term in core_vocab:
            return term

        # Tier 2: Rejected terms - apply correction
        if term in config.VOCABULARY_REJECTIONS.get(field, {}):
            rejection = config.VOCABULARY_REJECTIONS[field][term]
            if rejection["action"] == "remap":
                target = rejection.get("target", "")
                logger.warning(f"Node {node_idx} ({node_id}): Rejected {field} '{term}' → remapping to '{target}' ({rejection['reason']})")
                corrections["remapped_values"].append({
                    "node_id": node_id,
                    "field": field,
                    "old": term,
                    "new": target
                })
                return target
            elif rejection["action"] == "reclassify":
                target_type = rejection.get("target_type", "")
                logger.warning(f"Node {node_idx} ({node_id}): Rejected {field} '{term}' → reclassifying to {target_type} ({rejection['reason']})")
                corrections["reclassified_nodes"].append({
                    "node_id": node_id,
                    "old_type": data["nodes"][node_idx]["type"],
                    "new_type": target_type
                })
                errors.append(f"Node {node_idx}: {field} '{term}' triggers reclassification to {target_type}")
                return term  # Keep original, but flag for reclassification

        # Tier 3: Provisional terms - accept with INFO log
        if term in config.VOCABULARY_EXTENSIONS.get(field, {}):
            config.VOCABULARY_EXTENSIONS[field][term]["count"] += 1
            logger.info(f"Provisional vocabulary term '{term}' for {field} (count: {config.VOCABULARY_EXTENSIONS[field][term]['count']})")
            return term

        # Tier 4: Unknown terms - accept, WARN, auto-add to provisional
        logger.warning(f"Node {node_idx} ({node_id}): New vocabulary term '{term}' for {field} — adding to provisional")
        config.VOCABULARY_EXTENSIONS[field][term] = {
            "first_seen": catalog_id or "unknown",
            "date": datetime.date.today().isoformat(),
            "count": 1,
            "notes": "Auto-added during extraction"
        }
        return term

    # Validate nodes
    for i, node in enumerate(data["nodes"]):
        # Check type
        if "type" not in node:
            errors.append(f"Node {i}: missing 'type'")
            continue
        if node["type"] not in config.ALLOWED_NODE_TYPES:
            errors.append(f"Node {i}: invalid type '{node['type']}'")

        # Check ID
        node_id = node.get("id", "")
        if not node_id:
            errors.append(f"Node {i}: missing or empty 'id'")
        elif not re.match(r"^[a-z0-9_]+$", node_id):
            errors.append(f"Node {i}: id '{node_id}' not snake_case")

        # Check properties if present
        props = node.get("properties", {})

        # Validate controlled vocabularies with three-tier system
        for field in ["fact_category", "dimension", "value_type", "assertion_type", "latitude"]:
            if field in props:
                original = props[field]
                corrected = validate_vocab_term(field, original, node_id, i)
                if corrected != original:
                    # Update in-place for remapped values
                    props[field] = corrected

        # Validate fractions
        if "value_number" in props and props.get("value_type") == "fraction":
            val = props["value_number"]
            if not isinstance(val, (int, float)) or val < 0 or val > 1:
                errors.append(f"Node {i}: value_number {val} not in [0, 1] for fraction type")

    # Validate relationships
    for i, rel in enumerate(data["relationships"]):
        if "type" not in rel:
            errors.append(f"Relationship {i}: missing 'type'")
            continue
        if rel["type"] not in config.ALLOWED_RELATIONSHIP_TYPES:
            errors.append(f"Relationship {i}: invalid type '{rel['type']}'")
        if "source" not in rel or not rel["source"]:
            errors.append(f"Relationship {i}: missing or empty 'source'")
        if "target" not in rel or not rel["target"]:
            errors.append(f"Relationship {i}: missing or empty 'target'")

    return len(errors) == 0, errors, corrections
