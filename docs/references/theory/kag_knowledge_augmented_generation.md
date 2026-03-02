# KAG: Boosting LLMs in Professional Domains via Knowledge Augmented Generation

**Citation:** Liang, Lei et al. (2024). KAG: Boosting LLMs in Professional Domains via Knowledge Augmented Generation. arXiv:2409.13731v3

**URL:** https://arxiv.org/abs/2409.13731
**GitHub:** https://github.com/OpenSPG/KAG
**Team:** Ant Group Knowledge Graph Team + Zhejiang University

## Key Claims

- RAG has limitations: gap between vector similarity and knowledge reasoning relevance; insensitivity to knowledge logic (numerical values, temporal relations, expert rules)
- KAG achieves relative improvement of 19.6% on hotpotQA and 33.5% on 2wiki (F1 score) vs SOTA RAG methods
- Applied to E-Government and E-Health Q&A at Ant Group

## Five Key Enhancements

1. **LLM-friendly knowledge representation (LLMFriSPG)** - Upgrades SPG with DIKW hierarchy; separates instances and concepts; divides properties into knowledge (schema-constrained) and information (schema-free) areas
2. **Mutual-indexing between KG and original chunks** - Cross-references graph structure with source text blocks; semantic chunking; information extraction with descriptive context
3. **Logical-form-guided hybrid reasoning engine** - Three operator types: planning, reasoning, retrieval; integrates KG reasoning, language reasoning, numerical computation
4. **Knowledge alignment with semantic reasoning** - Domain knowledge injection; concept graphs for semantic alignment; reduces OpenIE noise
5. **Model capability enhancement (KAG-Model)** - Enhances NLU, NLI, NLG capabilities for framework operation

## Architecture: Three Parts

- **KAG-Builder**: Offline index construction (knowledge representation + mutual indexing)
- **KAG-Solver**: Logical-form-guided hybrid reasoning (planning + reasoning + retrieval operators)
- **KAG-Model**: Fine-tuned model capabilities (not yet fully open-sourced)

## Knowledge Representation (LLMFriSPG)

Three-layer hierarchy:
- **KG_cs (Knowledge layer)**: Domain knowledge with schema constraints, high accuracy, high labor cost
- **KG_fr (Graph information layer)**: Entities/relations from OpenIE, schema-free, lower accuracy but more coverage
- **RC (Raw chunks layer)**: Original document chunks after semantic segmentation

Key insight: For same entity type, supports BOTH pre-defined schema-constrained properties AND dynamically extracted schema-free properties. Users balance precision vs. coverage based on domain needs.

## Domain Knowledge Injection Methods

1. Domain term and concept injection (iterative extraction with vector retrieval)
2. Schema-constraint extraction (for structured professional documents)
3. Pre-defined knowledge structures by document type (e.g., government affairs docs → entity types with property slots)

## Extraction Pipeline

- Uses fine-tuning-free LLMs (GPT-3.5, DeepSeek, Qwen) or fine-tuned model
- Extracts entities → events → relations → hypernym relations
- Generates built-in properties: description, summary, semanticType, spgClass
- Mutual indexing: supporting_chunks links instances back to source text

## Logical Form Solver

- Transforms NL questions into hybrid symbolic+language solving
- Each step uses different operators: exact match, text retrieval, numerical computation, semantic reasoning
- Integrates four problem-solving processes: retrieval, KG reasoning, language reasoning, numerical calculation

## Benchmarks

- 2WikiMultiHopQA: +19.6% F1 vs HippoRAG
- MuSiQue: +12.2% F1
- HotpotQA: +12.5% F1

## Relevance to Census MCP / Pragmatics Project

### Potentially Useful
- Schema-constrained extraction approach could improve methodology doc processing vs LightRAG
- Mutual indexing (KG nodes ↔ source chunks) preserves provenance — important for citation requirements
- DIKW hierarchy framing parallels Bloom's taxonomy framing
- Concept alignment could help with statistical terminology normalization

### Limitations for Our Use Case
- Heavy infrastructure (OpenSPG engine, Docker stack)
- Designed for multi-hop factual Q&A, not judgment/fitness-for-use delivery
- Does not address semantic smearing or authoritative knowledge delivery
- Model quality still matters for extraction — doesn't solve the LightRAG problem of model dependency

### Bottom Line
KAG is infrastructure for building domain KGs with better extraction quality than vanilla GraphRAG. Could be useful for scaling methodology document processing across multiple surveys. Does NOT replace pragmatics layer — complementary infrastructure, not competing contribution.

## Notable Updates
- v0.8.0 (June 2025): MCP protocol support, expanded indexing types
- v0.7 (April 2025): Refactored solver, "lightweight build" mode (89% token cost reduction)
