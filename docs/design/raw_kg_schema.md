# Design Document: Raw Knowledge Graph Schema for Pragmatics Extraction

*Version: 3.1 — 2026-02-09*
*Status: Approved for Phase 1 implementation (post bug-fix review)*
*Review History: Five external reviews (Gemini Pro, GPT-5.2, Kimi-K2.5, Grok-4, GPT-5.2 round 3). Bug fixes applied from GPT-5.2 structural review (round 3).*

---

## 1. Purpose & Governing Analogy

The raw knowledge graph is a **clinical assessment system** for statistical data fitness-for-use.

| Medical Analogy | Census MCP Equivalent |
|----------------|----------------------|
| Doctor's medical training | LLM's statistical knowledge (the 90%) |
| Lab tests, patient history, vitals | Extracted `MethodologicalChoice` + `QualityAttribute` (raw KG) |
| Fitness standards by military occupational specialty | `AnalysisTask` + `REQUIRES` edges (what does this job demand?) |
| Fit/unfit determination with conditions | Harvested `ContextItem` (the pragmatic judgment) |
| The patient | The dataset the user wants to use |

**The KG does NOT contain diagnoses.** It contains the test results and the standards. Diagnoses (fitness implications) are derived by matching results against standards — via Cypher pattern-matching, not LLM inference.

**The question this KG answers:** "Given what we know about this survey's procedures and their measurable quality consequences, which analytic tasks are compromised, and how?"

**Immediate scope:** CPS-ACS income comparability. 3-5 source documents.

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────┐
│  Layer 0: SEED KNOWLEDGE (human expert, once)   │
│  AnalysisTask nodes + REQUIRES edges            │
│  ~20-30 rules encoding "what does good look     │
│  like for this analytic task?"                   │
│  Templates: threshold + condition +              │
│  violation_template + recommended_action         │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│  Layer 1: EXTRACTION (LLM, per document)        │
│  MethodologicalChoice + QualityAttribute        │
│  Factual only. No implications.                 │
│  "What does this survey do, and what are the    │
│  measurable quality consequences?"              │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│  Layer 2: HARVEST (Cypher, automated)           │
│  Pattern-match: REQUIRES vs PRODUCES            │
│  Instantiate violation templates                │
│  Flag unanticipated interactions                 │
│  Output: candidate ContextItems                 │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│  Layer 3: CURATION (human, per harvest batch)   │
│  Validate instantiated warnings                 │
│  Adjust severity, scope, wording                │
│  Approve for inclusion in pragmatics DB         │
│  Expert time: 10-15 min per batch (not hours)   │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│  Layer 4: EXPORT & COMPILE (automated)          │
│  neo4j_to_staging.py → staging JSON             │
│  compile_pack.py → SQLite packs (shipped)       │
└─────────────────────────────────────────────────┘
```

### Work Distribution

| Activity | Who | Frequency | Effort |
|----------|-----|-----------|--------|
| Define AnalysisTask + REQUIRES patterns | SME | Once per task type | High initial, then stable |
| Extract MethodologicalChoice from docs | LLM + human verification | Per document | Low (factual extraction) |
| Run harvest queries | Automated | Per curation cycle | Near-zero |
| Validate ContextItem instantiations | SME or trained reviewer | Per harvest batch | Medium (validation, not research) |
| Handle flagged unanticipated interactions | SME | As flagged | Targeted, rare |

---

## 3. Node Types (Phase 1: 13 types)

### 3.1 Layer 0: Seed Knowledge (Expert-Curated)

| Node Label | Description | Example | Seeded By |
|------------|-------------|---------|-----------|
| `AnalysisTask` | A category of analytic work a user might perform | "EstimateChangeOverTime", "CrossSurveyComparison", "SmallAreaEstimation" | Expert (one-time) |
| `CanonicalConcept` | Abstract concept that multiple surveys operationalize differently | "Household Income", "Employment" | Expert (one-time) |

**AnalysisTask Properties:**
```
name: str                       # e.g., "EstimateChangeOverTime"
description: str                # What this task involves
typical_use_cases: [str]        # Concrete examples
critical_quality_dimensions: [str]  # What quality attributes matter
```

**CanonicalConcept Properties:**
```
name: str                       # e.g., "Household Income"
canonical_definition: str|null  # Provisional; sourced to harmonization effort
```

### 3.2 Layer 1: Extracted Knowledge (LLM from Documents)

| Node Label | Description | Example |
|------------|-------------|---------|
| `MethodologicalChoice` | A specific decision or procedure within a survey process | "ACS 5-year estimates pool 60 months of data" |
| `QualityAttribute` | A measurable quality consequence of a methodological choice | "Consecutive 5-year estimates share 48 of 60 months (overlap = 0.8)" |
| `DataProduct` | A specific survey, release, or data product | "CPS ASEC", "ACS 5-Year" |
| `SurveyProcess` | A stage in the survey pipeline | "Sampling", "Weighting", "Estimation" |
| `UniverseDefinition` | Who/what is in scope | "Civilian noninstitutional population aged 16+" |
| `ConceptDefinition` | How a survey operationalizes a concept | "CPS ASEC: total money income = sum of 8 components for previous calendar year" |
| `Threshold` | Specific numeric boundary with operational consequences | "ACS 1-year requires 65,000+ population" |
| `TemporalEvent` | Dated methodology change | "2014 CPS ASEC redesign: income questions changed (split-panel test)" |
| `QualityCaveat` | Known quality issue or limitation | "CPS ASEC income nonresponse ~15%, hot-deck imputed" |
| `SourceDocument` | A source document in the corpus | See §5 |

### 3.3 Layer 2: Derived Knowledge (Harvest Output)

| Node Label | Description | Example |
|------------|-------------|---------|
| `ContextItem` | Materialized fitness-for-use judgment, derived by harvest | "Don't compare consecutive ACS 5-year estimates — they share 4/5 of the data" |

**ContextItem** is NOT extracted. It is produced by Cypher pattern-matching (Layer 2) and validated by humans (Layer 3). It carries full derivation provenance.

### 3.4 Required Properties

**All Extracted Nodes (Layer 1):**
```
# Per-node (minimal):
assertion_type: str         # "verbatim" | "paraphrased"

