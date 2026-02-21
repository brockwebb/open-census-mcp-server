# Semantic Smearing — Empirical Evidence Inventory

## Primary Data Locations
- **Full analysis report:** `talks/fcsm_2026/analysis/semantic_smearing_report.md`
- **Raw data artifacts:** `talks/fcsm_2026/analysis/results/`
- **Sample IDs:** `results/similarity_sample_ids.json` (n=2,500 variables)
- **RAG index metadata:** `results/rag_ablation/index/metadata.json`

## MiniLM 384 (all-MiniLM-L6-v2) — Matched-Pairs Analysis

| Metric | Labels Only | Raw (label + concept) | Enriched (full text) |
|--------|-------------|----------------------|---------------------|
| Mean pairwise similarity | 0.4791 | 0.4297 | 0.6271 |

- **Enrichment similarity increase:** 45.9%
- **Group discrimination collapse:** 63.7% — enrichment made unrelated variables much more similar, destroying retrieval signal

## RoBERTa-large (1024d) — Scaling Comparison

- **Similarity increase:** 82.2%
- **Discrimination collapse:** 86.5%
- **Conclusion:** Larger models amplify the effect. Problem is in the homogenized text (boilerplate methodology content), not model quality.

## Key Finding
AI-enriched metadata made the problem measurably worse. The enrichment added shared-domain boilerplate language that pushed all embeddings closer together. This is the empirical smoking gun: more semantics ≠ better discrimination in domain-homogeneous corpora. The problem is anisotropy (Ethayarajh 2019) compounded by domain homogeneity.

## Connection to Production Results
The same MiniLM 384 model was used for the RAG condition in the V2 evaluation:
- RAG index: FAISS IndexFlatIP (cosine), top-k=5, 311 chunks
- RAG CQS: 1.14 vs pragmatics 1.53 (d=0.922, S2-011)
- RAG fidelity: 74.6% vs pragmatics 91.2% (S3-002, S3-003)
- Pragmatics retrieval: 100% deterministic (39/39, DET-001–004) because graph traversal, not vector search
