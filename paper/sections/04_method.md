# Section 4: Method

<!-- Registry references: SD-001–010, PL-001–004, RAG-001–007, EXT-001–010, DET-001–004, DRV-001–004 -->
<!-- Existing section: 05_extraction_pipeline.md (subsume relevant parts) -->

## 4.1 Study Design

We conducted a knowledge representation study comparing three experimental conditions with identical data tool access. The single independent variable was the form of methodology support provided to the language model during statistical consultation. All three conditions used the same caller model (Claude Sonnet 4.5), the same Census Bureau API tools, and the same 39-query test battery. The conditions differed only in how domain knowledge was represented and delivered:

> **[INSERT FIGURE F5: Three-condition experimental design: control/RAG/pragmatics with shared data tools, varying methodology support]**

- **Control:** The model received Census API tools with no methodology support. This represents the baseline capability of a capable language model performing statistical consultation with data access but no expert guidance.

- **RAG (Retrieval-Augmented Generation):** The model received Census API tools plus retrieved document chunks from authoritative source material. For each query, the top five most similar chunks were retrieved from a FAISS index (IndexFlatIP, cosine similarity) using the all-MiniLM-L6-v2 embedding model (384 dimensions) over 311 chunks extracted from three Census Bureau publications.

- **Pragmatics:** The model received Census API tools plus curated expert judgment delivered through a methodology guidance tool. For each query, the system performed a deterministic graph traversal to retrieve relevant pragmatic context items from a compiled pack of 36 curated items.

The three source documents were identical across the RAG and pragmatics conditions: the ACS General Handbook 2020 (89 pages), the ACS Design and Methodology Report 2024 (238 pages), and the ACS Geography Handbook 2020 (27 pages), totaling 354 pages. RAG indexed all three as 311 chunks. Pragmatics drew 36 curated items from the same sources: 34 through pipeline extraction and 2 through manual expert review. The independent variable was representation method, not source material.

Tool access was controlled through distinct tool configurations for each condition. The control and RAG conditions were explicitly denied access to the methodology guidance tool, verified post-hoc through tool call auditing. The pragmatics condition included a grounding gate requiring consultation of methodology guidance before interpreting any data, verified at 100% compliance across all 39 queries.

## 4.2 Test Battery

The test battery comprised 39 queries stratified into 15 normal queries (38%) and 24 edge cases (62%). The stratification was derived from a power analysis: paired Wilcoxon signed-rank tests at a target effect size of d = 0.5, significance level α = 0.05, and power = 0.80 require approximately 35 pairs. The battery was stratified to provide sufficient power for both equivalence testing on normal queries (where pragmatics should not harm performance) and superiority testing on edge cases (where pragmatics value-add was hypothesized to concentrate).

Edge cases were drawn from seven categories reflecting known failure modes in statistical consultation: geographic edge cases (7 queries), small-area reliability concerns (4), temporal comparison issues (4), ambiguous requests (3), product mismatches (3), and persona-varied queries (3). This distribution weighted the battery 80% toward challenging scenarios where fitness-for-use judgment is most critical, consistent with the hypothesis that pragmatics address judgment gaps rather than knowledge gaps.

## 4.3 Pragmatics Extraction Pipeline

The 36 pragmatic items were produced through two extraction pathways from the same source documents used by the RAG condition.

**Pipeline extraction** produced 34 items. Source documents were processed through section-aware chunking, yielding structured text segments passed through LLM-based extraction to populate a knowledge graph of 5,233 nodes. From this graph, pragmatic items were harvested through pattern-matching against the FCSM 20-04 quality framework, then curated by a domain expert who assigned latitude levels, retrieval triggers, thread edges, and provenance citations. The extraction yield was 0.65%: each surviving item encodes a specific fitness-for-use judgment, stripped of the surrounding exposition that dilutes signal in chunk-based retrieval.

**Manual extraction** produced 2 items through human-AI collaborative review of source material. The Geography Handbook yielded zero usable items through the pipeline; this finding suggests that some expert judgment is implicit in how practitioners use documents rather than explicit in any single passage. The two manually extracted items (geographic hierarchy judgment and group quarters classification) required structured conversation between a domain expert and an AI assistant to articulate tacit knowledge that documents do not state directly.

The authoring-to-runtime pipeline implements strict separation of concerns. Items are authored in a graph database, exported to version-controlled JSON staging files, validated against a canonical schema, and compiled to a SQLite database: the deployable pack that the server loads at runtime. The runtime system has no dependency on the graph database, extraction pipeline, or authoring workflow.

## 4.4 Evaluation Pipeline

Evaluation proceeded through three stages.

> **[INSERT FIGURE F6: Evaluation pipeline: Stage 1 (response generation), Stage 2 (CQS scoring), Stage 3 (fidelity verification)]**

**Stage 1 (Response Generation)** produced 117 responses: 39 queries across 3 conditions. Each query was processed by the caller model with the condition-specific tool configuration, producing a complete statistical consultation response.

**Stage 2 (Consultation Quality Scoring)** assessed response quality through pairwise comparison using three independent judge models (Anthropic Claude, OpenAI GPT, Google Gemini). Each pair of conditions was evaluated across five quality dimensions: accuracy of statistical claims (D1), completeness of relevant information (D2), appropriate communication of uncertainty (D3), clarity of explanation (D4), and avoidance of potentially harmful misinterpretation (D5). Each comparison was scored by all three judges in both presentation orders, yielding six passes per comparison. This produced 2,106 total judge records (39 queries × 3 comparisons × 3 judges × 2 orderings) with zero parse failures.

Quality dimensions were scored on a three-point scale (0, 1, 2) where 0 indicates the first response is clearly better, 1 indicates a tie, and 2 indicates the second response is clearly better. Scores were normalized to a [-1, +1] scale for analysis, with positive values indicating the second-listed condition performed better.

**Stage 3 (Pipeline Fidelity Verification)** assessed whether responses accurately reported what Census API tools returned. An automated verification system extracted factual claims from each response and traced them to specific API calls, checking whether cited estimates, margins of error, geographic entities, and variable codes matched the actual tool responses. This stage measured auditability (whether claims could be verified at all) and fidelity (whether verified claims were accurate).

## 4.5 Statistical Analysis

Composite Consultation Quality Scores (CQS) were computed as the mean across five dimensions for each query-comparison-pass combination, then averaged across the six passes to produce a single score per query per comparison.

Omnibus differences were tested using the Friedman test for related samples. Pairwise comparisons used Wilcoxon signed-rank tests with Holm-Bonferroni correction. Effect sizes were computed as Cohen's d from the paired differences. Bootstrap confidence intervals (10,000 iterations) provided uncertainty estimates for mean differences. Stratum-level analyses tested whether effects differed between normal and edge case queries using permutation tests on the difference-of-differences.

The evaluation design aligns with the NIST AI Risk Management Framework's [@nist2023airm] Test, Evaluation, Verification, and Validation (TEVV) methodology. A crosswalk mapping CQS dimensions to FCSM 20-04 quality characteristics and NIST AI RMF trustworthiness properties is available as a separate publication [@webb2026crosswalk].