# All other provenance lives on the SOURCED_FROM edge (see §4.6)
```

Note: `assertion_type` no longer includes "inferred" — Layer 1 is factual extraction only. Inference happens in Layer 2 via graph traversal.

**MethodologicalChoice:**
```
fact_category: str          # CONTROLLED: "design" | "collection" | "weighting" |
                            #   "estimation" | "variance" | "processing" | "adjustment"
survey: str                 # "acs" | "cps" | "decennial" | "general"
valid_from: str|null        # ISO date (YYYY-MM-DD) when this choice took effect. Use Neo4j date() in queries.
valid_until: str|null       # ISO date (YYYY-MM-DD) when superseded. null = current/ongoing.
```

**QualityAttribute:**
```
name: str                   # Metric identifier within dimension
                            #   e.g., "overlap_fraction", "imputation_rate", "effective_sample_size"
dimension: str              # STABLE JOIN KEY for REQUIRES matching
                            #   e.g., "temporal_comparability", "precision", "coverage",
                            #   "definitional_alignment"
value_type: str             # "fraction" | "count" | "boolean" | "categorical"
value_number: float|null    # Numeric value (use when value_type is fraction or count)
value_string: str|null      # Categorical/text value (use when value_type is boolean or categorical)
unit: str|null              # e.g., "months", "persons", "percent"
                            # NOTE: fractions must be 0-1, not percentages. Enforce in extraction prompt.
