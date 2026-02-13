# Chapter 3: Test Configuration

[← Ch. 2](02_system_architecture.md) | [README](README.md) | [Ch. 4 →](04_data_flows.md)

---

## 3.1 Configuration Manifest

All parameters that affect outputs. Per QR-010 / C-006 / DEC-4B-019.

| Parameter | Value | Source | Affects |
|---|---|---|---|
| `DEFAULT_YEAR` | 2024 | `config.py` | All data queries without explicit year |
| `DEFAULT_PRODUCT` | acs5 | `config.py` | All data queries without explicit product |
| `CENSUS_API_KEY` | (from .env) | `.env` | API authentication |
| Test subject model | `claude-sonnet-4-5-20250929` | `agent_loop.py` | All response generation |
| Max tokens | 2048 | `agent_loop.py` | Response length cap |
| Max tool rounds | 5 | `agent_loop.py` | Agent loop safety limit |
| Treatment system prompt | See §3.2 | `agent_loop.py` | Treatment path behavior |
| Control system prompt | See §3.2 | `agent_loop.py` | Control path behavior |
| Judge model 1 | `claude-opus-4-5-20250929` | `judge_pipeline.py` | Stage 2 scoring |
| Judge model 2 | `gpt-5.2` (TBC) | `judge_pipeline.py` | Stage 2 scoring |
| Judge model 3 | `gemini-2.5-pro` (TBC) | `judge_pipeline.py` | Stage 2 scoring |
| Pack content | `packs/acs.db` (36 items) | Runtime | Pragmatics available to treatment |
| Battery version | `queries.yaml` git hash | Git | Query set |

## 3.2 System Prompts

**Treatment:**
```
You are a statistical consultant helping users access and understand U.S. Census data.

You have access to Census data tools. For every query:
1. FIRST call get_methodology_guidance with relevant topics to ground your response
2. Use get_census_data to retrieve actual data with margins of error
3. Use explore_variables if you need to find the right variable codes

Always provide:
- Specific table/variable codes and geography identifiers
- Margins of error and reliability context
- Appropriate caveats about fitness-for-use

If the data is unavailable or unreliable for the stated purpose, say so and explain why.
Recommend alternatives when possible.

IMPORTANT: ALWAYS call get_methodology_guidance first, even when you plan to ask for
clarification. Use the guidance to provide informed clarification that helps the user
understand what data is available and what limitations apply to their request.
Grounding first produces better questions.
```

**Control:**
```
You are a helpful assistant answering questions about U.S. Census data.
Provide accurate, well-sourced information.
```

**Design rationale (DEC-4B-015):** Control prompt is intentionally minimal. We are isolating the effect of tools + pragmatics, not prompt engineering.
