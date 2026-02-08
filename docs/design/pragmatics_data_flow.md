# How the Pragmatics Layer Works
## End-to-End Data Flow

*Written 2026-02-08. For vocabulary definitions, see `pragmatics_vocabulary.md`.*

---

## The Problem in One Sentence

Census data comes with numbers but not judgment. The pragmatics layer adds the judgment.

---

## Two Paths Into the System

There are exactly two ways pragmatic context reaches the caller LLM. Understanding both is essential.

### Path 1: Auto-Bundled (implicit)

The user asks for data. The MCP tool figures out what guidance applies and bundles it with the response automatically. The caller LLM never explicitly asked for guidance — it just gets it.

```
User: "What's the median income in rural Owsley County, KY?"
                    │
                    ▼
         Caller LLM interprets request
         Calls MCP tool: get_census_data
           state="21", county="189"
           variables=["B19013_001E"]
           product="acs5"
                    │
                    ▼
         ┌─────────────────────────────────┐
         │  MCP get_census_data             │
         │                                  │
         │  1. Validates parameters          │
         │  2. Calls Census API              │
         │  3. Auto-detects triggers:        │
         │     • product=acs5 → "period_     │
         │       estimate"                   │
         │     • geo=county → (no small-     │
         │       area trigger)               │
         │     • var=B19* → "dollar_values", │
         │       "inflation"                 │
         │     • always → "margin_of_error", │
         │       "reliability"               │
         │  4. Looks up matching context     │
         │  5. Bundles into response         │
         └────────────┬────────────────────┘
                      │
                      ▼
         Response to Caller LLM:
         {
           "data": { ... actual Census numbers ... },
           "pragmatics": {
             "guidance": [
               { "id": "ACS-DOL-001",
                 "text": "Income estimates are in nominal
                          dollars. To compare across years,
                          adjust for inflation using CPI-U.",
                 "latitude": "none" },
               { "id": "ACS-MOE-001",
                 "text": "Every ACS estimate has a margin
                          of error at the 90% confidence
                          level...",
                 "latitude": "narrow" }
             ],
             "related": [ ... thread-connected context ... ]
           },
           "source": { ... API provenance ... }
         }
```

**Key insight:** The caller LLM didn't ask for inflation guidance. The MCP saw an income variable (`B19*`) and automatically included it. This is the **parameter-matching** logic in `retriever.py:get_guidance_by_parameters()`.

The mapping rules are simple if/then — no LLM reasoning:

| If... | Then add triggers... |
|-------|---------------------|
| `product == "acs1"` | `population_threshold`, `1yr_acs` |
| `product == "acs5"` | `period_estimate` |
| `geo_level in (tract, block_group)` | `small_area` |
| Variable starts with `B19`, `B25` | `dollar_values`, `inflation` |
| `year in (2009, 2010)` | `break_in_series` |
| Always | `margin_of_error`, `reliability` |


### Path 2: Explicit Request (the caller asks)

The caller LLM decides it needs guidance before or instead of pulling data. It calls `get_methodology_guidance` directly with topic tags.

```
User: "Can I compare 2015 and 2022 ACS income data for my city?"
                    │
                    ▼
         Caller LLM recognizes:
           - temporal comparison question
           - dollar values involved
           - needs guidance before pulling data
         
         Calls MCP tool: get_methodology_guidance
           topics=["temporal_comparison", "dollar_values"]
           domain="acs"
                    │
                    ▼
         ┌─────────────────────────────────┐
         │  MCP get_methodology_guidance    │
         │                                  │
         │  1. Takes topics as-is           │
         │     (these ARE the triggers)     │
         │  2. Searches loaded packs for    │
         │     context items whose          │
         │     `triggers` field contains    │
         │     any matching topic           │
         │  3. For each match, traverses    │
         │     thread edges (max_depth=2)   │
         │     to find related context      │
         │  4. Returns guidance + related   │
         └────────────┬────────────────────┘
                      │
                      ▼
         Response includes:
         - CMP-001: "Don't compare 1-year to 5-year..."
         - DOL-001: "Adjust for inflation using CPI-U..."
         - Related (via thread): BRK-001: "Known breaks
           in ACS series at 2005, 2013, 2020..."
```

**Key insight:** The caller LLM chose which topics to send. This is where ADR-003 matters — you need a reasonably capable LLM to know that a temporal comparison of income involves both `temporal_comparison` and `dollar_values` triggers.

---

## What Happens Inside: Trigger Matching