```

**ConceptDefinition:**
```
reference_period: str       # e.g., "previous calendar year", "past 12 months"
unit_of_analysis: str       # e.g., "person", "household", "family"
granularity: str            # "composite" | "component"
survey: str                 # "acs" | "cps" etc.
```

**QualityCaveat (optional for clustering):**
```
tse_type: str|null          # OPTIONAL: "coverage" | "sampling" | "nonresponse" |
                            #   "measurement" | "processing" | null
```

**Threshold:**
```
measure: str                # What's being thresholded
value: str                  # The threshold value
operator: str               # "gte" | "lte" | "eq"
scope_notes: str|null       # Geographic/subgroup/temporal limitations
```

**ContextItem (Layer 2 output):**
```
derived_from_task: str      # AnalysisTask name
derived_from_choices: [str] # MethodologicalChoice IDs
instantiated_warning: str   # Filled template text
instantiated_recommendation: str
validation_status: str      # "pending" | "approved" | "rejected"
derivation_confidence: str  # "high" (direct pattern match) | "medium" (flagged interaction)
human_reviewer_notes: str|null
```

---

## 4. Relationship Types (Phase 1: 16 types)

### 4.1 Structural Relationships

| Relationship | From → To | Meaning |
|-------------|-----------|---------|
| `PART_OF` | MethodologicalChoice → SurveyProcess | This choice is part of this pipeline stage |
| `IMPLEMENTS` | DataProduct → SurveyProcess | Informational grouping only. Do NOT use for harvest joins — use APPLIES_TO instead. |
| `APPLIES_TO` | MethodologicalChoice → DataProduct | **Product-scoping edge.** This choice applies to this specific product. Required properties: `valid_from` (ISO date or null), `valid_until` (ISO date or null). **Required on all extracted MethodologicalChoice nodes.** |
| `DEFINED_FOR` | ConceptDefinition → DataProduct | Links concept definitions to specific products. Required for cross-survey comparison queries. |
| `OPERATIONALIZES` | ConceptDefinition → CanonicalConcept | This survey defines this concept this way |
| `TARGETS` | DataProduct → UniverseDefinition | This product covers this population |
| `SOURCED_FROM` | any → SourceDocument | Provenance link |

> ⚠️ **Design Note (Bug Fix #1):** Generic `SurveyProcess` nodes are shared across products.
> Harvest queries MUST join through `APPLIES_TO` for product-scoped results,
> NEVER through `IMPLEMENTS → SurveyProcess ← PART_OF`.

### 4.2 Quality/Consequence Relationships

| Relationship | From → To | Meaning | Required Properties |
|-------------|-----------|---------|---------------------|
| `PRODUCES` | MethodologicalChoice → QualityAttribute | This procedure creates this quality consequence | `mechanism` (how) |
| `REQUIRES` | AnalysisTask → QualityAttribute | This task needs this quality dimension to meet a standard | `threshold`, `condition`, `violation_severity`, `violation_template`, `recommended_action` |
| `TRADES_OFF_WITH` | QualityAttribute → QualityAttribute | Improving one degrades the other | `mechanism` |
| `MITIGATES` | MethodologicalChoice → QualityCaveat | This procedure reduces this quality issue | `mechanism` |
| `QUALIFIES` | QualityCaveat → DataProduct | This caveat affects this product | |

### 4.3 Temporal/Evolution Relationships

| Relationship | From → To | Meaning | Required Properties |
|-------------|-----------|---------|---------------------|
| `SUPERSEDES` | TemporalEvent → MethodologicalChoice | This change replaced this procedure | |
| `CONSTRAINS` | Threshold → DataProduct | This threshold limits this product | |
| `CONFOUNDS` | any → any | These interact to create compounding effects | `mechanism`, `evidence_basis`, `interaction_type` (CONTROLLED: "bias_interaction" \| "variance_interaction" \| "comparability_break" \| "coverage_interaction") |

### 4.4 Derivation Relationship

| Relationship | From → To | Meaning |
|-------------|-----------|---------|
| `DERIVED_FROM` | ContextItem → MethodologicalChoice[] | Reasoning chain from facts to judgment |

### 4.5 The REQUIRES Edge: Where Expert Knowledge Lives

This is the most important relationship in the schema. It encodes reusable expert judgment as structured rules:

```cypher
// Numeric threshold rule
CREATE (task:AnalysisTask {name: "EstimateChangeOverTime"})
CREATE (qa:QualityAttribute {name: "overlap_fraction", dimension: "temporal_comparability"})
CREATE (task)-[r:REQUIRES {
  rule_type: "numeric_threshold",           // CONTROLLED: "numeric_threshold" | "categorical_match" |
                                            //   "categorical_mismatch" | "boolean_required"
  threshold_number: 0.2,                    // For numeric rules
  threshold_string: null,                   // For categorical rules
  condition: "data_overlap_between_consecutive_periods",
  violation_severity: "critical",
  violation_template: "Consecutive estimates share {value} of underlying data. Standard change estimates are unreliable.",
  recommended_action: "Use non-overlapping periods or apply published variance correction factors."
}]->(qa)

