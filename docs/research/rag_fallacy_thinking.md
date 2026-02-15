# The RAG Fallacy: Why Retrieval ≠ Consultation

## Core Argument

The anticipated critique: "You hand-curated expert judgment into a graph. What if you just RAG'd the same source documents? Section-level chunks of the ACS Handbook with vanilla retrieval might produce similar improvements with 10% of the effort."

This fundamentally misunderstands what the system does.

## The Category Error

Every RAG variant — vanilla, HyDE, HyPE, GraphRAG, sentence-window, reranking — ultimately stuffs text chunks into context and hopes the model reasons correctly over them. Our system doesn't retrieve text. It retrieves pre-computed fitness judgments.

Example: "For Mercer PA at tract level, CV will exceed 30%, use 5-year, warn about reliability."

No RAG chunking strategy on the ACS Handbook will produce that sentence, because it's not in the handbook. It's the inference a statistician makes after reading the handbook, knowing the geography, and checking the population. RAG retrieves *information*. Pragmatics retrieve *judgment*.

## HyPE Parallel (and Divergence)

HyPE (Hypothetical Prompt Embeddings) pregenerates "what questions would this chunk answer?" and indexes by question-embedding. Pragmatics pregenerate "what judgment does this concept require?" and index by decision-point. Both shift work from query-time to index-time.

The difference: HyPE still retrieves document chunks as the answer. Pragmatics retrieve expert conclusions. HyPE is better plumbing for the same water. Pragmatics are a different water supply.

## The Bikeshedding Argument

The RAG technique zoo exists because retrieval is a lossy compression problem — you're trying to guess which 4K tokens out of 89 pages the model needs right now. Every technique is a different heuristic for that guess: better embeddings, hypothetical questions, graph structure, reranking.

But pragmatics sidestep the retrieval problem entirely by having a domain expert pre-identify the decision-relevant content and extract the judgment. We're not doing better retrieval. We're not doing retrieval at all. We're doing consultation.

If someone says "but you should have used HyPE / GraphRAG / reranking," the answer is: "Better retrieval would close some of the gap. But the gap between RAG-baseline and pragmatics is in *judgment quality*, not *retrieval precision*. The handbook chunk tells you MOEs exist. The pragmatic tells you this specific MOE makes this specific estimate unreliable for this specific use case. No chunking strategy bridges that."

## The Temporal Depreciation Asymmetry

RAG techniques depreciate. Expert judgment appreciates.

**RAG maintenance burden:**
- Every RAG technique is compensating for a model limitation (context window, attention, reasoning quality)
- As models evolve, the technique layer depreciates — what required HyPE with 8K context is unnecessary with 200K context
- You're constantly recompiling indexes, retuning chunk sizes, swapping embedding models, adjusting retrieval parameters
- Each model generation potentially invalidates your retrieval optimization — you're back to prompt tuning or something equivalent
- The RAG technique is tightly coupled to the model's current weaknesses

**Expert judgment durability:**
- Curated judgment is the *input*, not the *plumbing* — a better model reasons better over the same pragmatics
- Domain rules change slowly and *changes increase value* through temporal lineage
- Example: "The treatment of group quarters changed in 1985 because of X, so pre-1985 comparisons require Y adjustment"
- Example: "This variable was added in 2019 to capture Z, but before that analysts used W as a proxy — if comparing across vintages, be aware of the break in series"
- Example: "The MOE calculation methodology changed in 2006; pre-2006 standard errors are not directly comparable"
- These temporal annotations are *more valuable over time*, not less — they accumulate institutional knowledge that no document chunk contains because it spans multiple document versions
- A RAG system over the 2020 handbook loses the 2010 handbook's context. A pragmatics system preserves the lineage: "this concept was defined differently before, here's what changed and why it matters"

**The depreciation test:** If a new model with 1M context window launches tomorrow, does your system still add value?
- RAG: Probably not — just stuff the whole handbook in context
- Pragmatics: Yes — the model still doesn't know that Mercer PA's tract-level poverty estimates have CVs above 30%, or that comparing 2005 vs 2015 income requires the ACS methodology break adjustment. That's not in any document. It's synthesized judgment.

## The Semantic Smearing Insurance

The one risk to the pragmatics claim: if a frontier model can ingest the entire handbook and reason perfectly over it, pragmatics become "merely" a performance optimization (faster, cheaper, same quality).

Insurance against this: the semantic smearing finding. Even with full documents in context, models conflate survey vintages, estimate types, and methodological boundaries. The 82% increase in mean similarity and 86.5% collapse in group discrimination with enriched metadata — validated across models — shows that larger models *amplify* rather than correct smearing. More context doesn't fix ambiguity in training data; it can make it worse.

Pragmatics aren't compensating for context limits. They're compensating for training-data ambiguity that persists (and worsens) regardless of context window.

## Proposed Ablation Experiment

To preempt the critique empirically:

| Condition | Description |
|-----------|-------------|
| Control | Bare LLM, no tools, no documents |
| RAG baseline | Section-level chunks of ACS Handbook, vanilla embedding, top-k into system prompt. Deliberately untuned. |
| Treatment | Full pragmatics via MCP tools |

Use the most boring vanilla RAG possible. Don't optimize it. The point isn't to show bad RAG loses — it's to show the *category* has a ceiling.

**Expected results:**
- RAG > Control on D4 (definitions) and maybe D2 (methodology) — handbook text helps with "what is" questions
- RAG ≈ Control on D3 (uncertainty) and D5 (reproducibility) — handbook doesn't contain specific MOEs or table IDs for specific queries
- Treatment >> RAG on D3 and D5 — these require fitness judgment, not information retrieval
- Treatment > RAG on D1 (source selection) — pragmatics encode which product fits which use case

If T2 > T1 > Control: curation adds value beyond retrieval (strongest claim)
If T1 ≈ T2: "we found RAG works for statistical consultation" (different but still publishable claim)
If T1 ≈ Control: documents alone don't help, curation is essential (validates the whole approach)

## The One-Liner

"RAG retrieves what the handbook says. Pragmatics retrieve what a statistician *concludes* after reading the handbook."
