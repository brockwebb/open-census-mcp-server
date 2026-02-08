# Theoretical Foundations
## Frameworks That Inform the Architecture

*Established 2026-02-08. See ADR-004 for the architectural decision.*

---

## The Core Insight

Census data consultation is not a pipeline. It's an iterative reasoning process
where an expert continuously reorients against domain knowledge while gathering
and interpreting information. The architecture requires multiple complementary
frameworks because no single framework captures all three dimensions: how the
agent executes, how it thinks, and why some questions are harder than they appear.

---

## Three Frameworks, Three Layers

| Framework | Role | Layer | What It Answers |
|-----------|------|-------|-----------------|
| **ReAct** (Yao et al., 2022) | Execution pattern | What the agent *does* | "What action next?" |
| **OODA** (Boyd, 1976) | Cognitive model | How the agent *thinks* | "What does my expertise tell me?" |
| **Cynefin** (Snowden, 1999) | Diagnostic lens | Why the agent *loops* | "What kind of problem is this?" |

These are not competing. They nest:

```
ReAct loop:
│
├─ REASON (uses OODA internally):
│   ├─ OBSERVE: What is the user asking? What did the data show?
│   │   └─ Cynefin: Is this Clear, Complicated, Complex, or Chaotic?
│   ├─ ORIENT:  What does my expertise say? ← PRAGMATICS LIVE HERE
│   └─ DECIDE:  What tool to call? What to clarify? Ready to deliver?
│
├─ ACT: Call MCP tools. Deliver answer. Ask user for clarification.
│
└─ OBSERVE result → feeds next REASON step (or exit)
```

---

## ReAct: The Execution Pattern

**Source:** Yao, S., et al. (2022). "ReAct: Synergizing Reasoning and Acting in Language Models."

**Pattern:** Reason → Act → Observe → repeat.

**Why it's right for us:** ReAct is the established standard for tool-using LLM agents.
It's what Sonnet/Opus naturally do when given MCP tools. The agent reasons about what
to do, calls a tool, observes the result, and reasons again. No need to invent a
custom execution loop.

**What ReAct lacks:** "Reason" is undifferentiated. It doesn't distinguish between
parsing the situation, consulting expertise, and forming a plan. It also doesn't
explain why some queries need one loop and others need five. That's where OODA and
Cynefin fill the gap.

---

## OODA: The Cognitive Model

**Source:** Boyd, J.R. (1976). "Destruction and Creation." Unpublished manuscript.
Boyd, J.R. (1987). "A Discourse on Winning and Losing." Briefing slides.

**Loop:** Observe → Orient → Decide → Act

**Why it's right for us:** OODA gives us the Orient step that ReAct lacks. Orientation
is where expertise lives — it's the mental model the expert brings to every
observation. A novice and a senior statistician can observe the same data. They
orient differently because they have different expertise.

**The key insight:** Pragmatics are not something the system optionally consults.
They are the orientation layer that makes every observation, decision, and action
intelligent. They are always present, like a consultant's years of training — not a
reference book on a shelf.

**How pragmatics map to OODA:**
- **Observe:** Parse the user's question. Parse the data returned by the API.
- **Orient:** Consult the pragmatics layer. What does statistical expertise say about
  this geography, this variable, this comparison? This is where fitness-for-use
  judgment enters.
- **Decide:** Form a response strategy. Do I need more data? Should I warn about
  reliability? Should I suggest a different geography level?
- **Act:** Deliver the answer, call another tool, or ask the user to clarify.

---

## Cynefin: The Diagnostic Lens

**Source:** Snowden, D.J. (1999). "Liberating Knowledge." CBI Business Guide.
Snowden, D.J. & Boone, M.E. (2007). "A Leader's Framework for Decision Making."
Harvard Business Review.

**Domains:** Clear → Complicated → Complex → Chaotic → Confused

**Why it's right for us:** Census consultation spans multiple Cynefin domains in a
single conversation. A question that *looks* Clear often turns out to be Complicated
or Complex once pragmatics orient the agent.

**Cynefin is a state within Observe.** It classifies what you're looking at.
Based on that classification, you orient differently:

| User asks | Looks like | Actually is | Why |
|-----------|-----------|-------------|-----|
| "Population of Baltimore?" | Clear | Clear | Simple lookup |
| "Income in Census Tract 45?" | Clear | Complicated | MOE may exceed estimate |
| "How has poverty changed?" | Complicated | Complex | Period overlap, boundary change, inflation, series break |
| "Compare these neighborhoods" | Complicated | Chaotic | CDPs shifted, vintage mismatch, no stable geography |