// Categorical match rule
CREATE (task2:AnalysisTask {name: "CrossSurveyComparison"})
CREATE (qa2:QualityAttribute {name: "reference_period_alignment", dimension: "definitional_alignment"})
CREATE (task2)-[r2:REQUIRES {
  rule_type: "categorical_match",
  threshold_number: null,
  threshold_string: "matching",
  condition: "reference_periods_must_align_across_products",
  violation_severity: "high",
  violation_template: "Reference periods differ: {survey1} uses {period1} while {survey2} uses {period2}. Direct comparison produces systematic bias.",
  recommended_action: "Restrict to overlapping reference windows or apply published reconciliation factors."
}]->(qa2)
```

**Harvest queries are dispatched by `rule_type`** — one query pattern per type, not a single generic query. See §6 for patterns.

One REQUIRES edge generates warnings for ALL DataProducts where the pattern matches. Seed once, harvest forever.

### 4.6 Provenance Model

All extraction provenance lives on the `SOURCED_FROM` relationship edge, NOT on node properties.

**SOURCED_FROM edge properties:**
```
source_section: str         # Chapter/section reference
source_page: str|int        # Page number or range
raw_text: str               # Original text passage
extraction_model: str       # Which LLM extracted this
extraction_date: str        # ISO date
```

**Why edge-based:** Enables multi-citation (one node sourced from multiple document passages). Coverage queries use `MATCH (n)-[:SOURCED_FROM]->(d:SourceDocument)` which is now guaranteed to exist.

**Rule:** Every Layer 1 node MUST have at least one `SOURCED_FROM` edge. Nodes without provenance edges are invalid.

**ContextItem provenance** uses `DERIVED_FROM` edges (not `SOURCED_FROM`) linking to the MethodologicalChoice/QualityAttribute nodes that generated it, plus properties: `harvest_query_id`, `harvest_date`, `derivation_confidence`.

---

## 5. Source Document Nodes

```cypher
(:SourceDocument {
    catalog_id: "CPS-TP-077",
    title: "Design and Methodology: Current Population Survey",
    year: 2006,
    pages: 131,
    local_path: "knowledge-base/census_cps/CPS-Tech-Paper-77.pdf",
    ingestion_status: "complete" | "partial" | "pending",
    ingestion_date: "2026-02-08",
    pages_extracted: [1,2,3,...],
    pages_total: 131
})
```

---

## 6. Harvest Queries (Layer 2)

### 6.1a Numeric Threshold Violations
```cypher
// Harvest pattern for numeric rules (overlap, sample size, CV, etc.)
MATCH (task:AnalysisTask)-[req:REQUIRES]->(qa_std:QualityAttribute)
WHERE req.rule_type = "numeric_threshold"
MATCH (mc:MethodologicalChoice)-[ap:APPLIES_TO]->(dp:DataProduct)
WHERE ap.valid_until IS NULL OR date(ap.valid_until) >= date()  // current choices only
MATCH (mc)-[:PRODUCES]->(qa_obs:QualityAttribute)
WHERE qa_obs.dimension = qa_std.dimension
  AND qa_obs.value_number IS NOT NULL
  AND qa_obs.value_number >= req.threshold_number
