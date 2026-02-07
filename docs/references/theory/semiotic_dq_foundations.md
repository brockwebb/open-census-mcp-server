# Semiotic Data Quality Foundations

References supporting the pragmatics layer architecture.

## The Gap We're Filling

> "Syntactic tests ask 'does this data obey the formal rules?', while pragmatic tests ask 'is this data actually good enough for this specific use and user?'"
> — Semiotic DQ Thesis (2022)

Existing tools cover syntax and semantics. **No standard tools exist for pragmatics.**

## Core Framework Papers

### Semiotic Principles for Metadata Auditing
- **Source:** [research.amanote](https://research.amanote.com/publication/f5oI3HMBKQvf0BhivObD/semiotic-principles-for-metadata-auditing-and-evaluation)
- **Validates:** Thread traversal as "syntagmatic rules over records"

### Semiotic DQ for Behavioral Data (2022 Thesis)
- **Source:** [diva-portal.org](https://www.diva-portal.org/smash/get/diva2:1737820/FULLTEXT01.pdf)
- **Validates:** Latitude concept maps to "unusable / usable with caveats / fit-for-purpose"

### DataKitchen: Syntax-Semantics-Pragmatics Gap
- **Source:** [datakitchen.io](https://datakitchen.io/the-syntax-semantics-and-pragmatics-gap-in-data-quality-validate-testing/)
- **Validates:** Industry recognition that existing tools miss pragmatics

### Semiotics in Scientific Data Quality
- **Source:** [honghuang.myweb.usf.edu](http://honghuang.myweb.usf.edu/pub2/Huang_JIS.pdf)
- **Validates:** Context-as-signs approach

## Architecture Validation

| Our Concept | Literature Support |
|-------------|-------------------|
| Pragmatics layer | "fitness-for-use from user/decision perspective" |
| Latitude levels | "minimum viable quality thresholds per use" |
| Thread traversal | "syntagmatic rules" + "corpus boundaries" |
| Pack bundles | "metadata catalog with intended use, known unsuitable uses" |
| LLM handles syntax/semantics | Schema validators + OWL reasoners exist; pragmatics doesn't |

## Existing Toolchains (What We Don't Build)

**Syntactic:** Great Expectations, dbt tests, JSON Schema, SDMX validators
**Semantic:** OWL/RDF, Protégé, SPARQL reasoners

## What We Build

**Pragmatic:** Context items, latitude, thread traversal, pack compilation, docstring injection
