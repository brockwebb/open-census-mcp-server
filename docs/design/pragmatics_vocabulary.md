# Pragmatics Vocabulary
## The Terms We Use and Why

*Decided February 2026*

---

## The Stack

| Level | Term | What It Is | Why This Word |
|-------|------|------------|---------------|
| **Layer** | Pragmatics | The third semiotic dimension | Morris (1938). Established. Names the gap. |
| **Graph path** | Thread | Connected nodes traversed together | Graph-native. What you pull. What you follow. |
| **Collection** | Pack | Domain-specific, shippable bundle | Expansion pack. Repack with updates. Portable. |
| **Contents** | Context | What's in the thread | LLMs are context machines. It's what experts give you. |
| **Flexibility** | Latitude | How much freedom to bend | Navigation. Exploration space. Not a scalar like weight. |

---

## Pragmatics

**Origin:** Charles Morris, *Foundations of the Theory of Signs* (1938)

**The semiotic triad:**
- **Syntax** — structure, arrangement (*syntaxis* = arrangement)
- **Semantics** — meaning (*sēmantikos* = significant)  
- **Pragmatics** — use in context (*pragmatikos* = fit for action)

**Why it's right:** The Greek root *pragma* means "deed, act, thing done." Pragmatics is about what to *do* — and critically, what *not* to do. Current federal data frameworks handle syntax (APIs, schemas) and semantics (metadata, definitions). They don't handle pragmatics (fitness-for-use, expert judgment).

**Usage:**
- "The pragmatics layer encodes expert judgment about data use."
- "Metadata tells you what the data is. Pragmatics tells you whether and how to use it."

---

## Thread

**Origin:** Graph theory + textiles + conversation

**What it is:** A connected path through the knowledge graph. When you query, you don't get isolated nodes — you pull a thread that connects related context through inheritance, application, and relationship edges.

**Why it's right:** 
- Graph-native: threads are paths, not blobs
- Physical intuition: pull one thing, connected things follow
- Conversation: "let me pick up that thread" — continuity, connection
- Weaving: threads compose into fabric (the full context)

**Properties of a thread:**
- Has a starting point (triggered by query features)
- Traverses edges (inheritance, applies_to, relates_to)
- Collects context along the path
- Can branch and merge

**Usage:**
- "Pull the relevant threads for this query."
- "The ACS vintage thread connects to the general temporal validity thread."
- "These threads intersect at the small-geography node."

---

## Pack

**Origin:** Luggage + software (expansion packs) + compression

**What it is:** A domain-specific collection of threads and context that ships as a unit. The ACS pack. The CPS pack. Packs inherit from parent packs (ACS inherits from Census inherits from General Statistics).

**Why it's right:**
- **Expansion pack**: Add new domains without restructuring. Plug in the CPS pack.
- **Repack**: When knowledge updates, you repack. New vintage rules? Repack.
- **Trunk packing**: You pack what you need for THIS trip (query). Different trip, different pack contents.
- **Portable**: A pack ships with the MCP. Single artifact. Self-contained.

**Properties of a pack:**
- Has a domain (acs, cps, census, general_statistics)
- Inherits from parent pack(s)
- Contains threads specific to its domain
- Compiled to a shippable artifact (.db file)
- Versioned (repack on update)

**Usage:**
- "Ship the ACS pack with the MCP."
- "Load the CPS expansion pack."
- "Repack after the 2030 methodology changes."
- "The query packs threads from three domains."

---

## Context

**Origin:** Latin *contextus* — "a joining together, weaving"

**What it is:** The actual content inside a thread. What the expert would tell you before you touch the data. Not rules to obey — information to reason with.

**Why it's right:**
- LLMs are context machines. You're literally packing the context window.
- Experts give context, not commands: "Let me give you some context on this..."
- Context can be weighted, bent, interpreted. Rules can't.
- Etymology: weaving — context joins things together, like threads.

