# Pragmatics Gap Detection — Evaluation as Improvement Sensor

**Date:** 2026-02-16
**Section relevance:** Paper §8 Discussion, §10 Future Work
**Tags:** {paper} {slides:backup}

## Insight

The evaluation pipeline is not just a measurement system — it's a continuous 
improvement sensor for the pragmatics catalog. Every query where:

1. `get_methodology_guidance` returns empty or irrelevant guidance
2. The model calls with topics that don't match any pragmatic items
3. The response quality is low DESPITE grounding (pragmatics gap, not model gap)

...identifies a specific hole in the curated expert judgment catalog.

## Why This Matters

Because we have full traceability — query → topic selection → guidance returned → 
response produced → judge score — we can trace quality failures back to their root 
cause. A low D3 (uncertainty communication) score on a pragmatics response where the 
model called `get_methodology_guidance` with topic "dollar_values" but got nothing 
back tells you: we need a pragmatic item about inflation adjustment.

This is the opposite of the typical ML improvement cycle where you retrain on more 
data and hope. Here you have a specific, traceable, actionable gap: this query needed 
this guidance and we didn't have it.

## Reusable Benchmarking Utility

The test battery + judge pipeline is reusable and scalable as a benchmarking system.
Each new set of pragmatics packs added to the catalog can be measured against the 
same battery. Performance tracked over time as the catalog grows:

- 35 ACS items → baseline scores
- Add CPS pack → rerun battery with CPS queries → measure delta
- Add SIPP pack → same
- Each pack addition has a measurable before/after on the same benchmark

The 35 items are ACS-only for this study. CPS pragmatics exist in the system but 
aren't exercised by the current test battery. Expanding the battery to include 
CPS/SIPP queries tests cross-survey performance with the same pipeline.

## Reducing the Stochastic Tax

We validated deterministic retrieval behavior in the pragmatics system — the same 
query with the same topics returns the same guidance every time. This is reducing 
the stochastic tax where we can control or account for it. The remaining variance 
is in model reasoning, which is the part we WANT to be flexible.

RAG and GraphRAG are meant to "ground the model" and they do — at a cost. But 
consider the retrieval quality hierarchy:

- **RAG:** Retrieves by semantic similarity. In homogeneous domains like Census 
  methodology, embeddings can't differentiate between chunks that are semantically 
  close but contextually distinct. Retrieval is stochastic — similar queries may 
  get different chunks depending on embedding noise. No curation, no quality gate.
  
- **GraphRAG / Knowledge Graphs:** Retrieves by relationship traversal. Better 
  structural precision than flat RAG, but "if not done right, how do you know?" 
  The graph encodes whatever was extracted — including extraction errors, missing 
  relationships, and uncurated noise. The traversal is deterministic given the 
  graph, but the graph itself may be wrong. No fitness-for-use judgment.

- **Pragmatics:** Retrieves curated expert judgment. Deterministic. Each item has 
  been examined for correctness, bias, safety, and fitness-for-use. Provenance is 
  traceable to source documents with page-level citations. Latitude encodes 
  calibrated uncertainty. The catalog is transparent — you can read every item, 
  audit every claim, challenge every judgment.

RAG and GraphRAG optimize for retrieval coverage. Pragmatics optimize for retrieval 
quality. They're solving different problems. RAG asks "what's relevant?" Pragmatics 
asks "what does the expert think you need to know right now?"

## Tacit Knowledge Capture

This connects to a persistent challenge in knowledge management: capturing expert 
tacit knowledge. Organizations have whined about this for decades. Pragmatics offer 
a concrete mechanism:

- **Automated candidate extraction:** LLM-assisted extraction from source documents 
  identifies candidate items (what the documents say)
- **Expert SME capture:** A structured interview/review process where the expert 
  adds judgment that ISN'T in the documents — the fitness-for-use assessments, the 
  "I wouldn't trust that estimate because..." wisdom that lives in their head
- **Curation as quality gate:** Every item is reviewed, given a latitude, cited to 
  sources. This is what makes it trustworthy — not the volume, but the review

The word "wisdom" may be a stretch, but the direction is right. Pragmatics capture 
the layer between "knowing the facts" (data, documents) and "knowing what to do with 
the facts" (expert judgment). That's the layer that's hardest to encode and most 
valuable to deliver.

## Scaling Implications

At scale (hundreds or thousands of queries beyond the 39-query battery):
- Cluster the topic requests that return empty/low-relevance guidance
- Rank gaps by frequency and judge score impact
- Prioritize new pragmatic items by measurable quality improvement potential
- The catalog grows based on empirical demand, not expert guesswork

This turns the 35-item catalog into a living system that improves based on where it 
actually fails, with measurements at every step.

## Connection to Extraction Pipeline

Gap detection feeds directly into the quarry extraction pipeline:
- Identified gap → search source documents for relevant content
- Extract → curate → add to catalog → rerun affected queries → measure improvement
- Each new pragmatic item has a measurable before/after on real queries

The same pipeline that built the initial 35 items scales to fill gaps discovered 
through evaluation.

## For FCSM Narrative

This addresses the scalability critique head-on. "How do you scale beyond 35 items?" 
Answer: the evaluation system tells you exactly which items to build next, ranked by 
impact. You don't need to boil the ocean — you need to fill the gaps that matter most, 
and the system identifies them automatically with full traceability from query to gap 
to fix to measured improvement.

The determinism point is the kicker: every other grounding approach introduces its own 
stochastic noise into the system. Pragmatics reduce noise at the grounding layer so 
the only remaining variance is in the reasoning — which is where you want flexibility.