RETURN {
  task: task.name,
  product: dp.name,
  warning: replace(req.violation_template, "{value}", toString(qa_obs.value_number)),
  recommendation: req.recommended_action,
  severity: req.violation_severity,
  source_facts: collect(mc.name),
  confidence: "high"
} AS candidate_context_item
```

### 6.1b Categorical Mismatch Violations (Cross-Survey)
```cypher
// Harvest pattern for categorical match rules (reference period, unit of analysis, etc.)
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
} AS candidate_context_item
```

### 6.2 Cross-Survey Concept Misalignment

See §6.1b above — concept misalignment is now a REQUIRES-driven harvest pattern.

### 6.3 Universe Mismatches
```cypher
MATCH (dp1:DataProduct)-[:TARGETS]->(u1:UniverseDefinition)
MATCH (dp2:DataProduct)-[:TARGETS]->(u2:UniverseDefinition)
WHERE dp1.name CONTAINS "CPS" AND dp2.name CONTAINS "ACS" AND u1 <> u2
RETURN {
  warning: "Population scope differs: " + dp1.name + " targets " + 
           u1.raw_text + " while " + dp2.name + " targets " + u2.raw_text,
  severity: "critical",
  confidence: "high"
} AS candidate_context_item
```

### 6.4 Unanticipated Interactions (Flagged for Expert Review)
```cypher
// Co-occurring methodology changes affecting same quality dimension
MATCH (mc1:MethodologicalChoice)-[:PRODUCES]->(qa1:QualityAttribute)
MATCH (mc2:MethodologicalChoice)-[:PRODUCES]->(qa2:QualityAttribute)
WHERE mc1 <> mc2
  AND qa1.dimension = qa2.dimension
  AND (mc1.valid_from IS NULL OR mc2.valid_until IS NULL
       OR date(mc1.valid_from) <= date(mc2.valid_until))
  AND (mc2.valid_from IS NULL OR mc1.valid_until IS NULL
       OR date(mc2.valid_from) <= date(mc1.valid_until))
  AND NOT EXISTS { MATCH (mc1)-[:CONFOUNDS]-(mc2) }
RETURN {
  type: "potential_unanticipated_interaction",
  choices: [mc1.name, mc2.name],
  dimension: qa1.dimension,
  confidence: "low",
  action: "Expert review needed"
} AS flagged_interaction
```

### 6.5 Coverage Report
```cypher
MATCH (d:SourceDocument)
OPTIONAL MATCH (n)-[:SOURCED_FROM]->(d)
RETURN d.catalog_id, d.ingestion_status, 
       d.pages_total, count(DISTINCT n) AS nodes_extracted
```

### 6.6 Unconnected Facts (Extraction Gaps)
```cypher
MATCH (mc:MethodologicalChoice)
WHERE NOT (mc)-[:PRODUCES]->(:QualityAttribute)
OPTIONAL MATCH (mc)-[src:SOURCED_FROM]->(doc:SourceDocument)
RETURN mc.fact_category, doc.catalog_id AS source_document,
       src.source_page, src.raw_text
