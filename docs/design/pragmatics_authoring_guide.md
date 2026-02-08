# Pragmatics Authoring Guide
# How to Add Knowledge to the Census MCP

*Created: 2026-02-08*
*Vocabulary: see `pragmatics_vocabulary.md` (normative)*

---

## Overview

The Census MCP encodes expert statistical knowledge as **pragmatics packs** —
structured context items compiled to SQLite and served to LLM agents at query time.

**The separation:** The agent prompt teaches *how to think*. Packs teach *what to know*.
If you're adding domain knowledge, it goes in a pack. If you're adding reasoning
behavior, it goes in the prompt (and you should have a very good reason).

---

## What Goes in a Pack

Context items answer: **"What would an expert statistician tell a colleague
before they use this data?"**

Good context items:
- Population thresholds for data availability
- Formulas (SE from MOE, CV calculation)
- Comparability constraints (don't mix 1-year with 5-year)
- Geographic quirks (independent cities, consolidated governments)
- Temporal breaks (methodology changes, COVID disruption)
- Suppression rules and data quality signals
- Inflation adjustment requirements for dollar values

Bad context items (don't belong in packs):
- How to interpret a specific estimate (that's LLM reasoning)
- Policy recommendations ("this means the city should...")
- Causal claims ("poverty causes...")
- Tool usage instructions (that's the agent prompt)

---

## File Locations

```
staging/acs.json              ← Source of truth (version controlled)
staging/census/               ← Census-wide pack
staging/general_statistics/   ← Survey-agnostic statistics
packs/acs.db                  ← Compiled artifact (gitignored, rebuilt from staging)
scripts/compile_pack.py       ← Compiler: JSON → SQLite
scripts/compile_all.py        ← Batch compiler
```

You edit `staging/*.json`. You never edit `packs/*.db` directly.

---

## Adding a New Context Item

### Step 1: Choose the Pack

| Pack | Use When |
|------|----------|
| `acs` | ACS-specific methodology (MOE formulas, period estimates, product rules) |
| `census` | Census-wide (geography hierarchy, FIPS codes, decennial vs ACS) |
| `general_statistics` | Survey-agnostic (sampling theory, significance testing) |

New packs can be created for other surveys (CPS, SIPP) following the same pattern.

### Step 2: Write the Context Item

Add to the `contexts` array in the appropriate `staging/*.json`:

```json
{
  "context_id": "ACS-DIS-001",
  "domain": "acs",
  "latitude": "narrow",
  "context_text": "Starting with the 2020 vintage, Census Bureau applies differential privacy to some tabulations. Small cell counts may be perturbed. This primarily affects tract and block group estimates for small demographic subgroups.",
  "source": "ACS-GEN-001, Ch. 9",
  "tags": ["disclosure_avoidance", "differential_privacy", "small_area", "data_quality"]
}
```

### Field Reference

| Field | Required | Description |
|-------|----------|-------------|
| `context_id` | Yes | Unique ID. Convention: `{PACK}-{CATEGORY}-{NNN}`. Examples: `ACS-MOE-001`, `CEN-GEO-003`. |
| `domain` | Yes | Which pack domain: `"acs"`, `"census"`, `"general"` |
| `latitude` | Yes | How much flexibility the LLM has. See below. |
| `context_text` | Yes | The expert knowledge. 1-3 sentences. Factual, actionable. No jargon without explanation. |
| `source` | Yes | Provenance. Document ID + section. `"ACS-GEN-001, Ch. 7"`. See `docs/references/CATALOG.md`. |
| `tags` | Yes | Array of topic strings for retrieval. These must match what the agent queries via `get_methodology_guidance`. |

### Latitude Values

| Value | Meaning | Example |
|-------|---------|---------|
| `none` | Hard constraint. No flexibility. | "1-year estimates require 65K+ population" |
| `narrow` | Strong guidance. Deviate only with justification. | "CV above 40% is too unreliable for most uses" |
| `wide` | Context-dependent. Multiple valid approaches. | "5-year has smaller MOE than 1-year" |
| `full` | Background information. FYI only. | "ACS replaced the Census long form in 2005" |

**Rule of thumb:** If an expert would say "never do X" → `none`. If "usually do X" → `narrow`.
If "it depends" → `wide`. If "FYI" → `full`.

### Tags (How Items Get Retrieved)

Tags connect context items to queries. When the LLM calls
`get_methodology_guidance(topics=["small_area", "margin_of_error"])`,
the retriever matches those topics against tags.

**Existing tags** (use these when applicable):
```
geography, small_area, population_threshold, margin_of_error,
reliability, comparison, temporal, period_estimate, suppression,
data_availability, dollar_values, inflation, income, formula,
estimate_selection, significance, cv_threshold, labeling,
interpretation, overlap, trend_analysis, block_group, 5-year,
1-year, supplemental, statistical_testing
```

**Adding new tags:** Just use them. No registry required. But prefer existing
tags when they fit — it increases the chance your item gets surfaced.

### Step 3: Add Thread Edges (Optional but Recommended)

Thread edges connect related context items so the retriever can follow paths.
Add to the `threads` array in the same JSON file:

```json
{
  "source": "ACS-DIS-001",
  "target": "ACS-SUP-001",
  "edge_type": "relates_to"
}
```

**Edge types:**
- `relates_to` — general association (most common)
- `specializes` — target is a more specific case of source
- `depends_on` — source requires understanding of target first

**When to add edges:**
- New item about small area reliability? → Link to MOE items.
- New item about geographic quirk? → Link to geography items.
- New item about data product? → Link to population threshold items.

Threads are for retrieval depth, not ontology. Don't over-connect.

### Step 4: Compile

```bash
# Single pack
python scripts/compile_pack.py staging/acs.json packs/acs.db

# All packs
python scripts/compile_all.py
```

### Step 5: Validate

```bash
# Run tests
pytest tests/ -v

# Specifically test pack round-trip
pytest tests/unit/test_pragmatics.py -v
```

### Step 6: Test Live

Restart Claude Desktop (the server re-reads packs on startup).
Query with relevant topics to confirm your item surfaces:

```
get_methodology_guidance(topics=["disclosure_avoidance", "small_area"])
```

---

## ID Convention

```
{PACK_PREFIX}-{CATEGORY}-{NNN}

ACS-POP-001   ← ACS pack, population category, item 1
ACS-MOE-002   ← ACS pack, margin of error category, item 2
CEN-GEO-003   ← Census pack, geography category, item 3
GEN-SIG-001   ← General statistics pack, significance category, item 1
```

**Categories in use:** POP, MOE, CMP, PER, DOL, GEO, BRK, SUP
**Available for new content:** DIS (disclosure), THR (threshold), EQV (equivalence), IND (independent cities)

---

## Source Document Registry

All sources must be registered in `docs/references/CATALOG.md`.

| Document ID | Title |
|-------------|-------|
| ACS-GEN-001 | Understanding and Using ACS Data (2020) |

If citing a new source, add it to the catalog first.

---

## Immediate Content Needed (G.10, G.11)

These items were identified by the three-model comparison test (G.4) as gaps:

### Disclosure Avoidance (G.10)
- Differential privacy in post-2020 vintages
- Small cell suppression patterns
- What "0" or "-" means in published tables

### Population Thresholds + Geographic Equivalence (G.11)
- Proactive warning when tract population is very small (<1,000)
- "Tract effectively equals county" pattern for tiny jurisdictions
- Guidance on when tract-level adds information vs. noise

### Independent Cities (G.7)
- Virginia independent cities (no parent county in FIPS hierarchy)
- Baltimore, St. Louis, Carson City (same pattern)
- How to handle county-equivalent geography

---

## Anti-Patterns

**Don't write rules.** Write context. 
- Bad: "You must always adjust for inflation when comparing income."
- Good: "When comparing dollar-denominated estimates across years, adjust for inflation. Multiyear estimates are already adjusted to the final year of the period."

**Don't duplicate the prompt.** The prompt says "ground yourself first." The pack says "here's what to ground in."

**Don't write LLM instructions.** Context items are facts and guidance for a human expert. The LLM reads them and decides what to do. You're not prompting — you're informing.

**Don't over-tag.** 3-6 tags per item. If everything is tagged with everything, retrieval loses specificity.

**Don't skip sources.** Every context item must trace to a source document. Unsourced expert opinion is not auditable.
