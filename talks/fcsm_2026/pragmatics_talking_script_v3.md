# Pragmatics — Talking Script v3
## FCSM 2026: "GenAI and Open Data: Guidelines and Best Practices"
## 10-15 minutes

---

### The Arc (full talk, ~12 minutes)

**Open — The Timeline (2 min):**

"We've spent twenty years making federal data machine-readable. 2006, 2011 — the federal mandate. And we should keep doing that — please, stop burying data in Excel spreadsheets with merged headers and footnotes and calling it shared. Pretty data, good metadata, structured APIs — keep going. That work matters.

But here's where we are. We solved the syntax problem — machines can find and parse the data. We solved the semantics problem — LLMs can read metadata and understand what a variable means. What we haven't solved is the pragmatics problem: does the AI know when the data is actually fit for the question being asked?

And by the way — we're not the only ones on this journey. The commercial web is going through the same progression right now. robots.txt told crawlers what they could access — syntax. Schema.org and JSON-LD told AI what content means — semantics. Now you've got llms.txt, where sites publish markdown-friendly content maps for AI crawlers. Google's proposing WebMCP, where websites declare tool-use capabilities directly to AI agents. The whole web is learning to design for AI consumption — permission, then meaning, then structure, then capability.

But here's the difference. If an AI gets shoe prices wrong, someone buys different sneakers. If an AI gets a poverty estimate wrong, a school board misallocates funding. The commercial web doesn't need pragmatics. High-consequence domains like federal statistics do. And nobody's building that layer."

**The Problem (2 min):**

"Ask a model for median income in a small town. It'll give you a number. It won't tell you the margin of error is bigger than the estimate. It won't tell you the 1-year product isn't even published at that population size. It won't suggest 5-year estimates instead. It gives you data without judgment.

And any answer is good if you're brave enough to use it.

This isn't a retrieval problem. The model has the information — it's compressed together in the training weights. Survey years blur. Estimate types get conflated. We call it semantic smearing. More metadata doesn't fix it. Better prompting doesn't fix it. The Fed published a paper proving prompt engineering just moves the errors around."

**The Diagnosis (1.5 min):**

"Two established frameworks point at the same gap. Morris's semiotic triad — syntax, semantics, pragmatics. We built two layers, not the third. Bloom's taxonomy — machine-readable data gives you Remember and Understand, metadata gives you Apply, but Evaluate requires expert judgment that isn't in any system.

And here's something I found that surprised me. NIST has published twelve crosswalks between the AI Risk Management Framework and other standards. Twelve. ISO, EU AI Act, OECD, Singapore, Japan. Zero from the federal statistical community. FCSM 20-04 and NIST AI RMF — two authoritative frameworks governing quality when AI touches federal data — and no published mapping connects them.

So I built one."

**The Crosswalk (1.5 min):**

"The crosswalk reveals a structural pattern. FCSM's Objectivity and Integrity domains map well to NIST — accuracy, transparency, security, those are shared concerns with different vocabulary. But FCSM's Utility domain — relevance, timeliness, granularity — doesn't map to NIST at all. And NIST's AI-specific characteristics — safety, explainability, fairness — don't map to FCSM.

The critical finding is in the empty space between them. Neither framework addresses the specific failure mode where an AI system confidently produces a statistical answer that has no basis in appropriate data. FCSM wasn't designed for that — it assumes human analysts. NIST wasn't designed for that at the domain level — it can tell you AI should be valid, but not what validity means for ACS margin of error calculations.

That gap is where people get hurt. That's where a school board uses a bad estimate to allocate funding because the AI didn't know better."

**The Solution (1.5 min):**

"So I built pragmatics — structured expert judgment about data fitness-for-use. What a senior statistician would tell a colleague before they touch the data. Each item is one to three sentences, sourced to specific documents with page-level citations, tagged with how much latitude exists to deviate. The system consults this context before the AI interprets any data.

35 items for the American Community Survey. Not rules. Not lookup tables. Not prompt instructions. Expert judgment — the third layer nobody ships."

**The Evaluation (2 min):**

"Now, I don't get to just say it works. The crosswalk gave me the evaluation framework. I mapped FCSM data quality dimensions against NIST trustworthiness characteristics and built a domain-specific quality rubric at the intersection — six dimensions: five scored for consultation quality, plus a binary grounding check. That's TEVV — Test, Evaluation, Verification, and Validation — operationalized for AI-mediated statistical consultation.

