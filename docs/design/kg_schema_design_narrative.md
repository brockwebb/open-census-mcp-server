# How We Designed the Census MCP Knowledge Graph Schema
## A Multi-Model Adversarial Review Process

*Brock Webb — February 2026*
*Census Open Ontology of Statistics (COOS) Project*

---

## The Problem

The Census MCP Server needs to give AI models the same instincts a senior statistician has when working with Census data. When someone asks "how has median income changed in Baltimore?" a statistician doesn't just pull numbers — they mentally check a dozen fitness-for-use concerns: Are ACS 5-year estimates overlapping? Is the margin of error too wide for this geography? Did the CPS income questions change in 2014?

That expert judgment is what makes data *useful* rather than *misleading*. Our challenge: encode it in a form an AI can access at query time.

## The Approach: Knowledge Graph as Clinical Assessment System

We arrived at a medical analogy that governs the entire design. A "fit for duty" determination works like this: a doctor doesn't write the diagnosis into the patient's chart before the exam. They collect vitals, run labs, review history, then match results against standards for the specific job the soldier needs to do. Lost a limb? Fit for a desk as a cyber warrior, unfit for field infantry.

Our knowledge graph works the same way:

| Medical System | Census MCP Equivalent |
|----------------|----------------------|
| Lab tests and vitals | Extracted survey methodology facts (`MethodologicalChoice` + `QualityAttribute`) |
| Fitness standards by job specialty | `AnalysisTask` + `REQUIRES` rules ("what does trend analysis demand?") |
| Fit/unfit determination | Harvested `ContextItem` (the pragmatic judgment delivered to the LLM) |
| The patient | The dataset the user wants to use |

**The KG contains test results and standards, not diagnoses.** Diagnoses are derived by matching results against standards via automated graph queries.

## The Architecture: Four Layers

```
Layer 0: SEED    — Expert defines analysis tasks and quality requirements (once)
Layer 1: EXTRACT — LLM pulls facts from methodology handbooks (per document)
Layer 2: HARVEST — Cypher queries pattern-match violations (automated)
Layer 3: CURATE  — Human validates generated warnings (10-15 min per batch)
Layer 4: EXPORT  — Compile to SQLite packs shipped with the MCP server
```

The critical insight — arrived at through adversarial review — is that **fitness implications are derived, not extracted.** We don't ask the LLM to figure out what a statistician would warn about. We extract what the survey *does*, define what good analysis *requires*, and let graph traversal surface the gaps.

## The Review Process: Five Models, Five Rounds

Rather than designing in a vacuum, we subjected the schema to adversarial review by four independent AI models across five rounds, each chosen for a different perspective:

**Round 1 — Initial Design Review**
- **Google Gemini Pro**: Recommended splitting our overly-broad `MethodologicalFact` node, adding soft-typing via category properties, and introducing `AnalyticTask` as a concept.
- **OpenAI GPT-5.2**: Pushed for scope as a first-class concern, flagged `reference_period` and `unit_of_analysis` as critical for income comparison, proposed claim-centric reification.
- **Kimi-K2.5** (Moonshot AI): Delivered the architectural breakthrough — argued that fitness implications should be *abandoned as an extraction target* entirely, replaced by a process-centric schema where implications emerge from graph traversal. Proposed the template-based harvest architecture.

**Round 2 — Synthesis Review**
We synthesized the Round 1 feedback into a revised proposal and sent it back to Gemini and GPT-5.2 in their existing threads (maintaining full context). Both confirmed the phased approach was sound and converged on two "adopt now" requirements: `fact_category` on methodology nodes and `reference_period`/`unit_of_analysis` on concept definitions.

**Round 3 — Harvest Architecture Validation**
We sent Kimi's "derive, don't extract" proposal as a follow-up question. **Grok-4** (via Poe's cross-model feature) independently confirmed the template-based harvest pattern and provided concrete Cypher implementations. Both models produced consistent work-distribution tables showing 10x efficiency gains over manual authoring.

**Round 4 — Structural Bug Review**
GPT-5.2 reviewed the complete v3.0 schema and found **five blocking bugs** that would have caused the system to fail silently:

1. **Cross-product contamination**: Generic `SurveyProcess` nodes shared across products meant every methodology choice became reachable from every product. Harvest queries would generate systematic false positives.