The word "trigger" does double duty, which causes confusion. Here's the precise definition:

**Triggers are index keys stored on each context item.** They're the tags that make a piece of context findable. A context item about inflation adjustment might have:

```json
{
  "context_id": "ACS-DOL-001",
  "triggers": ["dollar_values", "inflation", "income_comparison", "cpi"],
  "context_text": "Income estimates are in nominal dollars...",
  "latitude": "none"
}
```

**Topics are what the caller sends.** When the caller sends `topics=["dollar_values"]`, the retriever scans all loaded context items and returns those where `"dollar_values"` appears in their `triggers` list.

**It's just tag matching.** No embeddings, no semantic search, no reasoning. The caller says "I need context tagged `dollar_values`" and the system returns everything tagged `dollar_values`. Simple.

```
Caller sends topics ──→ matched against ──→ triggers on context items
(what I need)                               (what I'm tagged with)
```

---

## Thread Traversal: Following Connections

After finding direct matches, the retriever follows **thread edges** to find related context. This is graph traversal, not search.

Each context item can have edges to other context items:

```
ACS-DIS-001 (data swapping/suppression)
    │
    ├──relates_to──→ ACS-SUP-001 (suppression rules)
    │
    └──relates_to──→ ACS-DIS-003 (**, -, *** symbols)
                         │
                         └──relates_to──→ ACS-MOE-002 (CV thresholds)
```

If you query for `["suppression"]` and match ACS-DIS-001, the traversal automatically pulls in ACS-SUP-001 and ACS-DIS-003 (depth 1), and ACS-MOE-002 (depth 2).

**Three edge types:**

| Edge | Meaning | Example |
|------|---------|---------|
| `inherits` | Parent pack's general version applies | CEN-GEO-001 inherits GEN-TV-001 |
| `relates_to` | Topically connected | DIS-001 relates to SUP-001 |
| `applies_to` | Specific application of general principle | *(future use)* |

---

## Latitude: What the Caller Does With It

Latitude tells the caller LLM how much freedom it has when applying each piece of context. It's metadata *about* the guidance, not the guidance itself.

```
Caller receives:
  { text: "ACS does NOT use differential privacy.", latitude: "none" }
  { text: "CV > 40% is usually unreliable.",       latitude: "narrow" }
  { text: "Consider SAIPE for county poverty.",     latitude: "wide" }

Caller's reasoning:
  "none"   → I must state this as fact. No wiggle room.
  "narrow" → I should follow this unless I have a specific reason not to.
  "wide"   → I should mention this but the user's context might override.
  "full"   → Background info. Use my judgment.
```

The MCP doesn't enforce latitude. It's a signal to the caller LLM about how to weight the context in its reasoning. A well-prompted caller will treat `none` as hard constraints and `full` as optional background.

---

## The Physical Architecture

### Where things live:

```
staging/                          ← ASSERTED (human-verified source of truth)
  ├── general_statistics/
  │   └── temporal.json           ← 1 context item
  ├── census/
  │   └── geography.json          ← 1 context item
  └── acs/
      ├── manifest.json           ← pack metadata + version
      ├── margin_of_error.json    ← 3 context items
      ├── population_threshold.json ← 3 items
      ├── disclosure_avoidance.json ← 3 items
      ├── threshold.json          ← 2 items
      ├── independent_cities.json ← 1 item
      └── ... (12 category files)

          │
          │  python scripts/compile_all.py
          ▼

packs/                            ← AUGMENTED (compiled, shippable)
  ├── general_statistics.db       ← SQLite: context + threads
  ├── census.db                   ← inherits general_statistics
  └── acs.db                      ← inherits census
```

### The inheritance chain:

```
general_statistics.db   (GEN-* items)
        ▲ inherits
    census.db           (CEN-* items)
        ▲ inherits
      acs.db            (ACS-* items, 27 total)
```

When you `load_pack("acs")`, it automatically loads all three. Queries search across the full chain.

### The authoring pipeline:

```
Source documents (ACS handbook, methodology docs)
        │
        │  Manual extraction (today)
        │  LLM-assisted extraction (future: MinerU + agent swarms)
        ▼
Neo4j `pragmatics` database       ← AUTHORING ENVIRONMENT
  (27 Context nodes, 16 RELATES_TO edges, 17 BELONGS_TO edges)
        │
        │  scripts/neo4j_to_staging.py
        ▼
staging/*.json                     ← ASSERTED (validated against Pydantic)
        │
        │  scripts/compile_all.py
        ▼
packs/*.db                         ← AUGMENTED (shipped with MCP)
        │
        │  (reverse sync)
        │  scripts/staging_to_neo4j.py
        ▲
staging/*.json
```

