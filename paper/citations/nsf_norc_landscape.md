# Related Work Landscape — NSF/NORC and Federal Statistical LLM Benchmarks

## NCSES/NORC — Measuring LLM Understanding of Federal Statistical Data
- Contracted by NCSES (National Center for Science and Engineering Statistics)
- Part of National Secure Data Service Demonstration (NSDS-D)
- Creates prompt-response pairs measuring LLM interaction with Commerce Dept statistical data
- Focus: how well LLMs interpret and respond to queries on statistical assets and metadata
- URL: https://www.americasdatahub.org/rfs-mlmu-25/
- Reginfo doc: https://www.reginfo.gov/public/do/DownloadDocument?objectID=164862701

## NSF National Deep Inference Fabric (NDIF)
- Research framework to analyze internal mechanisms of very large LLMs
- Goal: ensure safe, secure, accurate outputs
- URL: https://www.nsf.gov/news/new-nsf-grant-targets-large-language-models-generative-ai

## Relevant Benchmarks
- **LLM-SRBench:** Scientific equation discovery, 239 problems, 4 domains. Tests reasoning beyond memorization.
- **StatEval:** Statistical reasoning, 13,817 foundational problems + 2,300 research-level proofs.
- **Synthetic tabular data:** Traditional statistical methods still outperform LLM approaches — LLMs struggle with complex correlation structures.

## Focus Areas Across Initiatives
- Accuracy & reliability (no fabricated statistics, no misinterpreted data structures)
- Symbolic/numeric reasoning (multi-step, rigorous)
- Data-driven reasoning (without relying on memorization)

## Critical Gap All These Share
ALL of these focus on **measuring** model capability — benchmarking accuracy, testing reasoning, evaluating outputs. NONE address **delivering expert judgment** at the point of reasoning. They ask "how well does the model do?" not "how do we make it do better on fitness-for-use?"

This is the gap pragmatics fills. Measurement tells you the model is wrong. Pragmatics make it right.

## Citations
- https://ai.jmir.org/2025/1/e65729/
- https://www.nsf.gov/news/new-nsf-grant-targets-large-language-models-generative-ai
- https://www.americasdatahub.org/rfs-mlmu-25/
- https://www.reginfo.gov/public/do/DownloadDocument?objectID=164862701
- https://icml.cc/virtual/2025/poster/45191
- https://arxiv.org/abs/2510.09517
- https://www.sciencedirect.com/science/article/pii/S281717052500016X
- https://www.sciencedirect.com/science/article/pii/S0306457325001803
