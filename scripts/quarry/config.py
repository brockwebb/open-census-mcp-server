"""Quarry toolkit configuration."""

import os
from pathlib import Path

# === Neo4j Configuration ===
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_DATABASE = "quarry"
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "i'llbeback")

# === Anthropic Configuration ===
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = "claude-sonnet-4-5-20250929"

# === Repository Root ===
REPO_ROOT = Path(__file__).parent.parent.parent

# === Source Document Catalog ===
SOURCE_CATALOG = {
    "cps_handbook": {
        "catalog_id": "cps_handbook_of_methods_2024",
        "title": "CPS Handbook of Methods",
        "year": 2024,
        "survey": "cps",
        "local_path": "knowledge-base/census_cps/cps_handbook_of_methods.pdf"
    },
    "acs_design_methodology": {
        "catalog_id": "acs_design_methodology_2024",
        "title": "ACS Design and Methodology Report 2024",
        "year": 2024,
        "survey": "acs",
        "local_path": "knowledge-base/source-docs/census-methodology/acs_design_methodology_report_2024.pdf"
    },
    "cps_tech_paper_77": {
        "catalog_id": "cps_tech_paper_77",
        "title": "CPS Technical Paper 77: Design and Methodology",
        "year": 2006,
        "survey": "cps",
        "local_path": "knowledge-base/census_cps/CPS-Tech-Paper-77.pdf"
    },
    "census_quality_standards": {
        "catalog_id": "census_quality_standards",
        "title": "Census Bureau Statistical Quality Standards",
        "year": 2024,
        "survey": "general",
        "local_path": "knowledge-base/source-docs/census-methodology/quality-standards.pdf"
    }
}

# === Controlled Vocabularies ===
FACT_CATEGORIES = [
    "design", "collection", "weighting", "estimation",
    "variance", "processing", "adjustment"
]

DIMENSIONS = [
    "temporal_comparability", "precision", "coverage", "definitional_alignment",
    "topcoding_effects", "seasonal_adjustment", "nonresponse_bias",
    "processing_error", "variance_estimation"
]

VALUE_TYPES = ["fraction", "count", "boolean", "categorical"]

ASSERTION_TYPES = ["fact", "definition", "procedure", "threshold", "caveat", "change"]

LATITUDES = ["none", "narrow", "wide", "full"]

# === Allowed Node Types (from schema v3.1) ===
ALLOWED_NODE_TYPES = [
    "MethodologicalChoice",
    "QualityAttribute",
    "DataProduct",
    "SurveyProcess",
    "UniverseDefinition",
    "ConceptDefinition",
    "Threshold",
    "TemporalEvent",
    "QualityCaveat",
    "SourceDocument",
    "AnalysisTask",
    "CanonicalConcept",
]

# === Allowed Relationship Types (from schema v3.1) ===
ALLOWED_RELATIONSHIP_TYPES = [
    "PART_OF",
    "IMPLEMENTS",
    "APPLIES_TO",
    "DEFINED_FOR",
    "OPERATIONALIZES",
    "TARGETS",
    "SOURCED_FROM",
    "PRODUCES",
    "REQUIRES",
    "TRADES_OFF_WITH",
    "MITIGATES",
    "QUALIFIES",
    "SUPERSEDES",
    "CONSTRAINS",
    "CONFOUNDS",
    "DERIVED_FROM",
]

# === Chunking Configuration ===
MAX_CHUNK_TOKENS = 2000

# === Logging Configuration ===
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
