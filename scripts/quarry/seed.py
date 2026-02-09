"""Seed Layer 0 (AnalysisTask + REQUIRES + reference nodes) in quarry database.

Layer 0 data is hardcoded from docs/design/raw_kg_schema.md v3.1.
capture_layer_0() is retained as a diagnostic function but NOT used for seeding.
"""

import argparse
import sys

from .utils import get_neo4j_driver, setup_logging

logger = setup_logging(__name__)


# ============================================================================
# LAYER 0 SEED DATA (from raw_kg_schema.md v3.1)
# ============================================================================

CANONICAL_CONCEPTS = [
    {"name": "Household Income"},
    {"name": "Family Income"},
    {"name": "Personal Income"},
    {"name": "Earnings"},
    {"name": "Money Income"},
    {"name": "Employment"},
]

DATA_PRODUCTS = [
    {"name": "CPS ASEC"},
    {"name": "CPS Basic Monthly"},
    {"name": "ACS 1-Year"},
    {"name": "ACS 5-Year"},
]

SURVEY_PROCESSES = [
    {"name": "Sampling"},
    {"name": "Collection"},
    {"name": "Weighting"},
    {"name": "Estimation"},
    {"name": "Processing"},
    {"name": "Dissemination"},
]

ANALYSIS_TASKS = [
    {
        "name": "EstimateChangeOverTime",
        "description": "Compare estimates across time periods",
        "typical_use_cases": [
            "Year-over-year income change",
            "Pre/post recession comparisons",
            "Long-term trend analysis"
        ],
        "critical_quality_dimensions": [
            "temporal_comparability",
            "overlap_structure",
            "seasonal_adjustment_status"
        ]
    },
    {
        "name": "CrossSurveyComparison",
        "description": "Compare estimates across surveys (CPS vs ACS)",
        "typical_use_cases": [
            "CPS ASEC vs ACS 1-Year income levels",
            "Cross-survey employment validation",
            "Data product selection for research"
        ],
        "critical_quality_dimensions": [
            "definitional_alignment",
            "universe_match",
            "reference_period_match"
        ]
    },
    {
        "name": "SmallAreaEstimation",
        "description": "Estimate for sub-state geographies",
        "typical_use_cases": [
            "County-level poverty estimates",
            "School district income profiles",
            "Municipal planning data"
        ],
        "critical_quality_dimensions": [
            "effective_sample_size",
            "direct_estimate_reliability"
        ]
    },
    {
        "name": "SubgroupAnalysis",
        "description": "Estimate for demographic subpopulations",
        "typical_use_cases": [
            "Race/ethnicity earnings gaps",
            "Age cohort employment rates",
            "Educational attainment by region"
        ],
        "critical_quality_dimensions": [
            "subgroup_sample_size",
            "design_effect"
        ]
    },
    {
        "name": "IncomeDistributionAnalysis",
        "description": "Analyze income distribution shape",
        "typical_use_cases": [
            "Gini coefficient calculation",
            "Top 1% income share estimation",
            "Poverty threshold analysis"
        ],
        "critical_quality_dimensions": [
            "topcoding_effects",
            "imputation_method",
            "component_coverage"
        ]
    }
]

# REQUIRES edges: AnalysisTask → QualityAttribute with typed rules
# Format: (task_name, qa_name, qa_dimension, qa_value_type, edge_properties)
REQUIRES_EDGES = [
    # EstimateChangeOverTime requires low data overlap
    (
        "EstimateChangeOverTime",
        "overlap_fraction",
        "temporal_comparability",
        "fraction",
        {
            "rule_type": "numeric_threshold",
            "threshold_number": 0.2,
            "threshold_string": None,
            "condition": "data_overlap_between_consecutive_periods",
            "violation_severity": "critical",
            "violation_template": "Consecutive estimates share {value} of underlying data. Standard change estimates are unreliable.",
            "recommended_action": "Use non-overlapping periods or apply published variance correction factors."
        }
    ),
    # CrossSurveyComparison requires matching reference periods
    (
        "CrossSurveyComparison",
        "reference_period_alignment",
        "definitional_alignment",
        "categorical",
        {
            "rule_type": "categorical_match",
            "threshold_number": None,
            "threshold_string": "matching",
            "condition": "reference_periods_must_align",
            "violation_severity": "high",
            "violation_template": "Reference periods differ: {survey1} uses {period1} while {survey2} uses {period2}. Direct comparison produces systematic bias.",
            "recommended_action": "Restrict to overlapping reference windows or apply published reconciliation factors."
        }
    ),
    # CrossSurveyComparison requires matching universes
    (
        "CrossSurveyComparison",
        "universe_alignment",
        "coverage",
        "categorical",
        {
            "rule_type": "categorical_match",
            "threshold_number": None,
            "threshold_string": "matching",
            "condition": "target_populations_must_align",
            "violation_severity": "critical",
            "violation_template": "{survey1} targets {universe1} while {survey2} targets {universe2}. Aggregates are not comparable without universe restriction.",
            "recommended_action": "Restrict both surveys to overlapping population (e.g., civilian noninstitutional 16+)."
        }
    ),
    # SmallAreaEstimation requires sufficient sample size
    (
        "SmallAreaEstimation",
        "effective_sample_size",
        "precision",
        "count",
        {
            "rule_type": "numeric_threshold",
            "threshold_number": 100,
            "threshold_string": None,
            "condition": "minimum_effective_sample_size_for_area",
            "violation_severity": "critical",
            "violation_template": "Effective sample size of {value} is below reliability threshold. Direct estimates have unacceptable CVs.",
            "recommended_action": "Use model-based small area estimates (e.g., SAIPE) or aggregate to larger geography."
        }
    ),
    # SubgroupAnalysis requires sufficient subgroup sample
    (
        "SubgroupAnalysis",
        "subgroup_sample_size",
        "precision",
        "count",
        {
            "rule_type": "numeric_threshold",
            "threshold_number": 200,
            "threshold_string": None,
            "condition": "minimum_sample_size_for_subgroup",
            "violation_severity": "high",
            "violation_template": "Subgroup sample size of {value} produces unreliable estimates. Published CVs likely exceed thresholds.",
            "recommended_action": "Collapse categories, pool years, or suppress estimate per data product guidelines."
        }
    ),
]


