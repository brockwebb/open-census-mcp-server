# Semiotic Data Quality Foundations

References supporting the pragmatics layer architecture.

## Core Framework Papers

### Semiotic Principles for Metadata Auditing
- **Source:** [research.amanote](https://research.amanote.com/publication/f5oI3HMBKQvf0BhivObD/semiotic-principles-for-metadata-auditing-and-evaluation)
- **Relevance:** Concrete auditing framework (syntagm, sign-functions, corpus boundaries) - validates our thread traversal approach

### Semiotic DQ for Behavioral Data (2022 Thesis)
- **Source:** [diva-portal.org](https://www.diva-portal.org/smash/get/diva2:1737820/FULLTEXT01.pdf)
- **Relevance:** Operationalizes pragmatic indicators (task adequacy, interpretability, context completeness) - validates our latitude concept

### DataKitchen: Syntax-Semantics-Pragmatics Gap
- **Source:** [datakitchen.io](https://datakitchen.io/the-syntax-semantics-and-pragmatics-gap-in-data-quality-validate-testing/)
- **Relevance:** Industry recognition that existing tools cover syntax/semantics but NOT pragmatics - validates our gap analysis

### Semiotics in Scientific Data Quality
- **Source:** [honghuang.myweb.usf.edu](http://honghuang.myweb.usf.edu/pub2/Huang_JIS.pdf)
- **Relevance:** Sign-relations among data, models, interpretations - validates context-as-signs approach

## Key Validations

| Our Architecture | Literature Support |
|------------------|-------------------|
| Pragmatics = fitness-for-use | Semiotic DQ thesis: "pragmatic tests ask 'is this data actually good enough for this specific use and user?'" |
| Latitude levels (none→full) | Maps to pragmatic thresholds: "unusable," "usable with caveats," "fit-for-purpose" |
| Thread traversal | Auditing framework's "syntagmatic rules over records" |
| Pack as domain bundle | "metadata catalog extended with intended use, known unsuitable uses" |
| LLM handles syntax/semantics | DataKitchen: schema validators + Great Expectations = syntactic; OWL/reasoners = semantic |

## Toolchain Mapping

What exists (we don't build):
- **Syntactic:** Schema validators, Great Expectations, dbt tests, SQL constraints
- **Semantic:** OWL/RDF, Protégé, SPARQL reasoners

What we build (pragmatics layer):
- Context items with latitude
- Thread traversal for query-relevant context
- Pack compilation for domain bundles
- Docstring injection for LLM grounding
