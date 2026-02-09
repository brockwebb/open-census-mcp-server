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


def validate_extraction(data: dict) -> tuple[bool, list[str]]:
    """Validate extracted JSON against schema constraints.

    Args:
        data: Extraction output with 'nodes' and 'relationships' keys

    Returns:
        (is_valid, error_messages)
    """
    errors = []

    # Check structure
    if "nodes" not in data:
        errors.append("Missing 'nodes' key")
    if "relationships" not in data:
        errors.append("Missing 'relationships' key")
    if errors:
        return False, errors

    # Validate nodes
    for i, node in enumerate(data["nodes"]):
        # Check type
        if "type" not in node:
            errors.append(f"Node {i}: missing 'type'")
            continue
        if node["type"] not in config.ALLOWED_NODE_TYPES:
            errors.append(f"Node {i}: invalid type '{node['type']}'")

        # Check ID
        if "id" not in node or not node["id"]:
            errors.append(f"Node {i}: missing or empty 'id'")
        elif not re.match(r"^[a-z0-9_]+$", node["id"]):
            errors.append(f"Node {i}: id '{node['id']}' not snake_case")

        # Check properties if present
        props = node.get("properties", {})

        # Validate controlled vocabularies
        if "fact_category" in props and props["fact_category"] not in config.FACT_CATEGORIES:
            errors.append(f"Node {i}: invalid fact_category '{props['fact_category']}'")
        if "dimension" in props and props["dimension"] not in config.DIMENSIONS:
            errors.append(f"Node {i}: invalid dimension '{props['dimension']}'")
        if "value_type" in props and props["value_type"] not in config.VALUE_TYPES:
            errors.append(f"Node {i}: invalid value_type '{props['value_type']}'")
        if "assertion_type" in props and props["assertion_type"] not in config.ASSERTION_TYPES:
            errors.append(f"Node {i}: invalid assertion_type '{props['assertion_type']}'")
        if "latitude" in props and props["latitude"] not in config.LATITUDES:
            errors.append(f"Node {i}: invalid latitude '{props['latitude']}'")

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

    return len(errors) == 0, errors
