# Section 5: Extraction Pipeline — From Source Documents to Pragmatic Context

<!-- GAP-013: Methods narrative covering dual extraction paths, determinism, curation process -->
<!-- Registry references: EXT-001–010, DET-001–004, PL-001, RAG-004–005 -->

## 5.1 Source Material and Fair Comparison

Both the RAG and pragmatics conditions draw from the same three authoritative source documents: the ACS General Handbook 2020 (89 pages), the ACS Design and Methodology Report 2024 (238 pages), and the ACS Geography Handbook 2020 (27 pages), totaling 354 pages (EXT-001, EXT-008). This was a deliberate design choice — the independent variable is knowledge representation method, not source material. RAG indexes all three documents as 311 chunks for brute-force top-5 cosine retrieval (RAG-004). Pragmatics distills the same source material into 36 curated context items delivered via structured graph traversal (PL-001).

## 5.2 Dual Extraction Paths

The 36 pragmatic items were produced through two distinct extraction pathways, each addressing a different form of expert knowledge.

**Pipeline extraction** produced 34 of the 36 items. Source documents were processed through a section-aware chunking pipeline (Docling), yielding structured text segments that were then passed through LLM-based extraction to populate a knowledge graph (the "quarry"). The quarry accumulated 5,233 nodes from the Handbook and Design & Methodology documents (EXT-009). From this raw graph, pragmatic items were harvested through pattern-matching against the FCSM 20-04 quality framework, then curated by a domain expert who assigned latitude levels, retrieval triggers, thread edges, and provenance citations. The extraction yield was 0.65% — 34 items from 5,233 nodes (EXT-010). This severe reduction is not a limitation; it is the mechanism. Each surviving item encodes a specific piece of fitness-for-use judgment that a senior statistician would provide at the point of data interpretation, stripped of the surrounding exposition that dilutes signal in chunk-based retrieval.

**Manual extraction** produced the remaining 2 items through human-AI collaborative review of source material (EXT-003). The Geography Handbook, despite containing 27 pages of content relevant to geographic hierarchy and boundary changes, yielded zero usable items through the pipeline. This is itself a finding: the geographic judgment that practitioners need — when nesting assumptions break, which geographic levels are comparable across years, how to handle entity boundary changes — is implicit in how statisticians *use* geographic data, not explicit in any single passage of the handbook. The manually extracted geography item (ACS-IND-001) and group quarters item (ACS-GQ-001) required a different elicitation method: structured conversation between a domain expert and an AI assistant, reviewing the source material and articulating the tacit judgment that practitioners apply but documents do not state directly.

These two extraction paths reflect a broader methodological principle. Pipeline extraction operates *document-forward*: an expert reads source material, identifies judgment, and encodes it with provenance citations. Manual extraction operates *failure-forward*: the system is run against test queries, structural failures in statistical interpretation are identified, and a domain expert provides the judgment that would have corrected the failure, tracing it back to authoritative sources. The failure-forward path is how the pragmatics collection grew in practice — evaluation runs surfaced interpretation gaps that no single reading of the documentation would have anticipated, because the gaps emerge only at the intersection of a specific query and a specific data context. This dual authoring model has implications for scalability beyond the expert validation discussed in Section 7.2: a mature pragmatics ecosystem can operate as a continuous improvement loop in which deployed systems generate failure signals, domain experts provide corrective judgment, and the pack grows through empirical observation rather than exhaustive document review alone.

This dual-path finding has implications for scaling. A mature pragmatics authoring system requires both paths: automated pipeline extraction for explicit knowledge stated in documents, and structured expert interviews for tacit knowledge that lives in practitioner experience. The two manually extracted items serve as proof-of-concept for the Phase 2 expert validation pathway, where structured interviews with Census methodology specialists will elicit additional tacit knowledge items.

## 5.3 Determinism by Design

