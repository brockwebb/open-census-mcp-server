# The Stochastic Tax — Framing Note

## Core Concept
Every AI system built on stochastic models (LLMs) pays a "stochastic tax" — variance at every stage of the pipeline. The question isn't whether you pay it, but how much and where.

## RAG/GraphRAG: Compounding Variance
- Stochastic retrieval (embedding similarity, approximate nearest neighbor) × stochastic reasoning = variance compounds at both stages
- Every query: which chunks get retrieved varies, how the model interprets them varies
- Network/compounding effects: small retrieval variance cascades into large interpretation variance
- You're fighting entropy at every layer

## Pragmatics: Reduced Tax
- Deterministic retrieval (graph traversal, same result every time, 39/39 DET-001–004) × stochastic reasoning = variance isolated to one stage
- The grounding is fixed. The lighthouse doesn't move. The ship still navigates stochastically, but toward a stable signal.
- You can't eliminate the tax (entropy always wins, death and taxes), but you can reduce it by making one side of the pipeline deterministic

## The Stability Argument
- Historical Census data doesn't change. The judgments about fitness-for-use for historical estimates are stable.
- Updates happen (methodology changes, boundary revisions), but slowly — unlike RAG indexes that drift with embedding model versions, chunk strategy changes, index rebuilds
- Pragmatics items are curated once, stable for the life of the data they describe
- RAG/GraphRAG fight entropy continuously. Pragmatics front-load the curation cost and then sit stable.

## The Tacit Knowledge Connection
- The real compounding problem: capturing tacit knowledge from senior statisticians
- That expertise doesn't change with model versions or embedding drift
- It DOES have network effects — each judgment item builds on and connects to others (thread structure)
- Building on the age-old knowledge management problem: how do you capture what experts know but can't articulate from documents alone?
- Pragmatics is one answer: structured, auditable, deterministic delivery of captured expert judgment

## Paper Framing
- NOT: "pragmatics is better than RAG" (too simplistic)
- YES: "pragmatics reduces the stochastic tax by making grounding deterministic, front-loading curation cost, and delivering stable expert judgment for stable data"
- The honest version: reasoning is still stochastic, but you've eliminated one source of compounding variance

## The TCO Argument
- Yes, pragmatics costs MORE per query than RAG ($0.113 vs $0.082 at Sonnet — COST-001)
- But the HIDDEN costs of RAG/GraphRAG dwarf the per-query delta:
  - Vector DB hosting ($70/mo)
  - Graph DB hosting ($65/mo for GraphRAG)
  - Embedding model dependency (version lock-in, re-embedding on upgrades)
  - Index maintenance (re-chunk, re-embed when source docs update)
  - Chunk strategy tuning (ongoing engineering cost)
  - Infrastructure monitoring, scaling, failure modes
- Pragmatics runtime: ONE extra API call returning a SQLite lookup. Sidecar onto existing data API.
- No vector DB. No graph DB at runtime. No embedding model. No index.
- The authoring cost (curation) is real but front-loaded and amortized across all queries forever
- Maintenance: update when methodology changes (rare for historical data). Not when models change.
- TCO delivers better value AND better performance (2.2× more cost-effective per CQS point — COST-005)

## The Honest Cost Story for the Paper
- Per-query: pragmatics is ~38% more expensive than RAG (tokens)
- Infrastructure: pragmatics is essentially free (SQLite file read)
- Quality: pragmatics is 2.2× more cost-effective per unit of quality improvement
- Maintenance: pragmatics is stable for stable data; RAG requires continuous infrastructure
- Total cost of ownership: pragmatics wins and it's not close

## Status: RAW MATERIAL
