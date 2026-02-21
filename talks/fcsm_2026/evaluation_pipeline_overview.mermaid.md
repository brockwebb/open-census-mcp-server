---
title: "CQS Evaluation Pipeline — Slide-Ready Overview"
description: Four-stage evaluation pipeline for FCSM 2026 knowledge representation study
date: 2026-02-16
status: active
usage: backup/appendix slides for FCSM presentation
---

## Pipeline Overview (one slide)

```mermaid
flowchart LR
    subgraph S1["Stage 1: Generate"]
        direction TB
        S1_IN["39 queries\n3 conditions"]
        S1_OUT["117 responses\n(JSONL)"]
        S1_IN --> S1_OUT
    end

    subgraph S2["Stage 2: Judge"]
        direction TB
        S2_IN["3 pairwise\ncomparisons"]
        S2_OUT["2,106 scores\n(D1-D5)"]
        S2_IN --> S2_OUT
    end

    subgraph S3["Stage 3: Fidelity"]
        direction TB
        S3_IN["117 responses\nvs tool returns"]
        S3_OUT["claim verification\n(match/mismatch)"]
        S3_IN --> S3_OUT
    end

    subgraph S4["Stage 4: Analysis"]
        direction TB
        S4_IN["scores +\nfidelity"]
        S4_OUT["effect sizes\np-values\ntables"]
        S4_IN --> S4_OUT
    end

    S1 --> S2
    S1 --> S3
    S2 --> S4
    S3 --> S4
```

**Speaker notes:** Four-stage pipeline. Stage 1 generates responses under three experimental conditions. Stage 2 scores them using a multi-vendor LLM judge panel. Stage 3 independently verifies factual claims against tool returns. Stage 4 synthesizes scores and fidelity into statistical analysis. Stages 2 and 3 run independently from Stage 1 output — they measure different things (quality judgment vs factual accuracy).

---

## Stage 1: Response Generation (one slide)

```mermaid
flowchart TD
    Q["39 Curated Queries\n(41% normal, 59% edge cases)"]

    Q --> C["Control\nData tools only\nNo methodology"]
    Q --> R["RAG\nData tools +\nRetrieved document chunks"]
    Q --> P["Pragmatics\nData tools +\nCurated expert judgment\nvia MCP tool"]

    C --> OUT["117 Responses\n(JSONL with full provenance)"]
    R --> OUT
    P --> OUT

    style C fill:#f5f5f5,stroke:#999
    style R fill:#fff3e0,stroke:#e65100
    style P fill:#e3f2fd,stroke:#1565c0
```

**Speaker notes:** All three conditions get the same data tools — get_census_data and explore_variables. The only variable is how methodology support is delivered. Control gets none. RAG gets methodology via standard retrieval-augmented generation — document chunks retrieved by semantic similarity, injected into the system prompt. Pragmatics gets methodology via a curated MCP tool that delivers expert judgment structured around specific statistical concepts. Same model, same queries, same API access. The question is whether the form of knowledge representation matters.

Key design decision: the production MCP server bundles pragmatics in every data response. For the experiment, we sanitize tool results — stripping the pragmatics field before the model sees it for control and RAG. The full payload is logged for fidelity verification.

---

## Stage 2: LLM-as-Judge Scoring (one slide)

```mermaid
flowchart TD
    PAIRS["3 Pairwise Comparisons"]

    PAIRS --> P1["RAG vs Pragmatics"]
    PAIRS --> P2["Control vs Pragmatics"]
    PAIRS --> P3["Control vs RAG"]

    subgraph JUDGE["Per Comparison"]
        direction TB
        ANON["Anonymized\nResponse A / Response B"]
        VENDOR["3 Vendors\nAnthropic · OpenAI · Google"]
        PASSES["6 Passes\n(3 A-first, 3 B-first)"]
        RUBRIC["CQS Rubric\nD1-D5, scored 0-2\n+ confidence + reasoning"]
    end

    P1 --> JUDGE
    P2 --> JUDGE
    P3 --> JUDGE

    JUDGE --> SCORES["2,106 JudgeRecords"]
```

**Speaker notes:** Each comparison is scored by three independent LLM vendors — this detects self-enhancement bias, where a model scores its own outputs higher. Presentation is counterbalanced: each query is scored with both A-first and B-first orderings to detect position bias. Six passes per vendor per query enables test-retest reliability measurement. The judge never sees condition labels — just anonymized Response A and Response B. Five dimensions: source selection, methodology, uncertainty communication, definitions, reproducibility. Each scored 0-2 with confidence and free-text reasoning.

Why three comparisons instead of two? Control vs each is baseline validation. RAG vs Pragmatics is the core research question — does curation outperform retrieval? That deserves direct measurement, not a derived estimate.

---

## Stage 3: Fidelity Verification (one slide)

```mermaid
flowchart LR
    RESP["117 Responses"]

    RESP --> CHECK["Automated\nClaim Extraction"]

    CHECK --> VERIFY{"Verify each claim\nagainst tool returns"}

    VERIFY --> MATCH["match"]
    VERIFY --> MIS["mismatched"]
    VERIFY --> NOSRC["no_source"]
    VERIFY --> CALC["calculation\ncorrect/incorrect"]

    MATCH --> SCORE["Fidelity Score\n= (match + calc_correct)\n÷ total claims"]
    MIS --> SCORE
    NOSRC --> SCORE
    CALC --> SCORE
```

**Speaker notes:** Stage 3 is the trustworthiness verification stage. D6 (Grounding) is a binary gate — treatment conditions ground in authoritative sources by design; control does not. Automated fidelity provides claim-level verification: every quantitative claim in the response is extracted and compared against the actual tool call data. In V2, all three conditions make tool calls, so all three get fidelity verification. RAG responses are additionally verified against retrieved chunks.

---

## Stage 4: Three-Group Analysis (one slide)

```mermaid
flowchart TD
    INPUT["2,106 Judge Scores\n+ 117 Fidelity Reports"]

    INPUT --> AGG["Aggregate to Query Level\n(n=39 experimental units)"]

    AGG --> OMNIBUS["Friedman Test\n(repeated measures)"]
    AGG --> PAIRWISE["Wilcoxon Post-Hoc\n(Bonferroni α = 0.0167)"]
    AGG --> EFFECT["Cohen's d\nper dimension\nper comparison\n(bootstrap 95% CI)"]

    OMNIBUS --> REPORT["Publication Tables"]
    PAIRWISE --> REPORT
    EFFECT --> REPORT

    subgraph BIAS["Bias Checks"]
        B1["Position bias"]
        B2["Self-enhancement bias"]
        B3["Verbosity bias"]
    end

    AGG --> BIAS
    BIAS --> REPORT
```

**Speaker notes:** The experimental unit is the query, not the judge record. We aggregate across vendors and passes to get one score per query per condition before running statistical tests. Friedman test is the omnibus — are the three conditions different? Then Wilcoxon signed-rank post-hoc on each pair with Bonferroni correction for three comparisons. Effect sizes reported as Cohen's d with bootstrap confidence intervals. Three bias checks run on every analysis: position bias (does A always win?), self-enhancement (does Anthropic's judge favor Anthropic's caller outputs?), and verbosity (do longer responses score higher regardless of quality?). If any bias exceeds threshold, it's flagged and reported.