**What context includes:**
- Hard stops (data doesn't exist — but phrased as "this data doesn't exist," not "ERROR")
- Strong guidance (usually unreliable at this scale)
- Heuristics (consider this alternative source)
- Caveats (2020 collection was disrupted)
- Background (this variable was redesigned in 2016)

**What context is NOT:**
- Constraints (too rigid — can't bend)
- Rules (implies compliance, not judgment)
- Guardrails (implies boundaries, not navigation)
- Directives (implies commands, not information)

**Usage:**
- "The thread contains context about population thresholds."
- "Pack the relevant context into the docstring."
- "The model reasons with the context, including knowing when to bend."

---

## Latitude

**Origin:** Geography + navigation + freedom

**What it is:** How much freedom the reasoning has to bend, interpret, or deviate from the context. Not a scalar weight — a degree of exploration space.

**Why it's right:**
- Navigation metaphor: latitude is room to move, not magnitude
- Simulated annealing: exploration space, how far you can jump
- Expert judgment: knowing when you have latitude vs. when you don't
- Doesn't collide with LLM "temperature" (different concept)
- Doesn't collide with "weight" (that's magnitude, not freedom)

**The spectrum:**

| Latitude | Meaning | Example |
|----------|---------|---------|
| `none` | No freedom. Physics, law, or the data doesn't exist. | 1-year ACS isn't published below 65K pop. |
| `narrow` | Small freedom. Deviate only with strong justification. | CV > 40% is usually unreliable. |
| `wide` | Real freedom. Weigh it, but context-dependent. | SAIPE might be better, but ACS could work. |
| `full` | Just background. Reason freely. | This geography is a CDP. |

**Usage:**
- "This context has narrow latitude — don't bend without justification."
- "High-latitude context informs but doesn't constrain."
- "The model has no latitude on existence constraints."

---

## How They Compose

```
QUERY: "Median income in Severna Park"
              │
              ▼
┌─────────────────────────────┐
│  ROUTER                      │
│  Identifies:                 │
│  - domain: ACS               │
│  - geography: small CDP      │
│  - variable: income          │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  PACK SELECTION              │
│                              │
│  Load: ACS pack              │
│  (inherits from Census pack  │
│   inherits from General)     │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  THREAD TRAVERSAL            │
│                              │
│  Pull threads matching:      │
│  - small_geography           │
│  - income                    │
│  - cdp                       │
│  - vintage                   │
│                              │
│  Follow edges:               │
│  - inheritance (ACS→Census)  │
│  - applies_to (income vars)  │
│  - relates_to (MOE guidance) │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  CONTEXT COLLECTION          │
│                              │
│  From threads, gather:       │
│                              │
│  [none latitude]             │
│  "Pop <65K: 5-year only"     │
│                              │
│  [narrow latitude]           │
│  "Income MOE may exceed 20%" │
│                              │
│  [wide latitude]             │
│  "CDP boundaries can shift"  │
│                              │
│  [full latitude]             │
│  "Consider SAIPE for county" │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  COMPILE TO DOCSTRING        │
│                              │
│  Natural language context    │
│  injected into tool          │
│  description BEFORE the      │
│  LLM decides to act          │
└─────────────────────────────┘
```

---

## The Full Sentence

> "Load the **pack** for this domain. Pull the relevant **threads** by traversing the graph. Collect the **context** from each thread, noting its **latitude**. Compile into **pragmatics** that the model reads before acting."

---

## What This Vocabulary Avoids

| Avoided Term | Why |
|--------------|-----|
| Constraint | Too rigid. Can't bend. |
| Rule | Implies compliance. |
| Guardrail | Implies walls. We're navigating, not fencing. |
| Directive | Implies command. Context informs, doesn't command. |
| Schema | MDR hell. This is operational, not governance. |
| Ontology | Academic baggage. We're building, not philosophizing. |
| Taxonomy | Classification obsession. We care about traversal. |
| Weight | Scalar magnitude. Latitude is freedom, not mass. |
| Temperature | Already taken by LLM sampling. |
| Severity | Implies punishment. Latitude implies exploration. |
| Crystal | New Age baggage, even if the structure fit. |

---

## Schema Implication

The vocabulary maps to the database:

```sql
-- A piece of context
CREATE TABLE context (
    id INTEGER PRIMARY KEY,
    context_id TEXT UNIQUE,        -- e.g., 'ACS-POP-001'
    domain TEXT,                   -- which pack
    latitude TEXT,                 -- 'none', 'narrow', 'wide', 'full'
    context_text TEXT,             -- what the expert would say
    source TEXT                    -- provenance (for debugging)
);

-- Threads: how context connects
CREATE TABLE threads (
    from_context INTEGER REFERENCES context(id),
    to_context INTEGER REFERENCES context(id),
    edge_type TEXT,                -- 'inherits', 'applies_to', 'relates_to'
    PRIMARY KEY (from_context, to_context, edge_type)
);

-- Packs: domain collections
CREATE TABLE packs (
    pack_id TEXT PRIMARY KEY,
    pack_name TEXT,
    parent_pack TEXT REFERENCES packs(pack_id),
    version TEXT,
    compiled_date TEXT
);

-- Which context belongs to which pack
CREATE TABLE pack_contents (
    pack_id TEXT REFERENCES packs(pack_id),
    context_id INTEGER REFERENCES context(id),
    PRIMARY KEY (pack_id, context_id)
);
```

---

## Maintenance

**When to repack:**
- New survey vintage released
- Methodology changes (post-2030 Census)
- New domain added (expansion pack)
- Errors discovered in existing context

**How to repack:**
1. Update staging files (JSON source of truth)
2. Run compilation pipeline
3. Output new .db file
4. Ship with updated MCP
5. Version bump

**What doesn't change:**
- The vocabulary (this document)
- The schema structure
- The traversal logic
- The compilation pattern

---

## One-Liners for Different Audiences

**For statisticians:**
> "Pragmatics encodes the fitness-for-use judgment that metadata can't capture."

**For AI engineers:**
> "We pack domain-specific context threads into the prompt before the model acts."

**For data governance:**
> "It's the expert knowledge layer that connects your existing frameworks for machine consumption."

**For executives:**
> "The API gives you data. The pragmatics pack gives you the judgment to use it correctly."

---

*This is the vocabulary. Use it consistently. Don't drift.*