def capture_layer_0(driver):
    """Diagnostic function to inspect existing Layer 0 data in quarry.

    This function is NOT used for seeding. It's retained for debugging and verification.

    Returns:
        Dict with counts of existing Layer 0 nodes and edges
    """
    logger.info("Capturing existing Layer 0 data from quarry (diagnostic only)...")

    with driver.session(database="quarry") as session:
        # Get counts
        tasks = session.run("MATCH (t:AnalysisTask) RETURN count(t) AS count").single()["count"]
        qa_nodes = session.run("MATCH (qa:QualityAttribute) RETURN count(qa) AS count").single()["count"]
        requires = session.run("MATCH ()-[r:REQUIRES]->() RETURN count(r) AS count").single()["count"]
        concepts = session.run("MATCH (c:CanonicalConcept) RETURN count(c) AS count").single()["count"]
        products = session.run("MATCH (dp:DataProduct) RETURN count(dp) AS count").single()["count"]
        processes = session.run("MATCH (sp:SurveyProcess) RETURN count(sp) AS count").single()["count"]

    logger.info(f"Existing Layer 0: {tasks} AnalysisTasks, {qa_nodes} QualityAttributes, "
                f"{requires} REQUIRES edges, {concepts} CanonicalConcepts, "
                f"{products} DataProducts, {processes} SurveyProcesses")

    return {
        "tasks": tasks,
        "quality_attributes": qa_nodes,
        "requires_edges": requires,
        "concepts": concepts,
        "products": products,
        "processes": processes
    }


def seed_layer_0(driver, dry_run=False):
    """Seed Layer 0 nodes and relationships from hardcoded data.

    Args:
        driver: Neo4j driver
        dry_run: If True, print Cypher without executing

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    statements = []

    # === CONSTRAINTS ===
    statements.extend([
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:AnalysisTask) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:CanonicalConcept) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:DataProduct) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:SurveyProcess) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:SourceDocument) REQUIRE n.catalog_id IS UNIQUE",
    ])

    # === INDEXES ===
    statements.extend([
        "CREATE INDEX IF NOT EXISTS FOR (n:MethodologicalChoice) ON (n.fact_category)",
        "CREATE INDEX IF NOT EXISTS FOR (n:MethodologicalChoice) ON (n.survey)",
        "CREATE INDEX IF NOT EXISTS FOR (n:QualityAttribute) ON (n.dimension)",
        "CREATE INDEX IF NOT EXISTS FOR (n:QualityAttribute) ON (n.name)",
        "CREATE INDEX IF NOT EXISTS FOR (n:ConceptDefinition) ON (n.survey)",
        "CREATE INDEX IF NOT EXISTS FOR (n:Threshold) ON (n.measure)",
        "CREATE INDEX IF NOT EXISTS FOR (n:QualityCaveat) ON (n.tse_type)",
        "CREATE INDEX IF NOT EXISTS FOR (n:ContextItem) ON (n.validation_status)",
    ])

    # === CANONICAL CONCEPTS ===
    for concept in CANONICAL_CONCEPTS:
        stmt = f'MERGE (c:CanonicalConcept {{name: "{concept["name"]}"}})'
        statements.append(stmt)

    # === DATA PRODUCTS ===
    for product in DATA_PRODUCTS:
        stmt = f'MERGE (dp:DataProduct {{name: "{product["name"]}"}})'
        statements.append(stmt)

    # === SURVEY PROCESSES ===
    for process in SURVEY_PROCESSES:
        stmt = f'MERGE (sp:SurveyProcess {{name: "{process["name"]}"}})'
        statements.append(stmt)

    # === ANALYSIS TASKS ===
    for task in ANALYSIS_TASKS:
        # Build Cypher list syntax properly (using double quotes for strings inside lists)
        desc = task['description']
        use_cases_cypher = '[' + ', '.join(f'"{uc}"' for uc in task['typical_use_cases']) + ']'
        dims_cypher = '[' + ', '.join(f'"{d}"' for d in task['critical_quality_dimensions']) + ']'

        stmt = f"""MERGE (t:AnalysisTask {{name: "{task['name']}"}})
