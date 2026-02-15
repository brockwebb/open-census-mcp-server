# Parking Lot: Paper Appendix & Presentation Notes

## Last Updated: 2026-02-15

---

## Appendix A: Behavioral Comparison Table (PLACEHOLDER)

Need a table showing side-by-side examples of Control vs Treatment (and later RAG) 
responses for selected queries. Purpose: illustrate the *qualitative* differences that 
the quantitative scores capture.

### Queries to Feature

Pick queries that illustrate different effects:

| Query | What It Shows |
|-------|---------------|
| NORM-008 (unemployment) | Source selection: Control uses ACS, Treatment redirects to BLS LAUS. OpenAI judges caught this, Anthropic didn't. |
| GEO-002 (geographic comparison) | Full spectrum: Control scores 0 on D2/D3/D5, Treatment scores 2 across the board. Most dramatic gap. |
| SML-002 (small area poverty) | Uncertainty communication: Treatment provides CVs and MOE warnings, Control gives vague "patterns" |
| AMB-001 (ambiguous geography) | Both ask for clarification, but Treatment educates about 65K threshold and 1-year vs 5-year |
| NORM-001 (California population) | The interesting disagreement: OpenAI prefers control (decennial is right answer), Anthropic prefers treatment (better traceability) |
| PER-001a/b/c (persona variants) | The only queries where Anthropic preferred control — what's different about these? |

### For Each Query, Show:
- The query text
- Control response (first ~200 words)
- Treatment response (first ~200 words)  
- RAG response (when available)
- Judge scores (D1-D5) from each vendor
- Notable reasoning excerpts from judges
- What this illustrates about the system

### Pipeline Traceability Examples

Show the tool call chain for a treatment response:
1. Query received
2. `get_methodology_guidance` called → what pragmatics were returned
3. `explore_variables` called → what variables identified
4. `get_census_data` called → what data retrieved
5. Final response synthesized
6. Stage 3 fidelity: which claims mapped to which tool returns

This makes the "auditability" metric concrete — readers can SEE the trace.

---

## Presentation Strategy

### FCSM 2026 (primary)
- Audience: federal statisticians, methodology nerds
- Lead with: the semantic smearing problem (they'll recognize it immediately)
- Show: CQS effect sizes, fidelity numbers, the three-group table
- Killer slide: the auditability gap (72.8% vs 8.1%)
- Don't say: "this replaces [NORC's work]" — let them draw the conclusion

### April 30 Event (secondary submission)
- Friend on committee, likely acceptance
- Can be more provocative / less formal?
- Consider: emphasizing the LLM-as-judge methodology findings (self-enhancement bias, 
  vendor disagreement) as a standalone contribution

### The NORC Comparison (NEVER say this publicly)
$700K for single-shot prompts on base models analyzing responses. No tool augmentation,
no knowledge graph, no fitness-for-use judgment, no auditability pipeline. Our system 
does what they did plus: curated expert knowledge delivery at decision points, full 
traceability from query to tool call to response claim, automated fidelity verification,
and empirical evaluation with effect sizes. Built by one person with ~$55 in API costs.

The work speaks for itself. Let the audience do the math.

---

## GraphRAG Deflection (if asked)

**Q: "Why not use GraphRAG?"**

**A:** "We're doing the valuable part of GraphRAG — the knowledge graph — but at build time, 
not query time. GraphRAG constructs graph representations per query, which is computationally 
expensive ($$$) and doesn't scale for real-world deployment. We pre-curate the expert 
judgment into the graph once, with human quality review, then serve it at runtime with 
sub-second latency via simple vector lookup. 

GraphRAG would re-derive the relationships for every query and wouldn't know which 
relationships encode expert judgment vs which are just structural. Our approach is 
actually the distillation of what GraphRAG tries to do — but with a quality step 
(expert curation) that you can't get from automated graph construction.

We'd welcome someone running GraphRAG on the same test battery for comparison. We 
predict it would score between RAG and Pragmatics on D3/D5 — better retrieval 
structure, but still missing the fitness-for-use judgment that isn't in any document."

**Cost comparison to have in back pocket:**
- GraphRAG per query: ~$0.50-2.00 (graph construction + traversal + synthesis)
- Pragmatics per query: ~$0.01 (vector lookup + pack retrieval)
- At 1000 queries/day: GraphRAG = $500-2000/day, Pragmatics = $10/day
- Plus: GraphRAG quality is uncontrolled. Pragmatics quality is curated.

**⚠️ TODO (post-FCSM, before April 30):** The cost and latency numbers above are
rough estimates / vibes. Before citing in any presentation or paper, need to find
authoritative sources for GraphRAG runtime costs and latency. Look for:
- Microsoft Research GraphRAG papers (they built it — they'll have compute numbers)
- Academic benchmarks comparing RAG variants with cost/latency metrics
- Cloud provider pricing analysis for graph construction at query time
- Any published cost-per-query data from production GraphRAG deployments

Use Perplexity to find these, but verify against primary sources (conference papers,
technical reports, vendor documentation). Not blog posts. Need citable numbers if
anyone pushes back on the cost claim.

Also: capture our OWN per-query costs from the eval pipeline as a concrete comparison
point. We have token counts and latency in every judge record — compute actual $/query
for the pragmatics system.
