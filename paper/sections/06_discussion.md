# Section 6: Discussion

<!-- Registry references: S2-010–012, S2-032, SA-001–022, COST-001–013, EFF-001–008, DET-001–004 -->
<!-- Citation files: core_argument.md, stochastic_tax_framing.md, rag_graphrag_cost_comparison.md, d3_uncertainty_deep_dive.md -->

## 6.1 Selectivity Beats Volume

The central empirical finding is that 36 curated expert judgment items outperform 311 document chunks retrieved from the same source material, with a large effect size (d = 0.922) and a 16.6 percentage point fidelity advantage. Both conditions drew from the same 354 pages of Census Bureau documentation. The difference is entirely in how that knowledge was represented and delivered.

This result instantiates a broader principle: information selectivity at inference time follows the same pattern as training data curation. The machine learning community has established that curated, high-quality training datasets outperform larger, noisier corpora; data quality matters more than data volume for what a model learns. The same principle operates at every layer of the AI stack. Curating training data reduces variance in what a model learns. Curating reasoning traces (as in chain-of-thought distillation for inference-time reasoning models) reduces variance in how a model reasons. Curating expert judgment at the point of decision, as pragmatics does, reduces variance in how a model consults. Each is the same insight, applied at a different stage of the pipeline: precision of signal outperforms volume of context. What this study contributes is the empirical demonstration that the selectivity principle extends to inference-time expert knowledge, a layer that existing AI architectures have addressed primarily through retrieval volume rather than judgment curation.

The extraction yield (34 pipeline-extracted items from 5,233 knowledge graph nodes, a 0.65% retention rate) is not a limitation to be overcome through automation. It is the mechanism. Each reduction step in the pipeline (source documents → graph nodes → harvested candidates → curated items) removes content that is semantically related but pragmatically irrelevant. The final 36 items represent the distilled judgment that a senior statistician would actually provide at the point of data interpretation, stripped of the exposition, background, and procedural detail that constitutes the majority of methodology documentation.

The D3 (uncertainty communication) results provide the clearest illustration. This dimension showed the largest effect across all five quality dimensions (d = 1.353 vs. control, d = 1.040 vs. RAG) because it depends most directly on fitness-for-use judgment. RAG can retrieve a passage explaining what a margin of error is. Pragmatics deliver the specific judgment that *this* margin of error renders *this* estimate unreliable for *this* use case. The distinction between retrieving information about uncertainty and delivering judgment about uncertainty is the distinction between semantics and pragmatics.

## 6.2 Reducing the Stochastic Tax

Every AI system built on language models pays a stochastic tax: variance at every stage of the pipeline that cannot be eliminated because the underlying generation mechanism is non-deterministic. The practical question is not whether variance exists but where it accumulates and how much of it is avoidable.

RAG and GraphRAG systems compound variance at two stages. Retrieval is stochastic: embedding similarity is approximate, and the same query can return different chunks depending on model version, index state, and numerical precision. Generation is stochastic: the same context can produce different outputs. When both stages vary, the compounding effect produces inconsistent grounding for inconsistent reasoning.

Pragmatics eliminates one source of this compounding. Context retrieval is deterministic: a graph traversal that returns identical results every time, verified at 100% across all 39 queries and two independent replications. The model's reasoning over those items remains stochastic, as it must in any language model system. But the grounding is fixed. The variance is isolated to one stage rather than compounding across two.

For federal statistical consultation, this distinction matters practically. The difference between a one-year and five-year estimate, or between a 20% and 40% coefficient of variation, determines whether an answer is useful or harmful. Stochastic retrieval in a domain where all the documentation sounds alike (where anisotropy and domain homogeneity collapse the embedding space) means the grounding itself is unreliable. Deterministic delivery of curated judgment eliminates this failure mode.

## 6.3 The Sidecar Architecture

The empirical results establish that curated expert judgment improves statistical consultation quality. The delivery architecture determines whether that improvement is practically deployable.

Pragmatics are served as a server-side API resource. When a client model requests methodology guidance, the server performs a deterministic graph lookup, bundles the relevant context items, and returns them alongside the Census data response. The client receives expert judgment as structured data in the same response envelope as the statistical estimates. No client-side infrastructure is required: no vector database, no embedding model, no index to build or maintain.

This sidecar pattern inverts the cost structure of retrieval-based approaches. RAG requires each client to maintain its own chunked index: acquiring source documents, choosing a chunk strategy, embedding with a specific model, hosting a vector store, and re-indexing when any component changes. GraphRAG adds a graph database and approximately doubles the monthly infrastructure cost. Both approaches scale infrastructure linearly with the number of clients.

Pragmatics concentrates the authoring cost (one expert curates the pack) and distributes the benefit through a negligible-cost API call. Domain experts update the pack centrally; all clients benefit immediately. The runtime cost is a SQLite file read. As input token costs decline across model generations, the absolute cost of delivering expert judgment decreases while the quality advantage, which is structural rather than cost-dependent, remains stable.

The evaluation provides an unintentional test of vendor independence. Three judge models from three vendors (Anthropic Claude, OpenAI GPT, Google Gemini) all consumed pragmatic context through the same interface and consistently scored pragmatics-assisted responses higher. Any system that can receive structured context, regardless of the reasoning model behind it, benefits from the same expert judgment. This decouples the expertise from the model, allowing agencies to change model vendors without rebuilding their expert judgment infrastructure.

## 6.4 Implications for Federal Statistical Agencies

Making federal data AI-ready requires three investments: refactoring how data is exposed to AI systems, accelerating metadata curation, and encoding the expert judgment needed to evaluate fitness for use. The first two are underway across federal statistical agencies. The third is not.

The pragmatics concept does not compete with existing efforts. Continued investment in machine-readable formats, structured APIs, and rich metadata is essential; these ensure that syntax and semantics continue to be available in model training data and through programmatic access. Pragmatics complement this infrastructure by adding the layer that syntax and semantics cannot provide: the expert assessment of whether data is appropriate for a specific purpose.

The practical path forward involves packaging statistical expertise as a deliverable resource alongside data products. Not as documentation that users may or may not read, but as structured, machine-deliverable judgment that reaches the point of analysis automatically. The finding that 36 curated items from 354 pages of documentation produce a very large effect size suggests that the investment required is modest relative to the documentation that agencies already produce. The expert judgment exists. It lives in the professional practice of experienced statisticians. The task is to capture it, structure it, and deliver it computationally.

This is not a new obligation. The Federal Committee on Statistical Methodology's own data quality framework codifies characteristics that are fundamentally pragmatic: relevance, accuracy, timeliness, fitness for use. These have been the standard for decades. What pragmatics operationalizes is the delivery of this existing institutional knowledge through the channels where data consumers increasingly encounter federal statistics: AI-mediated analysis. A published crosswalk between FCSM 20-04 and the NIST AI Risk Management Framework provides a coordination tool for agencies navigating both quality and trustworthiness requirements simultaneously [@webb2026crosswalk].
