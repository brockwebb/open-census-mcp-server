# ADR-002: Grounding Layer, Not RAG

**Date:** 2026-02-07
**Status:** Accepted

## Context

Traditional RAG (Retrieval-Augmented Generation) replaces or supplements LLM knowledge by retrieving relevant documents at query time. This is useful when:
- LLM lacks domain knowledge
- Information changes frequently
- Authoritative sources must be cited

For statistical methodology guidance, the LLM already knows ~90% of what's needed (MOE concepts, general survey methodology, comparison best practices).

## Decision

**Build a grounding layer, not RAG.**

The pragmatics pack provides:
- **Citation**: "According to ACS Handbook Chapter 7..." — authoritative source reference
- **Correction**: Edge cases the LLM might miss (65K population threshold)
- **Thresholds**: Specific numbers (CV > 40% unreliable, 1.645 for 90% CI)

The pragmatics pack does NOT:
- Replace LLM's statistical knowledge
- Provide exhaustive documentation retrieval
- Require vector similarity search for every query

## Extraction Criteria

**Extract if:** "Would an LLM confidently give wrong guidance without this?"
- Yes → extract (hard constraints, specific thresholds, non-obvious rules)
- No → skip (general descriptions, navigation instructions, history)

## Consequences

**Positive:**
- Smaller, focused pack content (quality over quantity)
- Faster retrieval (tag-based, not semantic search)
- LLM reasoning preserved (context informs, doesn't replace)
- Lower maintenance burden (only update what matters)

**Negative:**
- Requires judgment about what to extract
- May miss some edge cases initially
- Assumes LLM baseline knowledge is correct

## Alternatives Considered

1. **Full RAG with vector search**: Rejected — overkill for methodology guidance
2. **Complete ontology/taxonomy**: Rejected — we tried this in v2, too complex
3. **No grounding (LLM only)**: Rejected — can't cite sources, misses thresholds
