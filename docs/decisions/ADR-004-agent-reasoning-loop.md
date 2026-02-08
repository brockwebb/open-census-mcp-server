# ADR-004: Agent Reasoning Loop Architecture

## Status
Accepted

## Context
During Phase 2 design, we oscillated between several architectures for how 
the LLM caller interacts with pragmatics and data:

1. **Tag lookup** — LLM explicitly calls `get_methodology_guidance(topics)` 
   before data retrieval. Problem: circular — if the LLM knows which tags to 
   request, it already knows enough to not need the guidance.

2. **Condition-matching engine** — MCP evaluates rules against request 
   parameters and fires matching guidance. Problem: puts reasoning into the 
   MCP, violating ADR-003's separation (MCP validates + retrieves, LLM reasons).

3. **Dumb pipeline** — Validate → Fetch → Auto-bundle guidance matched by 
   request parameters. Problem: treats the interaction as single-shot. Real 
   statistical consultation is iterative — the consultant may need to loop 
   back, ask clarifying questions, or try different approaches.

4. **Gemini's "Pragmatics Sandwich"** — Pre-fetch validation + post-fetch 
   enrichment with computed metrics (CV, reliability labels). Problem: 
   tunnel-visions on computable indicators. CV is one fitness metric among 
   dozens. Most pragmatic expertise is not reducible to arithmetic — it's 
   judgment about comparability, temporal validity, geographic pitfalls, 
   appropriate interpretation.

All four approached the problem as a pipeline. The actual problem is a 
reasoning loop.

## Decision

**The agent architecture combines three complementary frameworks:**

- **ReAct** (Yao et al., 2022) — the execution pattern (Reason → Act → Observe → repeat)
- **OODA** (Boyd, 1976) — the cognitive model within each reasoning step
- **Cynefin** (Snowden, 1999) — the diagnostic lens within Observe that 
  determines problem complexity

These are not competing frameworks. They operate at different layers.

### How They Fit Together

```
ReAct Execution Loop:
│
├─ REASON (uses OODA internally):
│   │
│   ├─ OBSERVE:  What is the user asking? What did the data show?
│   │   │
│   │   └─ Cynefin diagnosis: What kind of problem is this?
│   │       • Clear — straightforward lookup, answer directly
│   │       • Complicated — analyzable but needs expertise checks
│   │       • Complex — multiple factors, need to probe iteratively
│   │       • Chaotic — data contradicts, geography ambiguous, 
│   │         need to stabilize before proceeding
│   │
│   ├─ ORIENT:  What does my expertise tell me?
│   │   └─ Pragmatics layer — always present, always consulted.
│   │      Not optional. Not triggered. This IS the orientation.
│   │
│   └─ DECIDE:  What to do next?
│       • Pull data? Ask user to clarify? Flag a concern?
│       • Need another loop? Or ready to deliver?
│
├─ ACT:  Call MCP tools. Deliver answer. Ask user.
│
└─ OBSERVE result → feeds next REASON step (or exit)
```

### Why Three Frameworks

**ReAct alone** — gives you the loop but "Reason" is undifferentiated. 
Doesn't distinguish observation from orientation. Doesn't explain why 
some queries need one loop and others need five.

**OODA alone** — gives you the cognitive structure but isn't an established 
agent execution pattern. Would need to be translated into tool-use mechanics.

**Cynefin alone** — diagnostic only, not an action framework. Tells you 
what kind of problem you have but not what to do about it.

**Combined** — Cynefin classifies the problem (inside Observe), OODA 
structures the thinking (inside Reason), ReAct drives the execution. 
Each framework does what it's best at.

### Why Cynefin Matters for Census Data

A question that looks Clear is often Complicated or Complex:

| User asks | Looks like | Actually is | Why |
|-----------|-----------|-------------|-----|
| "Population of Baltimore?" | Clear | Clear | Simple lookup |
| "Income in Census Tract 45?" | Clear | Complicated | MOE may make estimate unreliable |
| "How has poverty changed?" | Complicated | Complex | Period overlaps, boundary changes, inflation, definition shifts |
| "Compare rural vs urban health" | Complicated | Complex | Different geographies, coverage bias, suppression patterns |

**Pragmatics are what tell the agent "this is harder than it looks."** 
Without them, the agent treats everything as Clear — look up number, 
report number. That's how you get confidently wrong statistical analysis.

### Where Pragmatics Live

Pragmatics are the ORIENT layer. They are:

- **Always bundled** with data responses — data without pragmatics is 
  incomplete. This is the core thesis: pragmatics make data AI-ready, 
  beyond schema (structure) and semantics (meaning).
- **The consultant's training** — always present in the background, 
  not a reference book optionally pulled from a shelf.
- **What distinguishes a statistician from a data retriever** — knowing 
  population thresholds, temporal validity, comparison rules, geographic 
  pitfalls, suppression patterns, coverage bias.

### MCP Role (unchanged from ADR-003)

The MCP provides the toolbox. It does not reason.

- **Validate:** Hard stops on impossible requests (data doesn't exist)
- **Fetch:** Census API calls
- **Bundle:** Attach relevant pragmatics to every data response

The LLM drives the ReAct loop. The MCP is what the LLM reaches for 
during ACT. The bundled pragmatics feed ORIENT on the next iteration.

### Agent Prompt = Maximizing Function

The agent system prompt encodes the loop as an objective function:

- **Maximize:** accurate, well-contextualized statistical consultation
- **Minimize:** misleading interpretation, false precision, invalid comparisons
- **Always:** surface limitations, uncertainty, and fitness-for-use caveats
- **When uncertain:** elicit clarification from the user (loop again)
- **Diagnose complexity first:** don't treat Complicated questions as Clear

## Consequences

- Agent prompt is the primary engineering artifact (not MCP logic)
- MCP remains simple: validate + fetch + bundle pragmatics
- Pragmatics content quality is the bottleneck (not code complexity)
- Evaluation measures consultation quality, not data retrieval accuracy
- Weaker models fail at the loop, not at the tools (ADR-003)
- Single-shot answers are the degenerate case (Clear domain), not the 
  design target
- The Cynefin framing gives us evaluation categories: does the agent 
  correctly identify when a question is harder than it looks?

## References

- Yao, S. et al. (2022). "ReAct: Synergizing Reasoning and Acting in 
  Language Models." ICLR 2023.
- Boyd, J.R. (1976). "Destruction and Creation." Unpublished manuscript.
- Boyd, J.R. (1987). "A Discourse on Winning and Losing." Briefing slides.
- Snowden, D.J. & Boone, M.E. (2007). "A Leader's Framework for Decision 
  Making." Harvard Business Review. (Cynefin framework)
- Morris, C.W. (1938). "Foundations of the Theory of Signs." — pragmatics 
  as the relationship between signs and their interpreters.
- ADR-003: Reasoning Model Requirement (minimum Sonnet-class caller)
