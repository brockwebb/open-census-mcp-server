# Session Log: 2026-02-08 — Pipeline Gap Discovery

## Summary

Fresh thread discovered that the Neo4j ↔ staging JSON round-trip scripts were never built, despite being identified as tech debt on 2026-02-07 and fully specified in architecture docs. This is a documentation continuity failure, not a design failure.

## What Happened

The 2026-02-07 session did excellent work:
- Designed the full pipeline (ADR-001, extraction_pipeline.md, knowledge_pack_management.md)
- Created the `pragmatics` Neo4j database
- Seeded 17 ACS context nodes + 6 thread edges + 1 Pack node
- Built compile scripts (staging JSON → SQLite)
- Validated the full chain manually

But the handoff document (2026-02-08_post_g6_prompt_slimming.md) focused on Phase 4A validation work and **did not mention:**
- The existence of the `pragmatics` Neo4j database
- The need for round-trip scripts
- The schema inconsistency between staging formats
- That `scripts/extract/` was empty (only `.gitkeep`)

CLAUDE.md also had **zero mention** of Neo4j, the `pragmatics` database, or the authoring pipeline.

Result: a fresh thread in the next session had no way to discover the pipeline existed. It saw `staging/acs.json` (flat file) and the authoring guide (which references flat file editing) and naturally assumed flat-file authoring was the workflow. The architecture docs existed but weren't linked from the entry points a new thread reads first.

## Root Cause Analysis

**The work got done. The handoff lost the thread.**

Specifically:
1. Tech debt was *identified* in session_2026-02-07_afternoon.md ("Need import script", "Need automated export script")
2. ADR-001 was *written* with the correct architecture
3. knowledge_pack_management.md was *written* with the correct workflow diagrams
4. But none of this was surfaced in:
   - CLAUDE.md (the first thing every thread reads)
   - The handoff document (the second thing every thread reads)
   - The pragmatics_authoring_guide.md (which tells people to edit flat JSON)

**Pattern:** Documentation exists in deep docs but isn't connected to entry points. New threads don't do archaeology — they read CLAUDE.md and the latest handoff, then start working. If it's not there, it doesn't exist to them.

## What Was Actually Broken

| Component | Expected State | Actual State |
|-----------|---------------|--------------|
| `pragmatics` Neo4j DB | Master authoring copy | ✅ Exists, 17 nodes seeded |
| `scripts/neo4j_to_staging.py` | Export Cypher → JSON | ❌ Does not exist |
| `scripts/staging_to_neo4j.py` | Import JSON → Cypher | ❌ Does not exist |
| `staging/acs.json` | Pydantic model format, in `staging/acs/` | ❌ Old flat format, wrong location |
| `staging/census/geography.json` | Pydantic model format | ✅ Correct format |
| `staging/general_statistics/temporal.json` | Pydantic model format | ✅ Correct format |
| CLAUDE.md Neo4j section | Documents database and pipeline | ❌ Missing entirely (fixed this session) |
| Neo4j node schema | Matches Pydantic model | ❌ Has `tags` not `triggers`, no `category`, flat `source` string |

## Schema Inconsistency Detail

**Pydantic canonical model** (`src/census_mcp/pragmatics/models.py`):
```python
class ContextItem(BaseModel):
    context_id: str
    domain: str
    category: str          # ← required
    latitude: str
    context_text: str
    triggers: list[str]    # ← "triggers" not "tags"
    thread_edges: list[ThreadEdge]
    source: Source | None   # ← structured object
```

**Neo4j nodes** (seeded from old format):
```
{tags: [...], source: "ACS-GEN-001, Ch. 7"}  # flat string, wrong field name
```

**staging/acs.json** (old format):
```
{tags: [...], source: "ACS-GEN-001, Ch. 7"}  # same old format
```

**staging/census/geography.json** (correct format):
```
{triggers: [...], source: {document: "...", extraction_method: "manual"}}
```

## Corrective Actions Taken This Session

1. ✅ Added Neo4j section to CLAUDE.md with database name, pipeline, known gaps
2. ✅ Added architecture doc links to CLAUDE.md
3. ✅ This lessons learned document
4. 🔲 Build `scripts/neo4j_to_staging.py` (export)
5. 🔲 Build `scripts/staging_to_neo4j.py` (import)
6. 🔲 Migrate Neo4j nodes to canonical schema
7. 🔲 Restructure `staging/acs.json` → `staging/acs/*.json` in correct format
8. 🔲 Update SRS to include pipeline script requirements

## Lessons Learned

### 1. CLAUDE.md Is the API Contract for AI Threads
If it's not in CLAUDE.md, it doesn't exist to the next thread. Deep architecture docs are necessary for humans doing archaeology. CLAUDE.md is what AI threads actually read. **Every operational fact must be in CLAUDE.md or directly linked from it.**

### 2. Handoffs Must Include Infrastructure State
The handoff doc was thorough about *what was accomplished* (G.4, G.6, G.9) but silent about *what infrastructure exists*. A handoff that says "we created a Neo4j database called `pragmatics`" would have prevented this entire session's discovery arc.

### 3. Tech Debt Logged ≠ Tech Debt Visible
Writing "Need export script" in a session log nobody reads is documentation theater. Tech debt needs to be in:
- CLAUDE.md (so AI threads see it)
- Implementation schedule (so it gets prioritized)
- Or ideally: a GitHub issue (so it's tracked)

### 4. Schema Divergence Is Inevitable Without Enforcement
Two weeks and three formats coexist. The Pydantic model should have been the ONLY way to create content from day one. The compile script should reject non-conforming JSON. Validation gates prevent drift.

### 5. The "Manual for Now" Trap
"We'll do it manually now and automate later" is a reliable way to never automate. The manual process works once, gets documented as tech debt, and then the next thread doesn't know the manual process existed. Build the script or accept that it won't happen.

## Pipeline Vision (Unchanged)

The architecture is correct. The implementation gap is the round-trip scripts:

```
Neo4j (pragmatics) ──► neo4j_to_staging.py ──► staging/*.json ──► compile_pack.py ──► packs/*.db
        ▲                                            │
        └──── staging_to_neo4j.py ◄──────────────────┘
```

Future scale: MinerU for PDF chunking → LLM agent swarms for extraction → Neo4j for graph authoring → automated export → CI compilation. But the foundation is these two scripts.
