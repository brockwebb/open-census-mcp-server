"""Seed Layer 0 (AnalysisTask + REQUIRES + reference nodes) in quarry database."""

import argparse
import sys

from .utils import get_neo4j_driver, setup_logging

logger = setup_logging(__name__)


def capture_layer_0(driver):
    """Capture existing Layer 0 data from quarry.

    Returns:
        Dict with AnalysisTasks, QualityAttributes, REQUIRES edges, and reference nodes
    """
    logger.info("Capturing existing Layer 0 data from quarry...")

    with driver.session(database="quarry") as session:
        # Get AnalysisTasks
        tasks = session.run("""
            MATCH (t:AnalysisTask)
            RETURN t.name AS name, properties(t) AS props
            ORDER BY name
        """).data()

        # Get REQUIRES edges
        requires = session.run("""
            MATCH (t:AnalysisTask)-[r:REQUIRES]->(qa:QualityAttribute)
            RETURN t.name AS task_name, qa.name AS qa_name, qa.dimension AS qa_dimension,
                   properties(r) AS rel_props
            ORDER BY task_name, qa_name
        """).data()

        # Get QualityAttributes linked to REQUIRES
        qa_nodes = session.run("""
            MATCH (t:AnalysisTask)-[:REQUIRES]->(qa:QualityAttribute)
            RETURN DISTINCT qa.name AS name, qa.dimension AS dimension, properties(qa) AS props
            ORDER BY dimension, name
        """).data()

        # Get CanonicalConcepts
        concepts = session.run("""
            MATCH (c:CanonicalConcept)
            RETURN c.name AS name, properties(c) AS props
            ORDER BY name
        """).data()

        # Get DataProducts
        products = session.run("""
            MATCH (dp:DataProduct)
            RETURN dp.name AS name, properties(dp) AS props
            ORDER BY name
        """).data()

        # Get SurveyProcesses
        processes = session.run("""
            MATCH (sp:SurveyProcess)
            RETURN sp.name AS name, properties(sp) AS props
            ORDER BY name
        """).data()

    logger.info(f"Captured: {len(tasks)} AnalysisTasks, {len(qa_nodes)} QualityAttributes, "
                f"{len(requires)} REQUIRES edges, {len(concepts)} CanonicalConcepts, "
                f"{len(products)} DataProducts, {len(processes)} SurveyProcesses")

    return {
        "tasks": tasks,
        "quality_attributes": qa_nodes,
        "requires_edges": requires,
        "concepts": concepts,
        "products": products,
        "processes": processes
    }


def seed_layer_0(driver, dry_run=False):
    """Seed Layer 0 nodes and relationships.

    Args:
        driver: Neo4j driver
        dry_run: If True, print Cypher without executing
    """
    # First capture existing data
    data = capture_layer_0(driver)

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
    for concept in data["concepts"]:
        props_str = ", ".join(f"{k}: ${k}" for k in concept["props"].keys() if k != "name")
        stmt = f"MERGE (c:CanonicalConcept {{name: '{concept['name']}'}}"
        if props_str:
            stmt += f"\nON CREATE SET c += {{{props_str}}}"
        statements.append(stmt)

    # === DATA PRODUCTS ===
    for product in data["products"]:
        props_str = ", ".join(f"{k}: ${k}" for k in product["props"].keys() if k != "name")
        stmt = f"MERGE (dp:DataProduct {{name: '{product['name']}'}}"
        if props_str:
            stmt += f"\nON CREATE SET dp += {{{props_str}}}"
        statements.append(stmt)

    # === SURVEY PROCESSES ===
    for process in data["processes"]:
        props_str = ", ".join(f"{k}: ${k}" for k in process["props"].keys() if k != "name")
        stmt = f"MERGE (sp:SurveyProcess {{name: '{process['name']}'}}"
        if props_str:
            stmt += f"\nON CREATE SET sp += {{{props_str}}}"
        statements.append(stmt)

    # === ANALYSIS TASKS ===
    for task in data["tasks"]:
        props = task["props"]
        stmt = f"""MERGE (t:AnalysisTask {{name: '{task['name']}'}})
ON CREATE SET t.description = '{props.get('description', '')}',
              t.typical_use_cases = {props.get('typical_use_cases', [])},
              t.critical_quality_dimensions = {props.get('critical_quality_dimensions', [])}"""
        statements.append(stmt)

    # === QUALITY ATTRIBUTES (for REQUIRES) ===
    for qa in data["quality_attributes"]:
        props = qa["props"]
        stmt = f"""MERGE (qa:QualityAttribute {{name: '{qa['name']}', dimension: '{qa['dimension']}'}})
ON CREATE SET qa.value_type = '{props.get('value_type', 'categorical')}'"""
        statements.append(stmt)

    # === REQUIRES EDGES ===
    for req in data["requires_edges"]:
        rel_props = req["rel_props"]
        props_str = ", ".join(f"r.{k} = {repr(v)}" for k, v in rel_props.items())
        stmt = f"""MATCH (t:AnalysisTask {{name: '{req['task_name']}'}})
MATCH (qa:QualityAttribute {{name: '{req['qa_name']}', dimension: '{req['qa_dimension']}'}})
MERGE (t)-[r:REQUIRES]->(qa)
SET {props_str}"""
        statements.append(stmt)

    # Execute or print
    if dry_run:
        print("\n=== DRY RUN: Cypher statements ===\n")
        for stmt in statements:
            print(stmt)
            print(";\n")
        return

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
                if summary.counters.nodes_created == 0 and "MERGE" in stmt:
                    matched["nodes"] += 1
                if summary.counters.relationships_created == 0 and "MERGE" in stmt and "]->" in stmt:
                    matched["relationships"] += 1

                logger.debug(f"[{i+1}/{len(statements)}] OK")
            except Exception as e:
                logger.error(f"Statement {i+1} failed: {e}")
                logger.error(f"Statement: {stmt[:100]}...")
                return 1

    # Report
    logger.info("Seed complete:")
    logger.info(f"  Created: {created['nodes']} nodes, {created['relationships']} relationships, "
                f"{created['constraints']} constraints, {created['indexes']} indexes")
    logger.info(f"  Matched: {matched['nodes']} nodes, {matched['relationships']} relationships")

    # Verify
    with driver.session(database="quarry") as session:
        counts = session.run("""
            MATCH (n)
            RETURN labels(n)[0] AS label, count(n) AS count
            ORDER BY label
        """).data()

        logger.info("Layer 0 inventory:")
        for row in counts:
            if row["label"] in ["AnalysisTask", "CanonicalConcept", "DataProduct", "SurveyProcess", "QualityAttribute"]:
                logger.info(f"  {row['label']}: {row['count']}")

        req_count = session.run("MATCH ()-[r:REQUIRES]->() RETURN count(r) AS count").single()["count"]
        logger.info(f"  REQUIRES edges: {req_count}")

    return 0


def main():
    """Seed Layer 0 in quarry database."""
    parser = argparse.ArgumentParser(description="Seed Layer 0 in quarry database")
    parser.add_argument("--dry-run", action="store_true", help="Print Cypher without executing")
    args = parser.parse_args()

    driver = get_neo4j_driver()
    try:
        return seed_layer_0(driver, dry_run=args.dry_run)
    finally:
        driver.close()


if __name__ == "__main__":
    sys.exit(main())