ON CREATE SET t.description = "{desc}",
              t.typical_use_cases = {use_cases_cypher},
              t.critical_quality_dimensions = {dims_cypher}"""
        statements.append(stmt)

    # === QUALITY ATTRIBUTES (for REQUIRES targets) ===
    # Extract unique QA nodes from REQUIRES_EDGES with value_type
    qa_nodes = {}
    for task_name, qa_name, qa_dimension, qa_value_type, props in REQUIRES_EDGES:
        qa_nodes[(qa_name, qa_dimension)] = qa_value_type

    for (qa_name, qa_dimension), qa_value_type in qa_nodes.items():
        stmt = f'MERGE (qa:QualityAttribute {{name: "{qa_name}", dimension: "{qa_dimension}"}})\nON CREATE SET qa.value_type = "{qa_value_type}"'
        statements.append(stmt)

    # === REQUIRES EDGES ===
    for task_name, qa_name, qa_dimension, qa_value_type, props in REQUIRES_EDGES:
        # Build property assignments
        prop_lines = []
        for k, v in props.items():
            if v is None:
                prop_lines.append(f"r.{k} = null")
            elif isinstance(v, str):
                # Escape double quotes in string values
                escaped_v = v.replace('"', '\\"')
                prop_lines.append(f'r.{k} = "{escaped_v}"')
            elif isinstance(v, (int, float)):
                prop_lines.append(f"r.{k} = {v}")
        props_str = ",\n    ".join(prop_lines)

        stmt = f"""MATCH (t:AnalysisTask {{name: "{task_name}"}})
MATCH (qa:QualityAttribute {{name: "{qa_name}", dimension: "{qa_dimension}"}})
MERGE (t)-[r:REQUIRES]->(qa)
ON CREATE SET {props_str}"""
        statements.append(stmt)

    # Execute or print
    if dry_run:
        print("\n=== DRY RUN: Cypher statements ===\n")
        for i, stmt in enumerate(statements, 1):
            print(f"-- Statement {i}")
            print(stmt)
            print(";\n")
        logger.info(f"Dry run complete: {len(statements)} statements generated")
        return 0

    # Execute statements
    created = {"constraints": 0, "indexes": 0, "nodes": 0, "relationships": 0}
    matched = {"nodes": 0, "relationships": 0}

    with driver.session(database="quarry") as session:
        for i, stmt in enumerate(statements):
            try:
                result = session.run(stmt)
                summary = result.consume()
                created["nodes"] += summary.counters.nodes_created
                created["relationships"] += summary.counters.relationships_created
                created["indexes"] += summary.counters.indexes_added
                created["constraints"] += summary.counters.constraints_added

                # MERGE matches existing
                if summary.counters.nodes_created == 0 and "MERGE" in stmt and "AnalysisTask" in stmt:
                    matched["nodes"] += 1
                if summary.counters.relationships_created == 0 and "MERGE" in stmt and "REQUIRES" in stmt:
                    matched["relationships"] += 1

                logger.debug(f"[{i+1}/{len(statements)}] OK")
            except Exception as e:
                logger.error(f"Statement {i+1} failed: {e}")
                logger.error(f"Statement: {stmt[:200]}...")
                return 1

    # Report
    logger.info("Seed complete:")
    logger.info(f"  Created: {created['nodes']} nodes, {created['relationships']} relationships, "
                f"{created['constraints']} constraints, {created['indexes']} indexes")
    logger.info(f"  Matched: {matched['nodes']} nodes, {matched['relationships']} relationships")

    # Verify with diagnostic capture
    capture_layer_0(driver)

    return 0


def main():
    """Seed Layer 0 in quarry database."""
    parser = argparse.ArgumentParser(description="Seed Layer 0 in quarry database")
    parser.add_argument("--dry-run", action="store_true", help="Print Cypher without executing")
    parser.add_argument("--diagnose", action="store_true", help="Run capture_layer_0() diagnostic only")
    args = parser.parse_args()

    driver = get_neo4j_driver()
    try:
        if args.diagnose:
            capture_layer_0(driver)
            return 0
        return seed_layer_0(driver, dry_run=args.dry_run)
    finally:
        driver.close()


if __name__ == "__main__":
    sys.exit(main())