**This is why the agent needs to loop.** It can't know upfront how complex the
question actually is. Pragmatics are what tell it "this is harder than it looks."

---

## The Semiotic Triad

**Source:** Morris, C.W. (1938). "Foundations of the Theory of Signs."
International Encyclopedia of Unified Science, vol. 1, no. 2.

**The triad:**
- **Syntax** — structure, arrangement (*syntaxis* = arrangement)
- **Semantics** — meaning (*sēmantikos* = significant)
- **Pragmatics** — use in context (*pragmatikos* = fit for action)

**Why it's foundational:** This is the theoretical justification for the entire
pragmatics layer. Existing federal data infrastructure handles syntax (APIs, schemas,
formats) and semantics (metadata, definitions, variable labels). Nobody handles
pragmatics — the fitness-for-use judgment that tells you whether and how to use data
in a specific context.

**The gap in the literature:** Recent semiotic data quality work (2022) explicitly
identifies that syntactic and semantic testing tools exist, but pragmatic testing
requires custom construction. Our packs are that custom construction.

| Semiotic Layer | Federal Infrastructure | Our System |
|----------------|----------------------|------------|
| Syntax | API schemas, file formats, SDMX | Census API client, parameter validation |
| Semantics | Variable labels, table definitions, metadata | LLM training data (already knows this) |
| Pragmatics | **Gap — nothing exists** | **Pragmatics packs** |

**See:** `pragmatics_vocabulary.md` for how Morris's framework maps to our terminology.

---

## The Asserted/Augmented Distinction

**Source:** Standard knowledge graph engineering terminology.
Yáñez Romero, F. (2026). "Why LLMs Fail at Knowledge Graph Extraction."

**Asserted graph** = only explicitly stated information. Ground truth.
**Augmented graph** = inferred relationships, inheritance, cross-references added.

**Our mapping:**

| KG Layer | Our Layer | Contents |
|----------|-----------|----------|
| Asserted | `staging/*.json` | What methodology docs explicitly state |
| Augmented | `packs/*.db` | Compiled with inheritance edges, thread traversal |

**Why it matters:** Validation gates belong at the asserted→augmented boundary.
If a pack contains bad context, trace it back to staging (asserted). The compilation
step (augmented) adds structural value but must not introduce errors.

---

## TEVV: Test, Evaluate, Verify, Validate

**Source:** NIST AI Risk Management Framework (AI RMF 1.0), January 2023.

**Why it's here:** We apply TEVV to every task, not just the final evaluation.
Each phase has explicit exit criteria. Content authoring requires compilation +
test pass. The CQS evaluation protocol is the formal TEVV instrument for the
system as a whole.

---

## ADR-003: The Jobs Doctrine

**Source:** ADR-003-reasoning-model-requirement.md

**Principle:** Require Haiku 3.5 or higher reasoning capability as the minimum
caller. Don't build compensatory complexity for less capable models. Let them
become obsolete.

**Why it connects:** The three-framework architecture (ReAct + OODA + Cynefin) only
works with a caller that can actually reason. A less capable model can't diagnose
Cynefin domains, can't orient against pragmatics, can't decide when to loop. ADR-003
accepts this tradeoff explicitly.

---

## Frameworks We Considered and Rejected

| Framework | Why Considered | Why Rejected |
|-----------|---------------|-------------|
| PDCA (Deming) | Quality management loop | Manufacturing metaphor, doesn't model expertise |
| Chain-of-Thought | LLM reasoning technique | Describes token generation, not agent behavior |
| DSPy | Programmatic prompt optimization | Over-engineers the prompt; we need the cognitive model |
| Semantic Web / OWL | Knowledge representation | Academic baggage; LLM is our semantic layer |
| DIKW Pyramid | Data→Information→Knowledge→Wisdom | Too linear; we need loops, not pyramids |

---

## How to Cite These in Project Documents

When referencing frameworks in ADRs, design docs, or evaluation materials:

- **ReAct:** "ReAct execution pattern (Yao et al., 2022)"
- **OODA:** "OODA cognitive model (Boyd, 1976)"
- **Cynefin:** "Cynefin diagnostic framework (Snowden, 1999)"
- **Semiotic triad:** "Morris's semiotic triad (1938) — syntax, semantics, pragmatics"
- **Asserted/Augmented:** "KG asserted/augmented distinction"
- **TEVV:** "NIST AI RMF TEVV protocol (2023)"
- **Jobs Doctrine:** "ADR-003, requiring reasoning-capable callers"

---

*These frameworks are tools, not dogma. If a better model emerges, update this document.*