Controlled evaluation. Three conditions: Census API tools alone, tools plus 311 RAG document chunks from methodology handbooks, and tools plus 35 pragmatic items. Multi-vendor LLM judges — Anthropic, OpenAI, Google — with counterbalanced pairwise comparison. 39 test queries. Statistical validation.

The pragmatics condition hit 92% fidelity. RAG hit 65%. 35 items of curated expert judgment outperformed 311 document chunks with ten times the content. Perfect determinism across all conditions."

**The Best Practice (1.5 min):**

"So here's the best practice, and it's simple. Keep making data pretty. Keep improving metadata. Use LLMs to help classify and standardize — they're great at that. But start capturing the third layer: expert judgments about data fitness-for-use. The knowledge that lives in statisticians' heads about what the numbers mean, when to use them, and when not to.

That knowledge is the most valuable thing in this room, and none of it is machine-accessible. Every time a senior statistician retires, we lose fitness-for-use judgment that took decades to build. Pragmatics is how we capture it, structure it, and put it where AI systems can use it.

Numbers without judgment? Any answer is good if you're brave enough to use it."

---

### Short Version (90 seconds — for hallways)

"We've spent twenty years on machine-readable data and metadata — syntax and semantics. There's a third layer nobody ships: pragmatics — expert judgment about whether data is fit for a specific use. I built a crosswalk between FCSM 20-04 and NIST AI RMF — first one from the statistical community, by the way — found the gap where neither framework covers AI confidently misusing statistical data, and built a system to fill it. 35 pieces of curated expert judgment, evaluated using a quality framework grounded in both federal standards. 92% fidelity versus 65% for traditional RAG. The best practice isn't more metadata — it's capturing what statisticians know."

---

### Zingers

- "Any answer is good if you're brave enough to use it."
- "The problem isn't that AI doesn't know enough. It knows too much, imprecisely."
- "NIST has twelve crosswalks. Zero from us."
- "Every time a senior statistician retires, we lose fitness-for-use judgment that took decades to build."
- "35 items beat 311 chunks. It's not about volume — it's about judgment."
- [slide of Excel icon with frowny face] "This is not machine-readable data sharing."

---

### Q&A Responses

**"How is this different from RAG?"**
"RAG gives the model more information. Pragmatics give it better judgment. Census data is so semantically similar that embeddings can't differentiate median household income from median family income from aggregate income. We measured it — enriching variable descriptions with LLM-generated metadata moved similarity scores 58% of the way toward total collapse. The domain is too homogeneous for retrieval to work. You need curated expert context, not more documents."

**"Does this scale?"**
"The architecture does. Domain packs are modular — ACS now, CPS and others follow the same pattern. Curation is the bottleneck, but we're building extraction pipelines from methodology documents. Hand-curate the quality standard, then scale with review."

**"Why not just improve the metadata?"**
"You should. But metadata tells you what the data IS. Pragmatics tell you whether you should USE it for THIS question. Better metadata doesn't teach an AI that comparing 1-year and 5-year estimates is methodologically invalid."

**"How do you know your evaluation is valid?"**
"The quality rubric is grounded in two federal standards — FCSM 20-04 for data quality and NIST AI RMF for AI trustworthiness. I built the crosswalk, identified where the frameworks align and where they don't, and the evaluation dimensions sit at their intersection. Multi-vendor judges prevent single-model bias. The methodology is documented and reproducible."

**"Have you submitted the crosswalk to NIST?"**
"Not yet, but that's the plan. NIST accepts submissions at aiframework@nist.gov. The pure framework crosswalk is documented and stands independent of the Census application."

**"Can other agencies use this?"**
"The pattern generalizes. Any federal statistical program has the same three layers and the same gap. BLS, BEA, NCHS — they all have methodology handbooks full of judgment that isn't machine-accessible. The crosswalk applies to any agency using AI with federal data. The pragmatics pattern works anywhere the gap exists."

**"What about the NORC/NCSES evaluation work?"**
"I saw early presentations on that effort and tried to share lessons learned — I'd already been down the measurement path and found it was necessary but not sufficient. Measuring the problem is important. I focused on building and validating a solution."

**"Is 35 items enough?"**
"For the ACS evaluation, it covered the most common fitness-for-use failures — population thresholds, margin of error, temporal comparisons, geographic edge cases, dollar values, suppression. The architecture supports expansion. But the point is that 35 curated items outperformed 311 document chunks. The bottleneck isn't volume."
