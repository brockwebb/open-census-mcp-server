"""Harvest Layer 2: Run pattern-matching queries to generate candidate ContextItems."""

import json
import sys
from datetime import datetime
from pathlib import Path

from .utils import get_neo4j_driver, setup_logging

logger = setup_logging(__name__)


def run_query(session, name, query):
    """Run a harvest query and return results."""
    logger.info(f"Running: {name}")
    try:
        result = session.run(query)
        records = [dict(r) for r in result]
        logger.info(f"  → {len(records)} results")
        return records
    except Exception as e:
        logger.error(f"Query failed: {e}")
        return []


def run_harvest():
    """Run all harvest queries and save results."""
    driver = get_neo4j_driver()
    all_results = {}

    try:
        with driver.session(database="quarry") as session:
            # §6.1a Numeric Threshold Violations
            all_results["numeric_threshold_violations"] = run_query(session,
                "§6.1a Numeric Threshold Violations",
                """
                MATCH (task:AnalysisTask)-[req:REQUIRES]->(qa_std:QualityAttribute)
                WHERE req.rule_type = "numeric_threshold"
                MATCH (mc:MethodologicalChoice)-[ap:APPLIES_TO]->(dp:DataProduct)
                WHERE ap.valid_until IS NULL OR date(ap.valid_until) >= date()
                MATCH (mc)-[:PRODUCES]->(qa_obs:QualityAttribute)
                WHERE qa_obs.dimension = qa_std.dimension
                  AND qa_obs.value_type = qa_std.value_type
                  AND qa_obs.value_number IS NOT NULL
                  AND qa_obs.value_number >= req.threshold_number
                WITH task, dp, req, qa_obs, collect(DISTINCT mc.id) AS source_facts
                RETURN {
                  task: task.name,
                  product: dp.name,
                  warning: replace(req.violation_template, "{value}", toString(qa_obs.value_number)),
                  recommendation: req.recommended_action,
                  severity: req.violation_severity,
                  source_facts: source_facts,
                  confidence: "high"
                } AS result
                """
            )

            # §6.1b Categorical Mismatch Violations
            all_results["categorical_mismatches"] = run_query(session,
                "§6.1b Categorical Mismatch Violations",
                """
                MATCH (task:AnalysisTask)-[req:REQUIRES]->(qa_std:QualityAttribute)
                WHERE req.rule_type = "categorical_match"
                MATCH (concept:CanonicalConcept)
                MATCH (op1:ConceptDefinition)-[:OPERATIONALIZES]->(concept)
                MATCH (op1)-[:DEFINED_FOR]->(dp1:DataProduct)
                MATCH (op2:ConceptDefinition)-[:OPERATIONALIZES]->(concept)
                MATCH (op2)-[:DEFINED_FOR]->(dp2:DataProduct)
                WHERE dp1 <> dp2
                  AND qa_std.dimension = "definitional_alignment"
                  AND op1.reference_period <> op2.reference_period
                WITH task, concept, dp1, dp2, op1, op2, req
                RETURN {
                  task: task.name,
                  concept: concept.name,
                  products: [dp1.name, dp2.name],
                  warning: replace(replace(replace(replace(req.violation_template,
                    "{survey1}", op1.survey), "{period1}", op1.reference_period),
                    "{survey2}", op2.survey), "{period2}", op2.reference_period),
                  recommendation: req.recommended_action,
                  severity: req.violation_severity,
                  confidence: "high"
                } AS result
                """
            )

            # §6.2 Temporal Comparability (SUPERSEDES chains)
            all_results["temporal_breaks"] = run_query(session,
                "§6.2 Temporal Comparability Breaks",
                """
                MATCH (te:TemporalEvent)-[:SUPERSEDES]->(mc:MethodologicalChoice)
                MATCH (mc)-[:PRODUCES]->(qa:QualityAttribute)
                WHERE qa.dimension IN ["temporal_comparability", "comparability", "definitional_alignment"]
                RETURN {
                  event: te.id,
                  date: coalesce(te.date, te.year),
                  superseded_choice: mc.id,
                  quality_impact: qa.dimension,
                  warning: "Methodology changed: " + mc.id + ". Temporal comparisons across this break require adjustment.",
                  confidence: "high"
                } AS result
                """
            )

            # §6.4 Unanticipated Interactions
            all_results["unanticipated_interactions"] = run_query(session,
                "§6.4 Unanticipated Interactions",
                """
                MATCH (mc1:MethodologicalChoice)-[:PRODUCES]->(qa:QualityAttribute)<-[:PRODUCES]-(mc2:MethodologicalChoice)
                WHERE mc1.id < mc2.id
                  AND NOT EXISTS { MATCH (mc1)-[:CONFOUNDS]-(mc2) }
                RETURN {
                  type: "potential_interaction",
                  choices: [mc1.id, mc2.id],
                  shared_attribute: qa.name,
                  dimension: qa.dimension,
                  confidence: "medium",
                  action: "Expert review: two methodological choices affect the same quality attribute"
                } AS result
                """
            )

            # §6.5 Coverage Report
            all_results["coverage"] = run_query(session,
                "§6.5 Extraction Coverage",
                """
                MATCH (d:SourceDocument)
                OPTIONAL MATCH (n)-[:SOURCED_FROM]->(d)
                RETURN {
                  document: d.catalog_id,
                  title: d.title,
                  nodes_extracted: count(DISTINCT n)
                } AS result
                ORDER BY result.document
                """
            )

            # §6.6 Unconnected Facts
            all_results["unconnected_facts"] = run_query(session,
                "§6.6 Unconnected Facts (Extraction Gaps)",
                """
                MATCH (mc:MethodologicalChoice)
                WHERE NOT (mc)-[:PRODUCES]->(:QualityAttribute)
                OPTIONAL MATCH (mc)-[src:SOURCED_FROM]->(doc:SourceDocument)
                RETURN {
                  fact_category: mc.fact_category,
                  source_document: doc.catalog_id,
                  source_page: src.source_page,
                  choice_id: mc.id
                } AS result
                ORDER BY result.fact_category, result.source_page
                LIMIT 50
                """
            )

            # Dimension Coverage Summary
            all_results["dimension_coverage"] = run_query(session,
                "Dimension Coverage Summary",
                """
                MATCH (qa:QualityAttribute)
                WHERE qa.dimension IS NOT NULL
                RETURN qa.dimension AS dimension, count(qa) AS count
                ORDER BY count DESC
                """
            )

            # Relationship Type Inventory
            all_results["relationship_inventory"] = run_query(session,
                "Relationship Type Inventory",
                """
                MATCH ()-[r]->()
                RETURN type(r) AS rel_type, count(r) AS count
                ORDER BY count DESC
                """
            )

            # MENTIONS check (should be 0)
            mentions_count = session.run(
                "MATCH ()-[r:MENTIONS]->() RETURN count(r) AS count"
            ).single()["count"]

            all_results["mentions_check"] = {
                "count": mentions_count,
                "status": "PASS" if mentions_count == 0 else "FAIL"
            }

    finally:
        driver.close()

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path("tmp") / f"harvest_results_{timestamp}.json"
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(all_results, f, indent=2)

    logger.info(f"Results saved to: {output_path}")

    # Print summary
    print("\n" + "="*60)
    print("HARVEST SUMMARY")
    print("="*60)

    for key, results in all_results.items():
        if key == "mentions_check":
            print(f"\n{key}: {results['status']} ({results['count']} MENTIONS relationships)")
        elif isinstance(results, list):
            print(f"\n{key}: {len(results)} results")
            if results and len(results) <= 5:
                for r in results:
                    print(f"  - {r}")
        else:
            print(f"\n{key}: {results}")

    print(f"\nFull results: {output_path}")

    # Check for failures
    if all_results["mentions_check"]["status"] == "FAIL":
        logger.warning("MENTIONS relationships found! Extraction prompt needs fixing.")
        return 1

    return 0


def main():
    """Run harvest queries."""
    return run_harvest()


if __name__ == "__main__":
    sys.exit(main())
