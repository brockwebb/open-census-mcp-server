# DATA PRAGMATICS — Quick Reference Card

---

## Definition

**Data Pragmatics** is the fitness-for-use layer of data intelligence — the encoded expert knowledge of *constraints*, *quality thresholds*, *permissions*, and *epistemic confidence* that determines whether a given data source is appropriate for a specific analytical question in a specific context. It is the layer that tells you not *what* the data is, but *whether and how you should use it*.

---

## Origin of the Term

The term **pragmatics** comes from **Charles Morris (1938)**, who formalized the three branches of **semiotics** (the study of signs and meaning):

| Branch | Studies | Greek Root |
|--------|---------|------------|
| **Syntax** | Structure and form of signs | *syntaxis* — "arrangement" |
| **Semantics** | Meaning of signs | *sēmantikos* — "significant" |
| **Pragmatics** | Use of signs in context | *pragmatikos* — "fit for action" |

Morris drew "pragmatics" from the Greek *pragma* (πρᾶγμα) — **"deed, act, thing done."** The root is *prassein*: **"to do, to practice."**

**Why it's the right term:** Syntax tells you how data is structured. Semantics tells you what data means. Pragmatics tells you what to *do* with it — and critically, what *not* to do. The original Greek captures exactly the gap: moving from description to **action-appropriate use**. Morris himself defined pragmatics as the relationship between signs and their *interpreters* — the context-dependent, purpose-driven dimension. That's precisely what's missing from current AI-ready data frameworks.

---

## The Semiotic Stack Applied to Data

| Layer | What It Captures | Data Analog | Example |
|-------|-----------------|-------------|---------|
| **Syntax** | Structure, format, arrangement | File formats, schemas, APIs, column types | "This is a CSV with 12 columns" |
| **Semantics** | Meaning, definitions | Metadata, variable labels, code descriptions | "Column B08 is 'median household income'" |
| **Pragmatics** | Appropriate use in context | Fitness-for-use rules, expert judgment, constraints | "Don't use 1-yr ACS for populations under 65K" |

**Current federal guidance operates at syntax and semantics. The gap is pragmatics.**

---

## Components of the Pragmatic Layer

### 1. Constraints (validation rules)
The hard boundaries — conditions under which data is valid or invalid for a given use.
*Formal analog: SHACL (Shapes Constraint Language)*

> "IF population < 65,000 THEN source ≠ 1-Year ACS"
> "IF geography = school district THEN source ≠ Census (boundaries don't align)"

### 2. Quality Thresholds (fitness policies)
The conditional quality judgments — when data meets a standard and when it doesn't, relative to purpose.
*Formal analog: DQV (Data Quality Vocabulary)*

> "Margin of error > 30% of estimate → flag as unreliable for this use"
> "Sample size < N for subgroup → suppress or redirect"

### 3. Permissions & Prohibitions (use policies)
What you're allowed to do — and forbidden from doing — with specific data, including methodological requirements.
*Formal analog: ODRL (Open Digital Rights Language)*

> "This variable requires inflation adjustment before cross-year comparison"
> "Suppressed cells must not be reverse-engineered from marginal totals"

### 4. Epistemic Metadata (confidence/validity markers)
The degree of trust — why something is reliable or unreliable, and under what conditions.

> "This estimate is reliable because 5-yr pooling stabilizes small-area noise"
> "This time series breaks at 2020 due to methodology change — not comparable across boundary"

---

## The Trunk-Packing Principle

**The full knowledge graph is too large to load. Graph *fragments* are the key.**

Think of it like packing for a trip: you don't bring your entire closet — you assess the destination, the weather, the activities, and pack the right segments. An experienced traveler packs efficiently because they know what matters for *this specific trip*.

The same principle applies to pragmatic knowledge:

```
Query arrives
    ↓
Router assesses: what domain? what entities? what pitfalls?
    ↓
Retrieval pulls relevant graph FRAGMENTS (not the whole graph)
    ↓
Compilation packs the "trunk" — constraints as natural language
    ↓
LLM reasons with the right segments in context
    ↓
Validator checks the plan against constraints
```

**You can't stuff 5,000 Census rules into a context window. You retrieve the 5-15 that matter for THIS query.** The expertise is in knowing *which* fragments to pack — that's the OODA loop (Observe-Orient-Decide-Act) doing the pre-reasoning before reasoning.

From a graph perspective: you're not traversing the entire graph. You're extracting *subgraphs* — connected clusters of constraints relevant to the query's entities, geography, time period, and methodology requirements.

---

## Why Retrieval Accuracy Alone Is Insufficient

### The Limitation of Prompt-Response Evaluation
Existing approaches to evaluating LLM understanding of statistical data focus on retrieval accuracy:
can the system return the correct number from the correct source?

This is necessary but not sufficient. A system can return the **correct number** and still give the
**wrong answer**.

**What retrieval evaluation measures:**
- Can the LLM retrieve the correct value?
- Does it cite the right source?
- Is the number accurate?

**What it cannot reach:**
- Should the LLM have answered at all?
- Did it route to the *appropriate* source for the user's specific purpose?
- Did it communicate uncertainty relative to the use case?
- Did it apply valid methodology for the data characteristics?
- Would a domain expert have answered *differently*?

### Example: Right Number, Wrong Answer
A system returns "median household income = $X" for Severna Park, MD (CDP). The number matches
the Census API. But Severna Park's population (~39,500 per 2023 ACS 5-year, table DP05) means
only the 5-Year ACS produces reliable estimates for this geography. A system without pragmatic context might pull from 1-Year ACS — returning an accurate
retrieval from an inappropriate source.

**Retrieval evaluation measures whether the system got the right number. The hard problem is
whether the system did what an expert would do.**

### The Evaluation Gap

| Dimension | Retrieval Evaluation | Pragmatic Consultation |
|-----------|---------------------|----------------------|
| Success metric | "Got the right number" | "Did what an expert would do" |
| Failure mode detected | Wrong value returned | Right value, wrong source/method |
| Handles redirects | No — only tests if answer matches | Yes — "don't use Census for this" is a valid answer |
| Handles uncertainty | Barely — checks if caveats exist | Deeply — communicates fitness relative to purpose |

---

## One-Liner

> "Federal AI-ready data guidance solves syntax and semantics. Implementation reveals the missing layer is **pragmatics** — the expert knowledge of when, whether, and how to use data for a specific purpose."

---

*All data examples in this document reference publicly available Census Bureau products.
Population thresholds, table references, and geographic claims are verifiable against
data.census.gov and Census Bureau technical documentation.*

---

*Reference: Morris, C. W. (1938). Foundations of the Theory of Signs. University of Chicago Press.*
*Context: FCSM 2026 Presentation Development*