ORDER BY mc.fact_category, src.source_page
```

---

## 7. Extraction Prompt Engineering (Layer 1)

### 7.1 Core Principle

**The extraction prompt asks for FACTS and MEASUREMENTS, not judgments.**

Instead of: "What are the fitness implications of this methodology?"
Ask: "What specific procedures does this survey use, and what are their measurable quality consequences?"

This is more reliable because LLMs extract facts well and implications poorly.

### 7.2 Extraction Targets

For each text chunk, extract:

1. **MethodologicalChoice**: What does the survey do? Include `fact_category`, scope, validity period.
2. **QualityAttribute**: What measurable quality consequence does this produce? Include dimension, value_type, value.
3. **ConceptDefinition**: How does this survey define/measure a concept? Include reference_period, unit_of_analysis.
4. **UniverseDefinition**: Who is in/out of scope?
5. **Threshold**: Any numeric boundaries with operational consequences?
6. **TemporalEvent**: Any dated methodology changes?
7. **QualityCaveat**: Any documented quality issues, limitations, error sources?

### 7.3 Prompt Requirements

1. **Penalize summary, reward operational detail.** "Ignore general descriptions. Focus on specific constraints, thresholds, adjustment procedures, edge cases, and processing rules."
2. **Force scope specificity** — "for CPS ASEC post-2014" not "for CPS"
3. **Extract the PRODUCES relationship** — every MethodologicalChoice should be paired with its quality consequence where documented
4. **Extract `fact_category`** from controlled vocabulary
5. **Extract `reference_period` and `unit_of_analysis`** for every ConceptDefinition
6. **Preserve page numbers**

### 7.4 Deduplication Strategy

Do NOT deduplicate during extraction. After extraction:
1. Cluster nodes by semantic similarity + matching `fact_category` + matching `survey`
2. Maintain all evidence citations
3. Merge only with human/Opus review
4. For overlapping documents: mark later edition as `preferred_source`, preserve both

---

## 8. Seeding Guide (Layer 0)

### 8.1 Initial AnalysisTask Set (Seed 5-10 for CPS-ACS Income)

| Task Name | Description | Critical Quality Dimensions |
|-----------|-------------|----------------------------|
| `EstimateChangeOverTime` | Compare estimates across time periods | temporal_comparability, overlap_structure, seasonal_adjustment_status |
| `CrossSurveyComparison` | Compare estimates across surveys (CPS vs ACS) | definitional_alignment, universe_match, reference_period_match |
| `SmallAreaEstimation` | Estimate for sub-state geographies | effective_sample_size, direct_estimate_reliability |
| `SubgroupAnalysis` | Estimate for demographic subpopulations | subgroup_sample_size, design_effect |
| `IncomeDistributionAnalysis` | Analyze income distribution shape | topcoding_effects, imputation_method, component_coverage |

### 8.2 REQUIRES Edge Examples

```cypher
// Task: CrossSurveyComparison requires matching reference periods
CREATE (t:AnalysisTask {name: "CrossSurveyComparison"})
CREATE (qa:QualityAttribute {name: "reference_period_alignment", dimension: "definitional_alignment"})
CREATE (t)-[:REQUIRES {
  rule_type: "categorical_match",
  threshold_number: null,
  threshold_string: "matching",
  condition: "reference_periods_must_align",
  violation_severity: "high",
  violation_template: "Reference periods differ: {survey1} uses {period1} while {survey2} uses {period2}. Direct comparison produces systematic bias.",
  recommended_action: "Restrict to overlapping reference windows or apply published reconciliation factors."
}]->(qa)

