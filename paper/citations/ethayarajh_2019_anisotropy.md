# Citation: Ethayarajh 2019 — Embedding Anisotropy

## Full Citation
Ethayarajh, K. (2019). How Contextual are Contextualized Word Representations? Comparing the Geometry of BERT, ELMo, and GPT-2 Embeddings. *Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing (EMNLP)*. https://arxiv.org/abs/1909.00512

## Key Finding
"The representations of all words occupy a narrow cone in the vector space rather than being uniform in all directions." High anisotropy means random word cosine similarities approach 1, especially in higher layers.

## Key Evidence
- **Anisotropy metric:** Average cosine similarity between randomly sampled word representations is non-zero and rises in upper layers (~0.99 in GPT-2's final layer) — a narrow cone
- **Visualization:** Figure 1 shows embeddings clustering in a conical region across nearly all layers of BERT, ELMo, and GPT-2
- **Implications:** Anisotropy accompanies increasing context-specificity but reduces effective dimensionality, unlike isotropic static embeddings

## Related Work
- CosReg and other regularization techniques encourage isotropy for better semantic separation
- Principal components from anisotropic spaces still outperform GloVe/FastText on benchmarks when derived from lower layers

## Relevance to This Paper
Anisotropy is the formal mechanism underlying what we operationally call "semantic smearing" in Census data. Census variable descriptions share vocabulary, domain, and structure — they start in the narrow cone and embeddings cannot separate them. Our enrichment experiment (AI-generated descriptions) made similarity WORSE because it added more shared-domain language. Higher-dimensional models (RoBERTa 1024) performed worse than smaller (MiniLM 384) — more dimensions captured more of the same overlapping signal. This is why RAG over Census metadata fails: cosine similarity cannot discriminate in an anisotropic, domain-homogeneous space.

## Paper Framing
- **Formal term:** anisotropy (Ethayarajh 2019)
- **Operational definition:** semantic smearing — the model can't keep distinct Census concepts distinct
- **Metaphor:** "not a needle in a haystack — a needle in a haystack of needles"
