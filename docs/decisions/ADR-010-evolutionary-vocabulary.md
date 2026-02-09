# ADR-010: Evolutionary Controlled Vocabulary with Provisional Extensions

**Status:** Accepted
**Date:** 2026-02-09
**Traces to:** FR-QE-006, FR-QE-014 (new), ADR-008

---

## Context

During the first real extraction of the CPS Handbook (157 chunks, 493 nodes), the LLM produced 21 nodes with `fact_category` values outside the controlled vocabulary:

- `dissemination` (17 nodes) — periodicity, release schedules, publication processes
- `definition` (4 nodes) — unemployment criteria (misclassified; should be `ConceptDefinition` nodes)

The `dissemination` category is a legitimate survey lifecycle stage that our vocabulary missed. The LLM correctly identified a gap. The `definition` category is a node-type error, not a vocabulary gap.

This presents a fundamental design tension: static controlled vocabularies are brittle and lose signal, while unconstrained vocabularies produce chaos that breaks downstream harvest queries.

## Decision

Implement an **evolutionary vocabulary** with three tiers:

1. **Core vocabulary** — Established terms validated across multiple documents. Enforced strictly. Listed in `FACT_CATEGORIES`, `DIMENSIONS`, etc.

2. **Provisional extensions** — New terms discovered during extraction. Accepted with warnings (not rejections). Tracked in `VOCABULARY_EXTENSIONS` with metadata: source document, first seen date, occurrence count.

3. **Rejected terms** — Terms reviewed and determined to be errors (misclassification, synonyms of existing terms). Listed in `VOCABULARY_REJECTIONS` with mapping to correct term or correct node type.

**Promotion lifecycle:**
```
LLM generates new term
  → Validation warns (not rejects)
  → Term added to VOCABULARY_EXTENSIONS with count=1
  → Term recurs in subsequent document extractions → count increments
  → After 2+ documents use the term → review for promotion to core
  → If term doesn't recur → review for rejection
```

**Double-regressive trait:** Extensions that don't prove their value across documents get pruned. Terms that repeatedly appear earn permanent status. The system self-repairs by absorbing legitimate vocabulary and shedding noise, but always with human review at promotion/rejection decision points.

## Rationale

### Why not strict enforcement (reject unknown terms)?
- Loses signal. The LLM found a real category (`dissemination`) that our initial vocabulary missed.
- Forces the LLM into junk-drawer categories (`processing` becomes a dumping ground), destroying the semantic precision harvest queries depend on.
- Assumes the vocabulary designers anticipated all categories before seeing real documents. They didn't and won't.

### Why not permissive (accept anything)?
- Vocabulary explodes. Each extraction invents its own terms.
- Harvest queries can't match on categories because the same concept has 5 synonyms.
- No mechanism to detect and correct errors (like `definition` being a node-type mistake).

### Why evolutionary?
- Mirrors how real taxonomies develop in practice — provisional acceptance, validation through use, promotion or pruning.
- Aligns with the project's "Spider and Starfish" principle: centralized enough to maintain coherence, decentralized enough to adapt to reality.
- Provides audit trail: you can see exactly when a term entered the vocabulary, which documents produced it, and whether it was promoted or rejected.
- Prevents compounding debt: errors caught at extraction time don't propagate into harvest and pack compilation.

### Precedent
The COOS project demonstrated empirically that bottom-up vocabulary discovery (extracting categories from what Census actually publishes) produces better taxonomies than top-down design (deciding what categories should exist). This ADR applies the same principle to the quarry extraction vocabulary.

## Consequences

**Positive:**
- Vocabulary evolves with the corpus rather than constraining it
- Clear audit trail for every vocabulary change
- Errors detected and corrected early (validation warnings, not silent acceptance)
- Human remains in the loop for promotion/rejection decisions

**Negative:**
- Slightly more complex validation logic (three-tier check instead of simple list membership)
- Requires periodic vocabulary review after each new document extraction
- Provisional terms may produce inconsistent harvest results until promoted or rejected

## Implementation

### config.py changes:
```python
# Core vocabulary (strict)
FACT_CATEGORIES = ["design", "collection", "weighting", "estimation", 
                   "variance", "processing", "adjustment", "dissemination"]

# Provisional extensions (warn, don't reject)
VOCABULARY_EXTENSIONS = {
    "fact_category": {
        # "term": {"first_seen": "doc_id", "date": "YYYY-MM-DD", "count": N, "notes": "..."}
    },
    "dimension": {},
    "value_type": {},
    "assertion_type": {},
}

# Rejected terms (map to correct term or node type)
VOCABULARY_REJECTIONS = {
    "fact_category": {
        "definition": {
            "reason": "Node type error — these are ConceptDefinition nodes, not MethodologicalChoice",
            "action": "reclassify_node_type",
            "target_type": "ConceptDefinition",
            "date": "2026-02-09"
        }
    }
}
```

### Validation behavior:
- Core term → accept silently
- Provisional term → accept with INFO log, increment count
- Rejected term → apply correction mapping, WARN log
- Unknown term → accept with WARNING log, auto-add to provisional extensions

---

*Static taxonomies die. Evolutionary ones adapt. The control is in the lifecycle, not the list.*
