# Core Thesis: Pragmatics as Point-of-Decision Expert Judgment

**Date:** 2026-02-13
**Context:** Crystallized during Phase 4B evaluation work. This is the theoretical 
contribution of the FCSM paper.

---

## The Problem We're NOT Solving

RAG assumes the problem is **retrieval** — find the right chunk from a large corpus. 
Knowledge graphs assume the problem is **relationships** — traverse connections 
between entities. Both are solutions to "the model doesn't know enough."

We are solving a different problem.

## The Actual Problem

**The model knows too much, imprecisely.** It has training data impressions of Census 
methodology — enough to sound right, wrong in ways that matter. This is semantic 
smearing: the model conflates information that should remain distinct across different 
survey years, estimate types, geographic levels, and methodological contexts.

The control condition in our evaluation demonstrates this: when asked for the poverty 
rate in Maricopa County, the model says "approximately 12-13%." The actual rate from 
the API is 11.0%. The model isn't confabulating from nothing — it has a training data 
impression that's close but imprecise, and it has no mechanism to know it's wrong. It 
sounds authoritative. A user would trust it.

## What the Model Already Knows (and What It Doesn't)

Here's the uncomfortable insight that the RAG and ontology communities need to hear: 
**the model has already encoded your ontology.** When you carefully construct a taxonomy, 
define semantic relationships, and organize metadata — the model's training data contains 
all of that, represented at a much higher dimensional level in latent space. Your 
hand-built ontology is a low-dimensional projection of what the model already 
approximates through statistical proximity in its embedding space.

The syntax (proper ordering, tabulation), the semantics (description metadata, 
classifications) — yes, do those things. They help. But the model already has a 
high-dimensional approximation of all of it. There are small errors in that 
approximation, and some compound, but **the real problem was never the answers.**

Making numbers easier to get doesn't help with interpretation. The Census API already 
provides the data. What's missing isn't access — it's the expert judgment about 
fitness-for-use that isn't well captured in any model's training data, because it 
lives in the heads of senior statisticians who learned it through decades of practice, 
not from documents.

## What Pragmatics Actually Do

We're not saying RAG doesn't work or knowledge graphs don't work. We're saying **you 
don't need the whole thing — just the right pieces at the right time.**

It's not about having "all the data." It's about having the right pieces when you need 
the right context to not just understand the data, but to diagnose and interpret it to 
develop well-founded conclusions.

Pragmatics provide **clinical judgment at the point of decision.** A radiologist doesn't 
need the entire medical textbook to read a scan. They need the specific diagnostic 
criteria relevant to what they're looking at right now. Similarly, when a user asks about 
poverty in a small county, the system doesn't need the entire ACS methodology handbook. 
It needs three things:

1. The MOE formula (SE = MOE / 1.645) to assess reliability
2. The CV threshold (>40% = unreliable) to flag fitness-for-use
3. The period estimate caveat (5-year = 60-month average, not a snapshot)

That's three sentences of expert judgment, delivered at the moment the model is 
interpreting the data. Not retrieved from a corpus. Not traversed from a graph. 
Structured, auditable, point-of-decision context.

## Three Layers of Noise

**Just as curating training data reduces variance in what a model learns, curating 
expert judgment reduces variance in what a model concludes.**

This principle operates at three layers, each addressing a different source of noise:

### Layer 1: Noise in What the Model Learns (Training Data Curation)

The ML community already accepts this: curated, high-quality datasets outperform 
massive, noisy corpora. The variance increases with volume — fatter outlier tails — 
unless quality is controlled. Garbage in, garbage out, but at scale.

### Layer 2: Noise in What the Model Applies (Expert Judgment Curation)

The same principle at inference time. The information selectivity pattern:

- **RAG over entire methodology corpus:** Retrieves chunks that are semantically 
  similar but may be contextually wrong (the dimensionality wall — Census methodology 
  is too semantically homogeneous for embeddings to differentiate)
- **Full knowledge graph traversal:** Returns everything connected to the query, 
  including irrelevant relationships that dilute the signal
- **35 pragmatic context items:** Each one is a distilled piece of expert judgment 
  with defined latitude, provenance, and retrieval triggers

The signal-to-noise ratio matters more than the signal volume. Just as you curate 
and clean your training data, you must curate and clean the expertise you provide 
at inference time. The same discipline, applied at a different stage of the pipeline.

### Layer 3: Noise in the Expertise Itself (Latitude as Calibrated Uncertainty)