// Task: CrossSurveyComparison requires matching universes
CREATE (qa2:QualityAttribute {name: "universe_alignment", dimension: "coverage"})
CREATE (t)-[:REQUIRES {
  rule_type: "categorical_match",
  threshold_number: null,
  threshold_string: "matching",
  condition: "target_populations_must_align",
  violation_severity: "critical",
  violation_template: "{survey1} targets {universe1} while {survey2} targets {universe2}. Aggregates are not comparable without universe restriction.",
  recommended_action: "Restrict both surveys to overlapping population (e.g., civilian noninstitutional 16+)."
}]->(qa2)
```

### 8.3 Seeding Process

1. Expert identifies 5-10 common analytic tasks for CPS-ACS income work
2. For each task, defines 3-5 REQUIRES edges with violation templates
3. Templates use `{placeholder}` syntax filled from graph data at harvest time
4. Total seeding effort: ~1 day for initial set
5. New tasks added incrementally as new surveys/use cases arise

---

## 9. Phase 2 Decision Points

| Decision | Trigger | Action |
|----------|---------|--------|
| Split `MethodologicalChoice` | `fact_category` shows clear clustering | Promote categories to node labels |
| Add `Scope` node | Unscoped generalizations cause false positives | Promote scope properties to nodes |
| TSE-type `QualityCaveat` | Caveats are unclusterable | Require `tse_type` |
| Claim reification | >10 documents, contradictions across editions | Add Claim + Evidence layer |
| `ComparabilityAssessment` | `OPERATIONALIZES` + `CanonicalConcept` insufficient | Add structured comparison nodes |
| Split `CONFOUNDS` | Edge overuse | Promote to BIASES, INCREASES_VARIANCE, etc. |
| `WeightingStage` nodes | Weighting pipeline detail needed for diagnosis | Add ordered sub-process nodes |
| `DataCollectionMode` nodes | Mode effects need first-class representation | Add mode nodes with BIASES edges |

---

## 10. Pre-Extraction Checklist

- [ ] `SourceDocument` nodes created for target documents
- [ ] `CanonicalConcept` nodes seeded (Household Income, Family Income, Personal Income, Earnings, Money Income, Employment)
- [ ] `DataProduct` nodes seeded (CPS ASEC, CPS Basic Monthly, ACS 1-Year, ACS 5-Year)
- [ ] `SurveyProcess` nodes seeded (Sampling, Collection, Weighting, Estimation, Processing, Dissemination)
- [ ] `AnalysisTask` nodes seeded (5-10 per §8.1)
- [ ] `REQUIRES` edges defined with templates (per §8.2)
- [ ] Extraction prompt written, tested on 2-3 sample pages
- [ ] `fact_category` controlled vocabulary finalized
- [ ] Neo4j constraints/indexes created

---

## 11. Relationship to Existing Architecture

| Component | Role |
|-----------|------|
| Neo4j `raw` database | The quarry — Layer 0 seeds + Layer 1 extractions |
| Neo4j `pragmatics` database | Layer 3 approved ContextItems |
| `staging/*.json` | Export from pragmatics DB (downstream, not authoring surface) |
| `packs/*.db` | Compiled SQLite (shipped to users) |
| `scripts/extract/` | Extraction pipeline code and prompts |
| `scripts/harvest/` | Harvest query scripts (Layer 2) |
| `provenance_catalog` table | Coverage tracking in compiled packs |

---

## Appendix A: External Review Summary

Schema reviewed across five rounds by four independent models.

| Model | Round | Key Contribution |
|-------|-------|-----------------|
| Gemini Pro | 1, 2 | Split MethodologicalFact, add AnalyticTask, soft-type via category property |
| GPT-5.2 | 1, 2 | Scope as first-class, reference_period/unit_of_analysis critical, claim reification |
| Kimi-K2.5 | 1 | Abandon FitnessImplication as extractable → derive via harvest. Process-centric design. |
| Grok-4 | 1 | Confirmed template-based harvest architecture, concrete REQUIRES seeding patterns |
| GPT-5.2 | 3 | Structural bugs: product-scoping, query path validity, type safety, provenance redundancy |

**Convergent finding (all four):** Fitness implications should be derived, not extracted. Expert knowledge belongs in reusable task/requirement structures, not per-document prose.

**Round 3 structural review (GPT-5.2):** Five blocking bugs identified and fixed: product-scoping via generic SurveyProcess, missing DEFINED_FOR relationship, provenance redundancy, QualityAttribute type safety, REQUIRES threshold heterogeneity.

**Key architectural shift:** From "extract facts AND implications" to "extract facts, seed standards, harvest violations."
