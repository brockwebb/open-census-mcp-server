# Background — 20-Year Federal Data Evolution Arc

## The Story
Same problem for 20 years — making federal data accessible and useful. Each era solved one layer, but AI introduces a new requirement that none of the previous work addresses.

## Timeline

### 2006–2011: The Machine-Readable Era
- Paradigm: structured formats, metadata catalogs, master data registries
- Goal: stop burying data in static Excel files
- "Machine-readable" became official federal policy ~2011
- **Layer solved: SYNTAX** — permission and parsing

### 2017: The Transformer Revolution
- "Attention Is All You Need" (Vaswani et al.)
- LLMs begin absorbing the syntactic and semantic layers that metadata catalogs were designed to provide
- Models encode relational structures and patterns directly from training data
- **Implication:** The metadata infrastructure we spent a decade building is now partially redundant — the models learned it from the training corpus

### 2025–2026: The AI-Ready Data Initiative
- FCSM and federal committees shift focus to making data "AI-ready"
- Extending traditional quality frameworks to support ML use cases
- **But:** Current guidance still misses the third layer — pragmatics
- They're solving the 2011 problem better, not the 2025 problem

## The Project's Internal Arc (mirrors the broader timeline)

### Attempt: RAG over enriched metadata
- Assumption: the problem is variable discovery
- Built massive enriched metadata index

### Failure: Semantic smearing
- Census methodology too semantically homogeneous
- Enrichment INCREASED mean similarity by 82% (RoBERTa)
- Discrimination COLLAPSED by 86.5%
- Anisotropy (Ethayarajh 2019) compounded by domain homogeneity
- Needle in a haystack of needles

### Insight: The pivot
- Variable discovery is the EASY part — LLMs handle it
- The hard problem — the "last mile" — is fitness-for-use judgment
- Not contained in documents. Lives in the heads of senior statisticians.
- Dies when they retire.

### Solution: Pragmatics
- Structured, auditable expert judgment at the point of decision
- Transforms data lookup into statistical consultation
- 36 items, d=1.440, $0.09/query

## The Punchline
We solved syntax (permission and parsing). We solved semantics (meaning and metadata). The future of federal data depends on shipping pragmatics (judgment) alongside the numbers.

## Paper Framing Note
This timeline serves the Introduction or Background section. It positions pragmatics not as a novel invention but as the INEVITABLE next layer in a 20-year progression. The audience at FCSM lived through this timeline. They'll recognize every beat. The question is whether they see the third layer as obvious-in-retrospect or as a stretch. The empirical evidence (d=1.440) makes it concrete rather than aspirational.

## Scope Boundary
The paper does NOT get into MCP protocol details, web-based discovery mechanisms, or tool architectures. The point about syntax/semantics is simpler: discovering and accessing data and official publications matters MORE than ever — it ensures metadata, syntax, and semantics continue to get baked into model training data. And as we expose more pragmatics, more expert judgment gets into the ecosystem, which improves responses especially as reasoning models advance. The virtuous cycle: better access → better training data → better base capability → pragmatics close the remaining judgment gap.

## Three Parts of "AI-Ready Data"
When agencies ask "how do we make our data AI-ready?" the answer has three parts:

1. **Refactor how we expose websites and data stores to AI.** Already underway. Can't wait forever — frontend changes need to happen now. The human-oriented discovery tools (website search, table finders) become irrelevant. Any good AI system + a data API blows open the doors to accessibility/findability.

2. **Accelerate data curation — structure, metadata, better labels.** AI tools can help here. Improve what we already do, faster.

3. **Encode statistical expertise on fitness-for-use.** THIS IS THE PART WE ARE NOT DOING TODAY. This is pragmatics. This is the paper's contribution.

Parts 1 and 2 are the syntax and semantics layers. Agencies are working on them. Part 3 is the gap.

## The FCSM Hook
Pragmatics is NOT a new concept bolted onto statistical practice. Fitness-for-use judgment IS statistical quality — it maps directly to FCSM 20-04 quality characteristics. The crosswalk already exists (our FCSM×NIST crosswalk proves it). The audience's own quality framework has an unimplemented layer for AI systems. We're not asking them to adopt something foreign. We're telling them their own framework has a gap, and here's how to fill it.

Morris defined pragmatics in 1938. FCSM codified data quality characteristics decades ago. The concepts exist. It's just taken us this long to operationalize them for AI. 88 years from Morris to implementation.

## Status: RAW MATERIAL — not yet paper prose
