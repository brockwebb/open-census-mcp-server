# Concept of Operations (ConOps)
## Census MCP Server — Pragmatics-First Statistical Consultant

*Version 1.0 — February 2026*

---

## 1. Problem Statement

Federal AI-ready data guidance addresses syntax (APIs, schemas) and semantics (metadata, variable definitions). It does not address pragmatics — the expert knowledge of whether and how to use data for a specific purpose.

An LLM connected to the Census API can return correct numbers. Correct numbers are not the same as valid analysis. Without encoded expert judgment, AI systems:

- Use 1-year ACS estimates for populations under 65,000
- Fail to flag unacceptable margins of error
- Compare across methodology breaks without caveat
- Return Census data when administrative records are the better source
- Treat CDPs as stable geographies

These are not retrieval failures. They are consultation failures. The system returns what was asked for instead of what should have been provided.

## 2. System Purpose

The Census MCP Server is an AI statistical consultant that provides U.S. Census data through the Model Context Protocol with expert judgment attached. It encodes the fitness-for-use knowledge that takes practitioners years to learn and makes it available at query time.

**Core design principle:** The MCP doesn't just serve data — it serves data with judgment.

## 3. Stakeholders

| Stakeholder | Role | Need |
|-------------|------|------|
| **End user** | Asks questions about demographics | Accurate data with appropriate caveats, redirects when Census isn't the right source |
| **Host LLM** | Receives MCP tool descriptions, decides actions | Pragmatic context compiled into tool docstrings BEFORE it acts |
| **MCP operator** | Deploys and maintains the server | Single-artifact deployment, versioned packs, clear update path |
| **Domain expert** | Authors and reviews pragmatic context | Structured authoring format, provenance tracking, review workflow |

## 4. Operational Concept

### 4.1 Query Flow

```
User question (natural language)
        │
        ▼
   Host LLM receives tool descriptions
   (pragmatic context already compiled into docstrings)
        │
        ▼
   Host LLM decides: call tool, redirect, or caveat
        │
        ├── Call tool → MCP resolves geography, retrieves data,
        │               attaches runtime context
        │
        ├── Redirect → "Census isn't the right source for this.
        │               Consider [alternative]."
        │
        └── Caveat → "I can get this, but you should know..."
        │
        ▼
   Response with data + expert judgment
```

### 4.2 Two-Phase Context Injection

**Phase 1 — Compile-time (before query):**
Pack-level context is compiled into MCP tool docstrings when the server starts. The host LLM reads these descriptions and has pragmatic context available for every tool decision.

**Phase 2 — Runtime (during query):**
Query-specific context is retrieved by traversing threads relevant to the detected domain, geography, variable, and time period. This context is included in the tool response alongside the data.

### 4.3 The Pragmatics Layer

The system implements a pragmatics layer using the vocabulary defined in the project's normative reference (`pragmatics_vocabulary.md`). Key terms:

| Term | What It Is |
|------|------------|
| **Pack** | Domain-specific, shippable bundle of context (e.g., ACS pack) |
| **Thread** | Connected path through the knowledge graph; what you pull when a query matches |
| **Context** | The expert knowledge inside a thread — what a practitioner would tell you |
| **Latitude** | How much freedom to bend: `none`, `narrow`, `wide`, `full` |

Packs inherit. The ACS pack inherits from the Census pack, which inherits from General Statistics. Specialist context overrides general context on the same condition.

## 5. System Boundaries

### 5.1 What This System Does

- Resolves natural language geography to Census FIPS codes
- Retrieves American Community Survey data via Census API
- Compiles pragmatic context into tool descriptions and responses
- Flags fitness-for-use issues (population thresholds, MOE, vintage)
- Redirects to better sources when Census data is inappropriate
- Communicates uncertainty relative to the user's purpose

### 5.2 What This System Does Not Do

- Replace the Census API (it wraps it with judgment)
- Provide real-time or streaming data
- Perform statistical modeling or forecasting
- Store or cache user data
- Make policy recommendations
- Serve as a general-purpose data warehouse

### 5.3 Survey Scope

**v1:** American Community Survey (1-year and 5-year)
**Future expansion packs:** Decennial Census, SAIPE, PEP, CPS

## 6. Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **SQLite for shipping packs** | Single file, zero dependencies, Python stdlib, queryable at runtime, portable |
| **Context not rules** | LLMs reason with information, not compliance directives. Context can be weighted and bent; rules can't. |
| **Latitude not severity** | Freedom to bend, not punishment. Exploration space, not magnitude. |
| **Compile to docstring** | Context reaches the LLM before it decides to act, not after |
| **Pack inheritance** | Avoids duplication. General knowledge flows down; specialist knowledge overrides up. |
| **Vocabulary lock** | Terms in `pragmatics_vocabulary.md` are normative. Don't drift. |

## 7. Normative References

| Document | Location | Purpose |
|----------|----------|---------|
| `pragmatics_vocabulary.md` | `docs/design/` | Canonical vocabulary — terms, schema, composition model |
| `pragmatics_reference_card.md` | `docs/design/` | Quick reference — semiotic origin, components, talking points |

## 8. Success Criteria

The system succeeds when it does what an expert would do, not when it returns the correct number. Specifically:

1. **Redirects when appropriate** — Tells user to use a different source when Census data isn't fit for purpose
2. **Flags reliability issues** — Communicates when estimates have unacceptable uncertainty for the question asked
3. **Applies vintage rules** — Uses correct ACS estimate type for the geography's population
4. **Caveats methodology breaks** — Notes when cross-year comparisons are invalid
5. **Disambiguates geography** — Resolves "St. Louis" to the correct jurisdiction before retrieving data

---

*This document defines what the system is and why. Requirements for how it must behave are in the SRS.*
