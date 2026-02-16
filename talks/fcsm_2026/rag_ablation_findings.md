# RAG Ablation Findings: Strategic Implications

## Date: 2026-02-15
## Context: Post three-group analysis discussion

---

## The "So Fucking What" Test

### Raw Numbers
- 35 ACS pragmatics (hand-curated expert judgments from 3 source documents)
- 311 RAG chunks (blind extraction from same 3 documents)
- Control: bare LLM, no augmentation

### Three-Group Results (0-2 scale)
| Dimension | Control | RAG | Pragmatics |
|-----------|---------|-----|------------|
| D1 (Data Selection) | 1.13 | **1.80** | 1.58 |
| D2 (Geographic) | 0.61 | 1.31 | **1.52** |
| D3 (Uncertainty) | 0.39 | 1.09 | **1.55** |
| D4 (Soundness) | 1.20 | 1.63 | **1.78** |
| D5 (Fitness) | 0.54 | 1.29 | **1.62** |
| Composite | 0.77 | 1.43 | **1.61** |

### Fidelity
| Metric | Control | RAG | Pragmatics |
|--------|---------|-----|------------|
| Fidelity | N/A | 64.9% | 91.6% |
| Mismatches | N/A | 0 | 1.6% |

---

## The Bloom's Taxonomy Framing

RAG operates at Level 1 (Remember): "Here's what the handbook says about MOEs."

Pragmatics operate at Level 5 (Evaluate): "This specific estimate has a CV 
that makes it unreliable for your use case. Use this instead."

**The D1 anomaly proves this.** RAG scores HIGHER on data selection (1.80 vs 
1.58) because it dumps more recalled information into the response. More 
information ≠ better decisions. Knowledge recall is the lowest level of 
thinking. The hard dimensions — D3 (uncertainty quantification) and D5 
(fitness-for-use) — require judgment and synthesis. That's where pragmatics 
pull ahead, and that's where getting it wrong causes actual harm.

The utility of information without judgment is limited. A 500-page handbook 
in your context window doesn't help if you don't know which paragraph matters 
for THIS query. RAG gives you information. Pragmatics give you judgment 
about that information.

---

## The Expert Knowledge Argument

The most valuable pragmatics are NOT found in any document. They are locked 
in the heads of expert statisticians and data scientists. Examples:

- "Don't compare 1-year and 5-year estimates directly" — this is in the 
  handbook, but the JUDGMENT about when users try to do it anyway and how 
  to redirect them is expert knowledge
- "For Mercer County PA, the CV on poverty estimates exceeds 30%" — no 
  document says this. An experienced analyst KNOWS this from working with 
  the data. A pragmatic encodes that judgment permanently.
- "St. Louis is an independent city, not in a county" — geographic edge 
  cases that every Census analyst learns the hard way

Pragmatics are an opportunity to CODIFY expertise and judgment that would 
otherwise be lost to retirement, turnover, and institutional amnesia. This 
is knowledge management, not just data management.

---

## Cost to Own: Pragmatics vs RAG

### RAG Maintenance Cycle
1. Source document updated → re-extract
2. Re-chunk (hope parameters still work)
3. Re-embed (model version matters)
4. Re-index (hope retrieval quality holds)
5. No way to verify without full evaluation re-run
6. No traceability: which queries are affected by the change?

### Pragmatics Maintenance Cycle
1. Source changes → edit the specific node
2. Provenance chain tells you exactly which source changed
3. Deterministic delivery means you know exactly which queries are affected
4. Update is surgical, not wholesale
5. Expert review of one judgment, not re-validation of entire pipeline

### Scale Comparison
- 35 pragmatics: a few days of expert curation
- 311 RAG chunks: 30 minutes of compute, but unknowable quality without eval
- The pragmatics took more human time but produce AUDITABLE, TRACEABLE, 
  DETERMINISTIC results. The RAG took less time but produces probabilistic, 
  unauditable, untraceable results.

---

## The Weight Class Argument

35 pragmatics punch astronomically above their weight:
- 35 atomic judgments vs 311 text chunks (9:1 ratio)
- Yet pragmatics win on composite (1.61 vs 1.43), on D3 (1.55 vs 1.09), 
  on D5 (1.62 vs 1.29)
- And achieve 91.6% fidelity vs 64.9%

Even with RAG, you must curate. Someone has to decide which documents to 
include, how to chunk them, how many to retrieve. Those are judgment calls 
made blindly. Pragmatics make those judgment calls explicitly, with 
provenance and expert review.

What good is having the information if you don't know how to use it?

---

## API-Side Delivery: The Architectural Advantage

RAG requires: vector store, embedding model, retrieval pipeline, chunk 
storage. Operationally heavy. Must be hosted and maintained separately 
from the data API.

Pragmatics require: a lookup table keyed to query parameters. The Census 
API already returns metadata with every call (variable labels, geography 
names, vintage). Pragmatics are the same pattern — structured JSON returned 
alongside the data. No vector store, no embeddings, no retrieval pipeline.

Call for poverty data in a small county → API returns the data PLUS a 
fitness-for-use note: "CV exceeds 30%, consider 5-year estimates."

This is how ARIA labels work for accessibility. This is how Open Banking 
structured APIs replaced screen-scraping. The producer ships the judgment 
with the data.

---

## The FCSM Pitch (One Sentence)

Same source documents, three delivery methods. Raw text helps models recall 
more (D1). Curated expert judgment helps models reason correctly (D3, D5). 
The difference isn't what the model knows — it's whether it gets expert 
judgment at the point of decision.

## The Best Practice Recommendation

Don't just publish your data. Don't just publish your documentation. 
Publish your expert judgment about fitness-for-use in a structured, 
machine-queryable, deterministic form. That's what makes open data 
safe for GenAI consumption.

RAG is the easy path. It works. But it doesn't scale to trustworthy.
