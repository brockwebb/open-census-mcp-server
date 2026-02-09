# Session Notes: llm-graph-builder Setup & Quarry Schema Seeding

**Date:** 2026-02-09  
**Phase:** FCSM Sprint Week 1 — Knowledge Graph Infrastructure  
**Outcome:** quarry database seeded with KG schema v3.1 Layer 0, llm-graph-builder backend running

---

## What We Did

### 1. llm-graph-builder Local Setup (backend-only)

**Repo:** `~/Documents/GitHub/llm-graph-builder` (cloned from neo4j-labs/llm-graph-builder, kept separate from census-mcp-server per project conventions)

**Environment:** Python 3.12 venv in `backend/`

**Key issues resolved:**

- **torch CPU suffix conflict:** `constraints.txt` pins `torch==2.3.1+cpu` which fails on macOS ARM64. Fix: `sed -i '' 's/+cpu//g' backend/constraints.txt` (strips all `+cpu` suffixes from torch, torchvision, etc.)
- **Conda interference:** Must `conda deactivate` before creating venv, otherwise conda's base Python hijacks the path.
- **RAGAS/OpenAI import bomb:** `src/ragas_eval.py` hardcodes `OpenAIEmbeddings()` at import time regardless of config. Fix: add `OPENAI_API_KEY=sk-dummy-not-used` and `RAGAS_EMBEDDING_MODEL=all-MiniLM-L6-v2` to `.env` to satisfy the import without actually using OpenAI.

**`.env` configuration (backend/.env):**
```
NEO4J_URI=bolt://localhost:7687
NEO4J_DATABASE=quarry
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=<your-password>
EMBEDDING_MODEL=all-MiniLM-L6-v2
IS_EMBEDDING=true
ENTITY_EMBEDDING=false
LLM_MODEL_CONFIG_anthropic_claude_4.5_sonnet=claude-sonnet-4-5-20250929,<your-api-key>
GRAPH_CLEANUP_MODEL=anthropic_claude_4.5_sonnet
GCS_FILE_CACHE=False
TRACK_TOKEN_USAGE=false
OPENAI_API_KEY=sk-dummy-not-used
RAGAS_EMBEDDING_MODEL=all-MiniLM-L6-v2
```

Strip all OpenAI/GCS/Bedrock/Diffbot/cloud config noise — backend-only, local deployment.

**Start command:**
```bash
conda deactivate
cd ~/Documents/GitHub/llm-graph-builder/backend
source venv/bin/activate
uvicorn score:app --reload
```

### 2. Schema Push — What Didn't Work

- **`POST /schema` is read-only.** Despite what the docs imply, this endpoint only *reads* existing labels from Neo4j. It does not accept schema definitions. Error: `'NoneType' object has no attribute 'session'` when DB is empty.
- **The "set schema" path is through the frontend** (Graph Enhancement tab → Add Schema from Data Importer JSON), which requires running the React frontend. We're backend-only.
- **Forum workaround** (Neo4j Aura → Data Importer JSON → import) is cloud-dependent, not useful for local.

### 3. Schema Seeding — What Worked (Option 2: Direct Cypher)

Bypassed the API entirely. Wrote a Python script (`seed_quarry.py`) that connects directly to the `quarry` database via the Neo4j driver and runs all schema DDL + seed data.

**Script location:** Generated to `/tmp/seed_quarry.py` (recreatable from `seed_quarry_task.sh`)

**What it creates:**

| Item | Count | Details |
|------|-------|---------|
| Uniqueness constraints | 5 | AnalysisTask, CanonicalConcept, DataProduct, SurveyProcess, SourceDocument |
| Indexes | 8 | On fact_category, survey, dimension, name, tse_type, validation_status, measure |
| AnalysisTask nodes | 5 | EstimateChangeOverTime, CrossSurveyComparison, SmallAreaEstimation, SubgroupAnalysis, IncomeDistributionAnalysis |
| REQUIRES edges | 5 | With full rule_type, threshold, violation_template, recommended_action |
| QualityAttribute nodes | 5 | overlap_fraction, reference_period_alignment, universe_alignment, effective_sample_size, topcoding_threshold |
| DataProduct nodes | 4 | CPS ASEC, CPS Basic Monthly, ACS 1-Year, ACS 5-Year |
| SurveyProcess nodes | 6 | Sampling, Collection, Weighting, Estimation, Processing, Dissemination |
| CanonicalConcept nodes | 6 | Household Income, Family Income, Personal Income, Earnings, Money Income, Employment |

**Run command:**
```bash
export NEO4J_PASSWORD='your-password'
python /tmp/seed_quarry.py
```

### 4. Neo4j MCP Database Gotcha

The Claude Desktop neo4j-mcp is configured globally in `~/Library/Application Support/Claude/claude_desktop_config.json` with `"NEO4J_DATABASE": "arnold"`. This means all neo4j-mcp calls from any Claude project hit `arnold`, not `quarry`. 

**Options:**
- Change it to `quarry` (breaks arnold project)
- Duplicate the MCP entry as a second server (e.g., `neo4j-quarry`)
- Use direct Python scripts for quarry operations (what we did)

---

## Key Lessons

1. **llm-graph-builder is frontend-dependent for schema config.** The backend API has no "set schema" endpoint. Schema is passed at extraction time via the frontend's session state or read from existing DB labels.
2. **Seeding skeleton nodes directly into Neo4j** is the cleanest backend-only path. Once labels exist, `/schema` reads them back and the extraction pipeline picks them up.
3. **Neo4j MCP is single-database.** Plan for database switching if working across projects.
4. **constraints.txt CPU suffixes** will break on any non-Linux platform. Always strip them.
5. **RAGAS module** has a hard OpenAI dependency at import time regardless of your embedding config. Dummy key + local model config is the workaround.
