"""Extraction prompt templates for quarry toolkit."""

from typing import Dict, List

from . import config


def build_extraction_prompt(
    chunk_text: str,
    section_path: List[str],
    source_doc: Dict[str, str],
    existing_entities: Dict[str, List[str]],
) -> str:
    """Build extraction prompt for a document chunk.

    Args:
        chunk_text: The text content to extract from
        section_path: Section hierarchy (e.g., ["Chapter 3", "3.2 Sample Design"])
        source_doc: Source document metadata from SOURCE_CATALOG
        existing_entities: Existing entity names to MERGE with
            {"DataProduct": ["CPS Basic Monthly", ...], "CanonicalConcept": [...], ...}

    Returns:
        Complete extraction prompt
    """
    section_context = " > ".join(section_path) if section_path else "(document root)"

    prompt = f"""You are extracting structured knowledge from a U.S. Census Bureau methodology document into a knowledge graph.

SOURCE DOCUMENT CONTEXT:
- Title: {source_doc['title']}
- Survey: {source_doc['survey']}
- Year: {source_doc['year']}
- Section: {section_context}

EXTRACTION TASK:
Extract facts about survey methodology, quality attributes, and statistical concepts from the text below. Return a JSON object with nodes and relationships conforming to the schema.

CRITICAL RULES:

1. **Extract FACTS and MEASUREMENTS only, not opinions or implications.**
   - BAD: "CPS uses complex sampling"
   - GOOD: "CPS uses a two-stage stratified cluster design with 824 primary sampling units"

2. **Use existing entity names when linking:**
   - DataProduct: {', '.join(existing_entities.get('DataProduct', []))}
   - CanonicalConcept: {', '.join(existing_entities.get('CanonicalConcept', []))}
   - SurveyProcess: {', '.join(existing_entities.get('SurveyProcess', []))}

3. **Node properties MUST use controlled vocabularies:**
   - fact_category: {', '.join(config.FACT_CATEGORIES)}
   - dimension: {', '.join(config.DIMENSIONS)}
   - value_type: {', '.join(config.VALUE_TYPES)}
   - assertion_type: {', '.join(config.ASSERTION_TYPES)}

4. **MethodologicalChoice nodes:**
   - id: lowercase snake_case (e.g., "cps_rotation_group_design")
   - Required: fact_category, survey, assertion_type
   - Link to DataProduct via APPLIES_TO if product-specific
   - Link to SurveyProcess via PART_OF if process-specific
   - Link to QualityAttribute via PRODUCES if quality impact documented

5. **QualityAttribute nodes:**
   - id: lowercase snake_case based on metric name
   - Required: name, dimension, value_type
   - value_number: use for fractions (0-1) and counts
   - value_string: use for categorical/boolean values
   - **CRITICAL:** Fractions must be 0-1, NOT percentages

6. **ConceptDefinition nodes:**
   - id: lowercase snake_case (e.g., "cps_asec_household_income_def")
   - Required: reference_period, unit_of_analysis, granularity, survey
   - Link to CanonicalConcept via OPERATIONALIZES
   - Link to DataProduct via DEFINED_FOR

7. **Threshold nodes:**
   - Include measure, value, operator (gte/lte/eq)
   - Link to DataProduct via CONSTRAINS

8. **TemporalEvent nodes:**
   - Include date or year of change
   - Link to MethodologicalChoice via SUPERSEDES if replacing prior procedure

9. **QualityCaveat nodes:**
   - Document known quality issues, limitations, biases
   - Link to DataProduct via QUALIFIES
   - Optionally link to MethodologicalChoice via MITIGATES

10. **UniverseDefinition nodes:**
    - Document population scope
    - Link to DataProduct via TARGETS

11. **Relationship rules:**
    - APPLIES_TO: MethodologicalChoice → DataProduct (product-specific choices)
    - DEFINED_FOR: ConceptDefinition → DataProduct
    - PART_OF: MethodologicalChoice → SurveyProcess
    - PRODUCES: MethodologicalChoice → QualityAttribute (with mechanism property)
    - OPERATIONALIZES: ConceptDefinition → CanonicalConcept
    - TARGETS: DataProduct → UniverseDefinition
    - CONSTRAINS: Threshold → DataProduct
    - SUPERSEDES: TemporalEvent → MethodologicalChoice
    - QUALIFIES: QualityCaveat → DataProduct
    - MITIGATES: MethodologicalChoice → QualityCaveat

12. **DO NOT create MENTIONS relationships.** Only use the relationships listed above.

OUTPUT FORMAT:
Return ONLY a JSON object with this structure (no markdown fences, no explanation):

{{
  "nodes": [
    {{
      "id": "node_id_in_snake_case",
      "type": "MethodologicalChoice",
      "properties": {{
        "fact_category": "design",
        "survey": "cps",
        "assertion_type": "fact"
      }}
    }},
    ...
  ],
  "relationships": [
    {{
      "source": "source_node_id",
      "target": "target_node_id",
      "type": "APPLIES_TO",
      "properties": {{
        "valid_from": "2014-01-01",
        "valid_until": null
      }}
    }},
    ...
  ]
}}

TEXT TO EXTRACT FROM:
{chunk_text}

Return the JSON now:"""

    return prompt
