# Chapter 2: Test System Architecture

[← Ch. 1](01_purpose_scope.md) | [README](README.md) | [Ch. 3 →](03_configuration.md)

---

## 2.1 System Diagram

```mermaid
flowchart TB
    subgraph INPUTS["Stage 0: Inputs"]
        BAT["queries.yaml\n39 queries"]
        CFG["config.py\nDEFAULT_YEAR=2024\nDEFAULT_PRODUCT=acs5"]
        PACKS["packs/acs.db\n36 pragmatics items"]
    end

    subgraph STAGE1["Stage 1: Response Generation"]
        HARNESS["harness.py\nTest Runner"]

        subgraph CONTROL["Control Path"]
            C_API["Claude API\nSonnet 4.5\nNo tools"]
        end

        subgraph TREATMENT["Treatment Path"]
            T_API["Claude API\nSonnet 4.5\nWith tools"]
            MCP["MCP Client\nstdio subprocess"]
            SERVER["census-mcp server\n3 tools"]
            CENSUS["Census API\napi.census.gov"]
        end
    end

    subgraph STAGE1_OUT["Stage 1 Output"]
        JSONL1["cqs_responses.jsonl\n39 QueryPairs"]
    end

    subgraph STAGE2["Stage 2: Judge Scoring"]
        JUDGE["judge_pipeline.py"]
        OPUS["Claude Opus 4.5"]
        GPT["GPT-5.2"]
        GEMINI["Gemini 2.5 Pro"]
    end

    subgraph STAGE2_OUT["Stage 2 Output"]
        JSONL2["cqs_scores.jsonl\n39 x 3 judgments"]
    end

    subgraph STAGE3["Stage 3: Analysis"]
        ANALYSIS["analysis.py"]
        AGREE["Inter-rater agreement\nKrippendorff alpha ordinal"]
        EFFECT["Treatment effect\nWilcoxon signed-rank"]
        EQUIV["Equivalence test\nTOST +/-1 CQS"]
    end

    subgraph STAGE3_OUT["Stage 3 Output"]
        REPORT["CQS evaluation report\nTables, figures, findings"]
    end

    BAT --> HARNESS
    CFG --> SERVER
    PACKS --> SERVER

    HARNESS --> C_API
    HARNESS --> T_API
    T_API -->|tool_use| MCP
    MCP -->|stdio JSON-RPC| SERVER
    SERVER -->|HTTP GET| CENSUS
    CENSUS -->|JSON| SERVER
    SERVER -->|tool_result + pragmatics| MCP
    MCP -->|tool_result| T_API

    C_API --> JSONL1
    T_API --> JSONL1

    JSONL1 --> JUDGE
    JUDGE --> OPUS
    JUDGE --> GPT
    JUDGE --> GEMINI
    OPUS --> JSONL2
    GPT --> JSONL2
    GEMINI --> JSONL2

    JSONL2 --> ANALYSIS
    ANALYSIS --> AGREE
    ANALYSIS --> EFFECT
    ANALYSIS --> EQUIV
    AGREE --> REPORT
    EFFECT --> REPORT
    EQUIV --> REPORT
```

## 2.2 Component Inventory

| Component | File | Status | Description |
|---|---|---|---|
| Test battery | `src/eval/battery/queries.yaml` | ✅ Built | 39 queries, machine-readable |
| Server config | `src/census_mcp/config.py` | ✅ Built | Externalized defaults, env overrides |
| Pydantic models | `src/eval/models.py` | ✅ Built | ToolCall, ResponseRecord, QueryPair |
| MCP client | `src/eval/mcp_client.py` | ✅ Built | Subprocess lifecycle, tool dispatch |
| Agent loop | `src/eval/agent_loop.py` | ✅ Built | Control + treatment paths |
| Test harness | `src/eval/harness.py` | ✅ Built | CLI runner, JSONL output, resume |
| Judge pipeline | `src/eval/judge_pipeline.py` | ⬜ Not built | Stage 2 |
| Analysis | `src/eval/analysis.py` | ⬜ Not built | Stage 3 |
| Stats library | `src/eval/lib/stats.py` | ⬜ Not built | Copy from harmonization project |