---

## Concrete Example: Full Round Trip

**Query:** "What's the poverty rate in a small rural tract in Kentucky?"

**Step 1 — Caller LLM interprets** and calls `get_census_data`:
- state="21" (KY), county="189" (Owsley), tract="*"
- variables=["B17001_001E", "B17001_002E"]
- product="acs5"

**Step 2 — MCP auto-detects triggers** from parameters:
- `product=acs5` → `["period_estimate", "5-year"]`
- `geo_level=tract` → `["small_area", "block_group"]`
- Always → `["margin_of_error", "reliability"]`

**Step 3 — Retriever searches loaded packs** for context items whose `triggers` field contains any of: `period_estimate`, `small_area`, `margin_of_error`, `reliability`

**Step 4 — Matches found** (example):
- ACS-PER-001: "5-year estimates represent a 60-month average..." (latitude: narrow)
- ACS-THR-001: "Pop <1,000, CV can exceed 100%..." (latitude: narrow)
- ACS-THR-002: "Pop <5,000, proactively warn about MOE..." (latitude: narrow)
- ACS-MOE-001: "Every ACS estimate has a margin of error..." (latitude: narrow)
- ACS-MOE-002: "CV < 15% reliable, 15-30% caution..." (latitude: narrow)

**Step 5 — Thread traversal** from each match (depth 2):
- ACS-THR-001 →relates_to→ ACS-POP-003 (5-year availability)
- ACS-THR-001 →relates_to→ ACS-MOE-003 (5-year vs 1-year precision)
- ACS-MOE-001 →relates_to→ ACS-MOE-002 →relates_to→ ACS-MOE-003

**Step 6 — Bundle and return:**
```json
{
  "data": { "B17001_001E": "4500", "B17001_002E": "2100", ... },
  "pragmatics": {
    "guidance": [ ... 5 direct matches ... ],
    "related": [ ... 3 thread-traversed items ... ],
    "sources": [{"document": "ACS-GEN-001", "section": "Ch. 7"}, ...]
  }
}
```

**Step 7 — Caller LLM reasons** with the bundled context:
> "The poverty rate is approximately 47% (2,100/4,500). However, this is a 5-year average (2018-2022), not a point-in-time snapshot. At the tract level in a county with population under 5,000, the margin of error may be significant — the coefficient of variation likely exceeds 30%, meaning this estimate should be used with caution. Consider using the county-level estimate for more reliable figures."

The caller didn't need to know any of this beforehand. The pragmatics layer told it.

---

## What Each Component Is Responsible For

| Component | Does | Does NOT |
|-----------|------|----------|
| **Caller LLM** | Interprets user question, selects topics, reasons with context, explains to user | Look up triggers, traverse threads, validate parameters |
| **MCP tools** | Validates parameters, calls Census API, matches triggers, traverses threads, bundles pragmatics | Interpret user intent, reason about fitness-for-use, decide what to tell user |
| **Retriever** | Tag matching (topics → triggers), thread traversal, auto-bundling from parameters | Semantic search, embedding-based matching, LLM reasoning |
| **Pack (SQLite)** | Stores context + threads + pack metadata, supports fast lookup | Authoring, versioning, collaborative editing |
| **Neo4j** | Authoring, graph visualization, collaborative editing, schema evolution | Runtime serving (too heavy, wrong tool) |
| **Staging JSON** | Source of truth (asserted), Pydantic-validated, human-readable | Runtime queries (must be compiled first) |

---

## Common Misconceptions

**"Triggers are guidance."** No. Triggers are index keys. They make context *findable*. The guidance is in `context_text`.

**"Topics and triggers are different things."** They're the same strings used in different contexts. Topics are what the caller sends. Triggers are what context items are tagged with. The retriever matches them.

**"Latitude is a weight."** No. Weight implies magnitude (how much does this matter?). Latitude implies freedom (how much can you deviate?). A piece of context can be extremely important (you'd better read it) but have `full` latitude (you can interpret it however you want).

**"The pragmatics layer does reasoning."** No. It does lookup and traversal. All reasoning happens in the caller LLM. The pragmatics layer is a library, not a librarian.

**"Thread traversal is search."** No. It's graph walking. Search finds things you don't know exist. Traversal follows known connections from things you already found. The retriever does search (tag matching) first, then traversal second.
