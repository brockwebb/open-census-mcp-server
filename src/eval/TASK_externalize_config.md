# Claude Code Task: Externalize Server Configuration — No Hardcoded Defaults

## Context
The Census MCP server has hardcoded defaults (year=2022, product="acs5") buried in 
tool schemas and dispatch logic in `server.py`. These are hidden parameters that 
silently affect every query result. The latest ACS 5-year release covers 2020-2024 
(year=2024), so the hardcoded 2022 is already stale.

**Rule: ALL parameters that affect outputs MUST be in a config file. No exceptions.**

## Scope
1. Create `src/census_mcp/config.py` — single source of truth for all server defaults
2. Update `server.py` to read from config instead of hardcoded values
3. Add env var overrides for runtime flexibility
4. Add a pragmatics item about ACS release schedule/currency
5. Update `.env.example` (if exists) or `.env` comments with new vars

## Files to Modify
- `src/census_mcp/server.py` — remove all hardcoded defaults, read from config
- `.env` — add commented-out override examples for new config vars

## Files to Create
- `src/census_mcp/config.py` — server configuration module

## Detailed Spec

### src/census_mcp/config.py

Follow the pattern in `scripts/quarry/config.py` — Python config module with env var overrides and dotenv loading.

```python
"""Census MCP Server configuration.

All parameters that affect outputs are externalized here.
Environment variables override defaults. No hardcoded values in server.py.
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / ".env")
except ImportError:
    pass

# === Census API Configuration ===
CENSUS_API_KEY = os.environ.get("CENSUS_API_KEY", "")

# === Data Product Defaults ===
# These defaults are used when the caller (LLM) does not specify.
# Update when new ACS vintages are released.
#
# ACS Release Schedule (as of 2025):
#   - ACS 1-year: Released September of the following year (e.g., 2024 data in Sep 2025)
#   - ACS 5-year: Released December of the following year (e.g., 2020-2024 in Dec 2025)
#
# IMPORTANT: When updating DEFAULT_YEAR, also verify the Census API 
# endpoint is live at: https://api.census.gov/data/{year}/acs/{product}
DEFAULT_YEAR = int(os.environ.get("CENSUS_DEFAULT_YEAR", "2024"))
DEFAULT_PRODUCT = os.environ.get("CENSUS_DEFAULT_PRODUCT", "acs5")

# Supported products
SUPPORTED_PRODUCTS = {"acs5", "acs1"}

# === Pragmatics Configuration ===
PACKS_DIR = os.environ.get("PACKS_DIR", "packs")

# === Logging ===
LOG_LEVEL = os.environ.get("LOG_LEVEL", "WARNING")
LOG_FILE = os.environ.get("CENSUS_LOG_FILE", "/tmp/census-mcp.log")

# === Server Metadata ===
SERVER_NAME = "census-mcp"
```

### server.py changes

Replace ALL hardcoded values. Specifically:

1. **Import config at top:**
```python
from census_mcp.config import (
    DEFAULT_YEAR, DEFAULT_PRODUCT, SUPPORTED_PRODUCTS,
    PACKS_DIR, LOG_LEVEL, LOG_FILE, SERVER_NAME, CENSUS_API_KEY,
)
```

2. **Logging setup** — use `LOG_LEVEL` and `LOG_FILE` from config (already uses env vars, but route through config for single source of truth)

3. **Server initialization** — use `SERVER_NAME` from config

4. **`_ensure_initialized()`** — use `PACKS_DIR` from config instead of `os.environ.get("PACKS_DIR", "packs")`

5. **Tool schemas** — replace ALL hardcoded year/product defaults:

In `get_census_data` tool schema:
```python
"year": {
    "type": "integer",
    "description": f"Data year (default {DEFAULT_YEAR})",
    "default": DEFAULT_YEAR,
},
"product": {
    "type": "string",
    "description": f'"{DEFAULT_PRODUCT}" or "acs1" (default "{DEFAULT_PRODUCT}")',
    "default": DEFAULT_PRODUCT,
},
```

In `explore_variables` tool schema: same pattern.

6. **Tool dispatch defaults** — replace hardcoded fallbacks:
```python
# OLD: year = arguments.get("year", 2022)
# NEW:
year = arguments.get("year", DEFAULT_YEAR)

# OLD: product = arguments.get("product", "acs5") 
# NEW:
product = arguments.get("product", DEFAULT_PRODUCT)
```

Also replace the hardcoded product validation:
```python
# OLD: if product not in ("acs5", "acs1"):
# NEW:
if product not in SUPPORTED_PRODUCTS:
```

7. **Search for ANY remaining hardcoded "2022" or "acs5" strings in server.py** and replace with config references. There should be ZERO hardcoded defaults remaining.

### .env additions

Add to the bottom of `.env`:
```
# Census MCP Server Configuration
# CENSUS_DEFAULT_YEAR=2024
# CENSUS_DEFAULT_PRODUCT=acs5
# CENSUS_LOG_FILE=/tmp/census-mcp.log
```

### Pragmatics item for ACS release schedule

Add a new context item to the ACS pack. The pack files are in the `packs/` directory.
Check the existing pack structure first:

```bash
ls packs/acs/
```

Add a new item with context_id `ACS-REL-001` (release schedule) with these properties:
- context_id: ACS-REL-001
- text: "As of December 2025, the most recent ACS releases are: ACS 1-year 2024 (released September 2025) and ACS 5-year 2020-2024 (released December 2025). The tool defaults to the most recent 5-year vintage. When users ask for 'current' or 'most recent' data, use the default year. For historical comparisons, explicitly specify the year parameter."
- tags: ["release_schedule", "data_currency", "vintage", "timeliness"]
- latitude: "narrow"
- provenance: source is census.gov/programs-surveys/acs/news/data-releases.html, extraction_method: manual, confidence: grounded
- Add it to the appropriate topic mapping so it surfaces when "timeliness" or "data_currency" topics are requested

Follow the existing pack item format exactly. Read an existing item first to match the structure.

## Verification

After changes, run the smoke test:
```bash
cd /Users/brock/Documents/GitHub/census-mcp-server
/opt/anaconda3/envs/census-mcp/bin/python src/eval/smoke_test_mcp.py
```

Then verify the year default works:
```bash
# Should show 2024 in the tool schema description
/opt/anaconda3/envs/census-mcp/bin/python -c "
from census_mcp.config import DEFAULT_YEAR, DEFAULT_PRODUCT
print(f'DEFAULT_YEAR={DEFAULT_YEAR}')
print(f'DEFAULT_PRODUCT={DEFAULT_PRODUCT}')
"
```

Also run existing tests:
```bash
cd /Users/brock/Documents/GitHub/census-mcp-server
/opt/anaconda3/envs/census-mcp/bin/python -m pytest tests/ -x -q
```

## Constraints
- Do NOT change any test battery or eval code
- Do NOT change the tool names or required parameters
- Do NOT change the MCP protocol interface
- The config change must be backward-compatible: if no env vars are set, it uses 2024/acs5
- Verify the Census API actually serves 2024 ACS 5-year data before committing to that default
