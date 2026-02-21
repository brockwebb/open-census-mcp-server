# RAG and GraphRAG Cost/Performance Landscape

## Positioning for Paper
NORC measures the disease. We have the treatment. But we also need to show why the "obvious" treatments (RAG, GraphRAG) are more expensive and less effective in this domain.

## Framing
- NORC/NSF: diagnosing the pathology (how wrong are LLMs on statistical data?)
- RAG/GraphRAG: expensive treatments with side effects
- Pragmatics: targeted intervention — cheaper, more effective, deterministic

## Cost Benchmarks (from literature)

| Component (Monthly, 100K docs/10K queries) | RAG | GraphRAG |
|---|---|---|
| Vector DB | $70 | $70 |
| Graph DB | — | $65 |
| LLM (e.g., Claude Sonnet) | $200 | $280 |
| Compute | $50 | $120 |
| **Total** | **$320** | **$635** |

- GraphRAG ~2× monthly infrastructure cost of RAG for similar workloads
- Per-query: ~$0.023 (RAG) vs ~$0.034 (GraphRAG) — driven by ~40% more LLM tokens
- Annual TCO estimates: $127K–$205K range (1TB data, 10K daily queries)
- GraphRAG retrieves ~47K tokens vs ~3.7K for top-5 RAG — massive overhead

## Performance vs No Retrieval
- RAG: F1 from ~0.48 (no context) to 0.52+ with retrieval
- GraphRAG matches or exceeds RAG but retrieves far more tokens without proportional gains on simple tasks
- Groundedness: RAG 57% → GraphRAG 86% (+29%), especially multi-hop (+35%)
- Enterprise target: >0.85 faithfulness

## Our Numbers for Comparison
- Pragmatics: $0.09/query marginal (Sonnet), $0.14 (Opus) — COST-003, COST-012
- Full 39-query battery: $4.42 (Sonnet) — COST-002
- NO vector DB, NO graph DB at runtime, NO embedding model dependency
- Runtime is a SQLite file read. Infrastructure cost: effectively zero.
- 2.2× more cost-effective than RAG per CQS point gained — COST-005

## The Argument
GraphRAG costs 2× RAG. RAG costs 196% more than baseline for a medium effect (d=0.546). Pragmatics costs 38% more than RAG for a large effect (d=0.922). And pragmatics has zero runtime infrastructure — no vector DB, no graph DB, no embedding model. The authoring cost is front-loaded; the delivery cost is negligible.

The point isn't that RAG and GraphRAG don't work. It's that for domain-homogeneous corpora like Census methodology, the retrieval problem is misdiagnosed. You don't need better retrieval. You need better judgment. And judgment is cheaper to deliver than retrieval.

## Citations Needed
- GraphRAG cost benchmarks: cognilium source (need proper citation)
- GraphRAG performance: arxiv sources (need proper citation)
- NVIDIA developer eval: developer.nvidia source (need proper citation)
- Ethayarajh 2019 for anisotropy mechanism
- Our own: COST-001–013, S2-010–012

## Status: RAW MATERIAL
