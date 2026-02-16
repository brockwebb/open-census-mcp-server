# Bloom Taxonomy Framing — Recurring Reference Note

**Date:** 2026-02-16
**Purpose:** Ensure Bloom tie-in is consistently threaded through all materials
**Tags:** {paper} {slides:main}

## Core Mapping

Bloom's revised taxonomy (Anderson & Krathwohl, 2001) maps directly to the 
knowledge representation hierarchy in this study:

| Bloom Level | Knowledge Type | Census Example | Who/What Provides It |
|-------------|---------------|----------------|---------------------|
| Remember | Factual | "ACS variable B01003_001E is total population" | Model training data, API metadata |
| Understand | Conceptual | "ACS produces period estimates, not point-in-time" | Documents, RAG chunks |
| Apply | Procedural | "SE = MOE / 1.645 to calculate standard error" | Documents, RAG chunks, pragmatics |
| Analyze | Analytical | "CV > 40% means this estimate is unreliable for your use case" | Pragmatics (narrow latitude) |
| Evaluate | Evaluative | "I wouldn't trust this estimate because the allocation rate is 35% for this characteristic in this geography" | Pragmatics (wide latitude) — expert judgment |
| Create | Synthesis | "Given the reliability issues, here's what you should do instead..." | Model reasoning WITH pragmatics |

## The Key Insight

RAG retrieves across ALL Bloom levels indiscriminately — it doesn't know whether a 
chunk is a fact (Remember) or a judgment call (Evaluate). The embedding space doesn't 
encode cognitive complexity.

Pragmatics are specifically curated at the Analyze/Evaluate levels — the levels where:
- Training data is least reliable (expert judgment isn't well-represented in corpora)
- The fitness-for-use question lives
- Errors have the highest downstream impact
- The stochastic tax of imprecise retrieval is most costly

The lower Bloom levels (Remember, Understand) are where the model's training data is 
strongest. You don't need pragmatics to tell the model what B01003_001E means — it 
already knows. You need pragmatics to tell it when NOT to trust the number it just 
retrieved.

## Where This Framing Appears

Thread this through:

### Paper §1 Introduction
- Frame the semiotic gap (syntax/semantics/pragmatics) in terms of Bloom levels
- Agencies have made data AI-ready at Remember/Understand levels
- The gap is at Analyze/Evaluate — expert judgment about fitness-for-use

### Paper §2 Semantic Smearing
- Smearing happens because the model conflates Bloom levels — it treats a Remember-level 
  fact (the number) with Evaluate-level confidence (whether to trust it)
- The model doesn't distinguish between "I know this fact" and "I can judge this fact"

### Paper §3 Pragmatics
- Latitude maps to Bloom complexity:
  - `none` latitude = Apply level (hard rules, no judgment needed)
  - `narrow` latitude = Analyze level (strong consensus, recognizable exceptions)
  - `wide` latitude = Evaluate level (genuinely context-dependent expert judgment)
  - `full` latitude = Remember/Understand (background context)
- This isn't accidental — it reflects the epistemological structure of expert knowledge

### Paper §5 Extraction Pipeline
- The extraction pipeline is a Bloom-level filter: source documents contain all levels, 
  the curation process selects for Analyze/Evaluate, the latitude assignment encodes 
  which level each item operates at

### Paper §6 Evaluation Design
- The CQS rubric dimensions map to Bloom levels:
  - D1 (source selection) = Apply
  - D2 (methodology) = Analyze/Evaluate
  - D3 (uncertainty) = Evaluate
  - D4 (definitions) = Understand
  - D5 (reproducibility) = Apply
- Pragmatics should show largest effects on D2/D3 (the Evaluate-level dimensions)

### Paper §8 Discussion
- "Wisdom" framing: Bloom's highest levels ARE evaluation and synthesis
- Pragmatics encode expert judgment at these levels — not wisdom in the philosophical 
  sense, but the top of the cognitive taxonomy applied to a specific domain
- This is why 35 curated items outperform 311 retrieved chunks: the 35 are selected 
  for the Bloom levels where the model is weakest and the stakes are highest
- The retrieval quality hierarchy (RAG → GraphRAG → Pragmatics) maps to Bloom-level 
  targeting: RAG is level-agnostic, GraphRAG is structurally aware but not 
  cognitively targeted, pragmatics are specifically curated for Analyze/Evaluate

### Slides
- One slide: Bloom pyramid with Census examples at each level, highlight the 
  Analyze/Evaluate gap. {slides:main}
- Use "knowledge representation study" language — we're studying which representation 
  best delivers Analyze/Evaluate level knowledge to a reasoning model

### FCSM Q&A Prep
- "How is this different from RAG?" → RAG retrieves at all Bloom levels indiscriminately. 
  Pragmatics are curated specifically for the levels where the model needs help most.
- "Why not just better RAG?" → Better retrieval doesn't solve the curation problem. 
  You can retrieve the right chunk and still miss the expert judgment that isn't in 
  any document.
- "How do you scale?" → The evaluation pipeline identifies which Bloom-level gaps 
  matter most. You scale by filling Analyze/Evaluate gaps ranked by measured impact.

## Terminology Note

Use "knowledge representation study" not "ablation study" for FCSM audience. The Bloom 
framing makes this natural — we're studying which representation of domain knowledge 
best supports expert-level reasoning by an AI system. That's a cognitive science 
question, not an ML hyperparameter sweep.