A defining architectural property of the pragmatics retrieval layer is determinism. Given identical topic parameters, the system returns identical context sets on every invocation. This was verified empirically: across two independent replications plus the original Stage 1 run, all 39 queries produced identical context retrievals — zero mismatches (DET-001–004).

Determinism is not a tuned property; it is a structural consequence of the retrieval mechanism. Pragmatic context is retrieved through graph traversal: a query's topic maps to a thread identifier, which traverses defined edges to collect the relevant context nodes. There are no embedding computations, no approximate nearest-neighbor searches, no stochastic sampling. The path from topic to context is a deterministic function.

This contrasts with RAG retrieval, where the same query can return different chunks depending on embedding model version, index state, and the inherent approximation in cosine similarity over high-dimensional spaces. In semantically homogeneous domains like Census methodology — where documents about poverty estimation, income thresholds, and sampling methodology occupy overlapping regions of embedding space — this stochasticity is not merely theoretical. It is the mechanism underlying semantic smearing: the retrieval system cannot reliably distinguish between chunks that are semantically similar but contextually distinct.

The pragmatics system eliminates this failure mode by replacing similarity search with curated graph structure. The curation cost is paid once, at authoring time. At query time, retrieval is a O(1) graph lookup with zero variance.

## 5.4 The Curation Process

Curation is the core intellectual contribution of the pragmatics approach — not as methodology, but as the specific act of exercising expert judgment about what information matters at the point of statistical reasoning.

Each of the 36 items in the ACS pack underwent a structured curation process. Starting from a harvested knowledge graph node, the domain expert assigned five properties that transform raw information into actionable expert judgment:

- **Context text** (1–3 sentences): The specific fitness-for-use judgment, written as factual context rather than as an instruction or constraint. Example: "When the coefficient of variation exceeds 40%, the estimate is considered unreliable for most analytical purposes."

- **Latitude** (none / narrow / wide / full): Calibrated uncertainty over the judgment itself. A `none`-latitude item represents hard consensus — no reasonable expert disagrees. A `wide`-latitude item acknowledges that practitioners legitimately diverge on the correct interpretation. This is not metadata decoration; it gives the consuming model explicit permission to exercise judgment within defined bounds.

- **Triggers** (3–6 keywords): Retrieval activation terms that connect the item to query contexts where it is relevant. Triggers are authored to reflect how practitioners describe problems, not how documents index topics.

- **Thread edges**: Links to related context items that a user might need in the same analytical session. Thread structure enables retrieval of coherent judgment bundles rather than isolated facts.

- **Provenance** (document, section, page): Verifiable citation to the authoritative source, enabling audit of every judgment claim back to its documentary basis.

This curation process is what GraphRAG systems attempt to automate through community detection and summarization over extracted knowledge graphs. The pragmatics approach does this work by hand, trading scalability for precision. The tradeoff is justified by the empirical results: 36 hand-curated items outperform 311 automatically chunked passages from the same source material, with a Cohen's d of 0.922 (S2-011) and a 16.6 percentage point fidelity advantage (DV-005). The curation process — the 0.65% yield — is not a bottleneck to be automated away. It is the intelligence.

## 5.5 Compilation Pipeline

The authoring-to-runtime pipeline implements a strict separation of concerns (ADR-001). Pragmatic items are authored in a Neo4j graph database, where the graph structure supports iterative refinement of thread edges and relationship exploration. Authored items are exported to version-controlled JSON files in a staging directory, organized by domain and category (18 files for the ACS pack). A compilation script validates all items against the canonical Pydantic schema and produces a SQLite database — the deployable "pack" — that the MCP server loads at startup.

This pipeline means the authoring environment (graph database, expert curation tools, extraction pipelines) is entirely decoupled from the runtime environment (SQLite file served via MCP). The MCP server has no dependency on Neo4j, no dependency on the extraction pipeline, and no dependency on the authoring workflow. It reads a SQLite file. This architectural simplicity is deliberate: the complexity belongs in the authoring pipeline, not in the production system that serves expert judgment at query time.