2. **Nonexistent query path**: The cross-survey comparison query referenced a relationship (`SurveyProcess → ConceptDefinition`) that didn't exist in the schema. Would return zero results.

3. **Provenance redundancy**: Both node properties AND relationship edges carried provenance data, creating inconsistency and preventing multi-citation.

4. **Type safety failure**: `QualityAttribute.value` was defined as string but used in numeric comparisons. Harvest queries would silently fail or produce nonsense.

5. **Threshold heterogeneity**: `REQUIRES` edges mixed numeric thresholds (0.2) with categorical ones ("matching"). No single query could evaluate both.

Plus three high-risk issues: null-unsafe date comparisons, unconstrained `CONFOUNDS` edges, and non-numeric comparison rules lacking formalization.

**Round 5 — Final Validation**
Google Gemini gave a "green light with minor warnings" (null handling, unit normalization) while GPT-5.2's bug fixes were applied. All 8 fixes verified via automated audit.

## Key Convergent Findings

Across all four models and five rounds, several findings emerged independently:

**Universal agreement:**
- Fitness implications should be derived, not extracted from documents
- Expert knowledge belongs in reusable task/requirement structures
- Extraction should capture facts and measurements; judgment is a separate pass
- `reference_period` and `unit_of_analysis` are the #1 CPS-ACS income comparability trap
- Staged extraction (facts first, then implications) dramatically improves reliability

**The strongest disagreement** was on scope handling: GPT-5.2 wanted a first-class `Scope` node on every extracted entity; Gemini said existing nodes handle scope naturally. We deferred the `Scope` node to Phase 2, using structured properties and prompt-enforced specificity for Phase 1.

## What the Schema Looks Like

**13 node types** across three layers:
- *Seed knowledge*: `AnalysisTask`, `CanonicalConcept`
- *Extracted facts*: `MethodologicalChoice`, `QualityAttribute`, `DataProduct`, `SurveyProcess`, `UniverseDefinition`, `ConceptDefinition`, `Threshold`, `TemporalEvent`, `QualityCaveat`, `SourceDocument`
- *Derived output*: `ContextItem`

**16 relationship types** including the critical `REQUIRES` edge where expert judgment lives as reusable rules with violation templates.

**Example harvest**: An expert seeds a rule: "Trend analysis requires data overlap < 0.2 between consecutive periods." The LLM extracts from the ACS handbook: "5-year estimates pool 60 months; consecutive periods share 48 months (overlap = 0.8)." A Cypher query matches the 0.8 against the 0.2 threshold and instantiates: *"Consecutive ACS 5-Year estimates share 80% of underlying data. Standard change estimates are unreliable. Use non-overlapping periods."*

That warning ships in a SQLite pack. When a user asks an LLM about income trends, the warning is retrieved and incorporated into the response. No statistician needed at query time — their judgment was encoded in the REQUIRES rule.

## Why This Matters

Traditional approaches to Census data access assume the user knows what they're doing. They don't flag that ACS 5-year estimates overlap. They don't warn that CPS and ACS define "income" differently. They don't mention that the 2014 CPS redesign broke trend comparisons.

The knowledge graph transforms Census data access from *lookup* to *consultation*. The goal: any 8th grader with an active imagination should be able to pull authoritative data and get plain-language explanations of what it means and what to watch out for.

## Lessons Learned

**Multi-model adversarial review works.** Each model brought genuinely different perspectives. Google thought like a search engineer (queryability, soft typing). OpenAI thought like a knowledge representation researcher (reification, scope formalism). Kimi thought like a systems architect (process-centric, derived vs. extracted). And when we sent the synthesis back, they found each other's blind spots.

**The most valuable feedback came from the most unconventional model.** Kimi's "abandon FitnessImplication as extractable" was the insight that reorganized the entire architecture. It's counterintuitive — the thing you most want to produce is the thing you should NOT try to extract.

**Bug-finding requires a different mindset than design review.** The first four reviews produced architectural insights. The fifth (GPT-5.2 round 3) found implementation bugs. Both are necessary; neither substitutes for the other.

**The 90/10 rule holds.** LLMs handle 90% of the work (extraction, pattern matching) with 10% of the effort. The remaining 10% (seeding analysis tasks, defining REQUIRES rules) takes 90% of the expert effort — but it's invested once and reused forever.

---

*Schema v3.1 is approved for Phase 1 implementation. Source: `docs/design/raw_kg_schema.md` in the census-mcp-server repository.*
