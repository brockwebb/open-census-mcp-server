# FCSM AI-Ready Data Landscape — Reference Context

*Added: 2026-02-08*
*Purpose: Background context for FCSM 2026 talk development*

---

## Federal AI-Ready Data Initiative

In 2025, the Federal Committee on Statistical Methodology (FCSM) centered its agenda on transitioning federal open data to be AI-ready — data structured, labeled, and accessible enough to support AI applications without model guesswork.

Key developments:

- **FCSM 25-03** ("AI-Ready Federal Statistical Data: An Extension of Communicating Data Quality," May 2025) — the primary guidance document, extending traditional data quality frameworks for machine learning use cases.
- **Department of Commerce** (January 2025) — explicit focus on making open data generative-AI-ready.
- **FCSM Research and Policy Conference** (2025) — sessions on federal statistics, data quality, and AI intersections.
- These build on the **OPEN Government Data Act** (Title II, P.L. 115-435) mandate for useful, usable, and trustworthy federal data.

## Where This Talk Fits: The Practitioner's Gap

The federal guidance addresses what *should* be true about AI-ready data. This talk addresses what happens when a practitioner actually *builds* against that guidance — what works, what doesn't, and what's missing.

### The thesis

Federal AI-ready data initiatives correctly identified the need to move beyond raw data publication. But the framing remains anchored in a 2006-era machine learning paradigm: structured formats, metadata catalogs, master data registries — the "machine-readable" mandate that became federal policy around 2011. That was a necessary step. It is no longer a sufficient one.

The 2017 transformer revolution ("Attention Is All You Need") absorbed the syntactic and semantic layers that those catalogs were designed to provide. Format specifications, ontologies, controlled vocabularies, relational schemas — models now encode these patterns from training data. Continuing to invest in hand-built semantic layers duplicates what the model already knows while ignoring what it doesn't.

What models lack is **pragmatics**: the expert judgment about fitness-for-use that comes from years of working with specific data products. When to use 1-year vs. 5-year ACS. Why a margin of error above 30% CV invalidates a comparison. Why St. Louis, MO breaks your county hierarchy assumption. This knowledge exists as tacit expertise in the heads of domain specialists — exactly the kind of knowledge that doesn't appear in training data and can't be inferred from metadata schemas.

### The confabulation problem

The polite term is "hallucination." The accurate term is **confabulation** — the model generates plausible-sounding but factually wrong statistical guidance with high confidence. This is not a bug to be patched; it's a structural property of probabilistic language models. The knowledge management response is to capture tacit expert knowledge into explicit documentation — specifications, methodology guides, best practices — and provide this as grounding context at inference time.

But there's too much to know. The full knowledge graph of Census domain expertise is too heavy for runtime traversal, and most of it is already in the training data anyway. The productive approach is to distill the **essence** of ground truth — the minimum expert context needed to prevent the most consequential confabulations — and deliver it as modular, composable bundles: **Pragmatics Packs**.

### The philosophical honesty

There will always be errors. Human experts make errors too. The question is not "can we eliminate error" but "can we systematically minimize consequential error while remaining honest about uncertainty." Science revises truth based on evidence. Our goal is continuous improvement — minimizing the gap between model output and the best known understanding at this moment. And because we build modularly, when understanding evolves, we update packs, not retrain models.

### On model selection and the Jobs Doctrine

This work targets modern reasoning models (ADR-003: Haiku 3.5+ minimum). The inevitable objection — "but did you test with GPT-4? With $LEGACY_MODEL?" — mistakes backward compatibility for rigor. The Jobs Doctrine applies: allow less capable models to become obsolete rather than building compensatory complexity. By the time practitioners adopt pragmatics patterns, the models they'll use will exceed today's frontier. Designing for yesterday's limitations is engineering malpractice disguised as thoroughness.

### The trajectory

The 2006 ML paradigm gave us machine-readable data. The 2017 transformer paradigm absorbed that layer. The current need is the pragmatics layer — expert judgment delivered as structured context at inference time. This talk is a snapshot of one practitioner's experience building that layer against real Census data, with honest reporting of what works, what doesn't, and what the field needs next. It will itself be a historical artifact within six months. That's the point — the velocity of change is the message.

---

## Theoretical Foundation: V-Information (Xu et al., 2020)

The pragmatics layer has formal grounding in predictive V-information theory (Xu et al., ICLR 2020). Classical Shannon mutual information assumes an unbounded observer. V-information restricts the observer to a predictive family V — a computationally bounded agent — and measures how much *usable* information one variable provides about another given those constraints.

Three results directly support the pragmatics architecture:

- **Computation creates usable information** (Section 3.2). The data processing inequality says you can't create information by computing on data. V-information shows you *can* create usable information for a bounded observer. An LLM augmented with pragmatics packs has strictly higher V-information about Census fitness-for-use than the same LLM relying on training data alone. This is the formal justification for the always-ground pattern (ADR-004).

- **Asymmetric information is expected** (Section 3.3). Distilling expert knowledge into pack threads is inherently lossy: IV(expert → thread) ≠ IV(thread → expert). This is acceptable because the goal is grounding the model, not reconstructing the expert.

- **Misspecification is tolerable** (Section 6.1). Even when the predictive family V doesn't match the true underlying distribution, V-information still outperforms mutual information estimators for structure learning. Pragmatics packs don't need to perfectly represent expert knowledge — they need to be usable by the observer class we care about (reasoning LLMs). This is why structured context with latitude outperforms formal ontology.

**Citation:** Xu, Y., Zhao, S., Song, J., Stewart, R., & Ermon, S. (2020). A Theory of Usable Information Under Computational Constraints. ICLR 2020. arXiv:2002.10689

---

## Source References

1. FCSM 25-03: https://statspolicy.gov/assets/fcsm/files/docs/FCSM.25.03_AI-Ready-Extension-Data-Quality.pdf
2. FCSM Conference: https://fcsmconf.org/home
3. FedTech Magazine (Aug 2025): https://fedtechmagazine.com/article/2025/08/how-make-data-ai-ready-guide-federal-agencies-perfcon
4. BTS/ROSAP: https://rosap.ntl.bts.gov/view/dot/83634
5. Dathere (Jan 2026): https://dathere.com/2026/01/2025-the-year-opening-data-was-great-again/
6. Travis Hoppe LinkedIn post: https://www.linkedin.com/posts/travis-hoppe-17902b59_federal-committee-on-statistical-methodology-activity-7331356126388572160-6XDK
7. ODI: https://theodi.org/news-and-events/blog/how-ready-is-open-data-for-ai/
8. Commerce GenAI Open Data: https://www.commerce.gov/sites/default/files/2025-01/GenerativeAI-Open-Data.pdf
9. NISS/FCSM event: https://www.niss.org/events/nissfcsm-empowering-generative-ai-trusted-federal-data-strategies-quality-usability