This is the uncomfortable truth: **human experts can be way off.** Sometimes for 
reasons that wouldn't make sense to ordinary people — a senior statistician refuses 
to use a published estimate because they know the sampling frame changed that year 
in a way the documentation doesn't adequately convey. Sometimes the error is subtle, 
and only a master would detect it. And sometimes, there simply is no "right" answer — 
the tradespace has a wide optimum plateau where multiple positions are defensible.

This maps directly to the latitude system in the pragmatics architecture:

| Latitude | Epistemological Status | Expert Agreement |
|----------|----------------------|------------------|
| `none` | Hard constraint — no expert disagrees | "ACS 1-year requires 65K+ pop" |
| `narrow` | Strong consensus with rare, recognizable exceptions | "CV > 40% means unreliable" |
| `wide` | Genuinely context-dependent — the optimum plateau | "Whether to use 1yr vs 5yr depends on recency vs reliability tradeoff" |
| `full` | Background that informs but doesn't constrain | "ACS replaced the Census long form in 2005" |

Latitude is not a metadata field. It is a **calibrated uncertainty model over expert 
judgment itself.** It encodes not just what experts know, but how confidently the field 
holds that knowledge — and crucially, where the field acknowledges that reasonable 
practitioners disagree.

This connects to Kahneman, Sibony & Sunstein (2021) *Noise: A Flaw in Human Judgment*: 
experts exhibit shocking variance in supposedly deterministic professional judgments. 
Pragmatics don't eliminate expert noise — they **structure it explicitly** so the 
consuming model knows how much latitude it has. A `none`-latitude item means "the field 
is sure, don't deviate." A `wide`-latitude item means "reasonable people disagree, use 
your judgment given the specific context."

The model consuming these pragmatics doesn't just get expert knowledge. It gets 
**expert knowledge with calibrated confidence bounds.** That's what separates structured 
pragmatics from a prompt injection of domain rules.

## Architecture Implications

The quarry, knowledge graph, and extraction pipeline are not the product. They are 
the **authoring environment** for distilling expert judgment into portable, structured 
context items. The runtime is 35 items in a SQLite file. Not a knowledge graph at 
runtime. Not a vector store at runtime. Just the right 35 things a statistician would 
tell you before you use this data.

The pipeline architecture reflects this:

```
Source documents → KG extraction → harvest → curate → 35 pragmatic items → SQLite
     (broad)        (structured)    (filter)  (judge)     (precise)        (fast)
```

Each stage is a noise reduction step. The final product is maximally selective.

## Empirical Evidence

Our Stage 3 fidelity results validate this directly:

| Metric | Treatment (35 pragmatics) | Control (no pragmatics) |
|--------|---------------------------|-------------------------|
| Auditability | ~95% | ~10% |
| Fidelity to source data | ~91% | Unmeasurable |
| Specific enough to verify | Yes | No |

The treatment doesn't just produce better answers. It produces answers that are 
**structurally verifiable** — each claim traces to a specific API response, table, 
variable code, and geography. The control produces plausible-sounding claims that 
cannot be independently checked.

This isn't a RAG-vs-no-RAG comparison. It's a demonstration that a small number of 
precisely targeted expert judgments, delivered at the point of decision, produce 
measurably more trustworthy statistical consultation than the model's training data 
alone — regardless of how much training data exists.

## Framing for FCSM

The contribution is not "we built a better RAG system." The contribution is:

1. **Diagnosis:** LLMs exhibit semantic smearing in federal statistical domains — 
   they conflate information that should remain distinct, producing confidently wrong 
   answers that are difficult for non-experts to detect. The model already has your 
   ontology encoded in latent space. The problem isn't knowledge — it's judgment.

2. **Treatment:** Pragmatic context items — structured expert judgment with calibrated 
   latitude, provenance, and defined retrieval triggers — correct for semantic smearing 
   at the point of decision without requiring comprehensive knowledge retrieval.

3. **Evidence:** A three-stage evaluation framework (response generation, multi-model 
   judge scoring, automated pipeline fidelity) demonstrates that 35 expert judgment 
   items improve consultation quality on 4/5 dimensions while achieving 91% fidelity 
   to authoritative sources.

4. **Principle:** Information selectivity at inference time follows the same pattern as 
   training data curation — precision beats volume. Just as curating training data 
   reduces variance in what a model learns, curating expert judgment reduces variance 
   in what a model concludes. And encoding the uncertainty of that expertise (latitude) 
   gives the model calibrated confidence bounds over the judgment itself.

5. **Three layers of noise management:** Training data curation (what it learns), 
   expert judgment curation (what it applies), and latitude encoding (how certain 
   the expertise is). One architecture addresses all three. That's the contribution.
