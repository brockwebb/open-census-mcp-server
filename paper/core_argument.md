# Paper Core Argument — Working Draft

## Central Goal
Secure PRAGMATICS as a named concept — the layer beyond metadata that federal statistical AI systems need.

## The Argument (5 beats)

1. **Syntax and semantics are done.** Federal agencies have done the hard work on syntax (APIs, machine-readable formats) and semantics (metadata, variable descriptions, concept classifications). That's the "AI-ready data" push. It's necessary and real.

2. **LLMs leverage that work.** They translate natural language into domain-aware queries and retrieve correct data. The syntax and semantics layers are working.

3. **There's a layer beyond metadata.** The expert judgment about fitness-for-use — when to trust an estimate, when to refuse, when the data answers a different question than the one asked. No agency packages this. No benchmark tests for it. It lives in the heads of senior statisticians and dies when they retire.

4. **Pragmatics is that layer.** Named, defined, implementable. The best practice for open data should be: ship the expertise alongside the data. Not as documentation that nobody reads. As structured, machine-deliverable judgment that reaches the user at the moment they need it. "Statistician in your pocket."

5. **Proof it works.** d=1.440, 36 items, $0.09/query, same source material as RAG but 2.2× more cost-effective. Largest effect on D3 (uncertainty communication, d=1.353) — exactly where fitness-for-use judgment matters most.

## Landscape Positioning
- NORC/NCSES: measuring model performance on statistical data (prompt-response pairs)
- NSF/NDIF: analyzing internal LLM mechanisms for safety/accuracy
- StatEval, LLM-SRBench: benchmarking reasoning capability
- **All measuring the gap. Nobody filling it.** Pragmatics is the intervention, not another benchmark.

## Framing Devices
- **Formal basis:** Morris (1938) semiotic triad — syntax, semantics, pragmatics
- **Technical mechanism:** Anisotropy (Ethayarajh 2019) + domain homogeneity = semantic smearing
- **Metaphor:** Not a needle in a haystack — a needle in a haystack of needles
- **Vision:** Statistician in your pocket (Jobs framing)
- **Empirical anchor:** Enrichment experiment — more semantics made discrimination 63.7% WORSE

## What This Paper Is NOT
- Not primarily an evaluation paper (though it has empirical validation)
- Not competing with NORC (complementary — they measure, this treats)
- Not a RAG paper (pragmatics is a different concept, not a better RAG)
- Not an ontology paper (the LLM handles semantics; this is the judgment layer above it)

## Status: WORKING DRAFT — still shaping
