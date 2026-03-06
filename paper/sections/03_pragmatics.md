# Pragmatics: Structured Expert Judgment

<!-- Registry references: PL-001, PL-004, DET-001–004 -->
<!-- Citation files: core_argument.md, federal_data_evolution_arc.md, d3_uncertainty_deep_dive.md -->

## The Semiotic Foundation

Charles Morris's [-@morris1938] *Foundations of the Theory of Signs* introduced a three-part framework for understanding how signs function: syntax concerns the formal relationships between signs, semantics concerns the relationship between signs and the objects they represent, and pragmatics concerns the relationship between signs and their interpreters, specifically the contextual conditions under which signs are appropriately used. Applied to federal statistical data, these three layers correspond to distinct infrastructure investments and distinct institutional responsibilities (@fig-semiotic-stack).

![The semiotic stack applied to federal statistical data, after Morris [-@morris1938]. Syntax and semantics are mature; pragmatics is the missing layer.](assets/diagrams/fig_semiotic_stack.png){#fig-semiotic-stack width=6.5in}

*Syntax* encompasses the structural layer: APIs, machine-readable formats, data transmission protocols, and the formal rules governing how data is organized and accessed. This is the domain of open data mandates, format standards, and programmatic access. It is mature.

*Semantics* encompasses the meaning layer: variable descriptions, concept classifications, geographic hierarchies, and the metadata that allows a consumer to identify what a data element represents. This is the domain of documentation, catalogs, and AI-ready data initiatives. It is well-developed and continues to improve.

*Pragmatics* encompasses the judgment layer: the expert assessment of whether a particular data element is appropriate for a particular use, given the specific context of the question being asked. This is the domain of experienced statisticians, methodology specialists, and data stewards. It does not exist as a computationally deliverable resource in any federal statistical system.

The three layers are cumulative, not substitutable. An agency that has invested in syntax and semantics has completed two of three necessary steps for responsible AI-mediated data access. The third step, encoding the fitness-for-use judgments that practitioners apply but have never formalized for machine delivery, is the subject of this paper. The distinction between semantics and pragmatics is critical to understanding why metadata alone is insufficient for statistical consultation.

| | Semantics | Pragmatics |
|---|---|---|
| **Answers** | What is this number? | Is this number fit for my purpose? |
| **Source** | Data dictionaries, API metadata | Methodology handbooks, technical documentation, expert judgment |
| **Example** | B19013_001E = median household income, inflation-adjusted dollars, ACS 5-year | MOE may render this estimate unreliable at pop. 8,000; 5-year = 60-month rolling average; comparing to decennial requires methodology reconciliation |

: Semantics versus pragmatics for a single Census variable. {#tbl-sem-vs-prag}

The semantic information is in the metadata. The pragmatic judgment is scattered across methodology documentation, disconnected from the data it governs, or exists as tacit expertise that experienced statisticians apply but have never formalized.

## What a Pragmatic Is

A pragmatic is a structured unit of expert judgment about fitness for use. It is not an instruction, a rule, a constraint, or a lookup table. It is a factual statement of the kind a senior statistician would make to a colleague before they use a particular data product: the professional assessment that transforms a data retrieval into a statistical consultation. Each pragmatic has five structural components, illustrated in @fig-anatomy using ACS-MOE-002, the coefficient of variation reliability threshold.

![Anatomy of a pragmatic, showing the five structural components using ACS-MOE-002 (coefficient of variation threshold) as an example.](assets/figures/F4_pragmatic_item_anatomy.pdf){#fig-anatomy fig-pos="H" width=80% height=80%}

### Context Text

Context text is the judgment itself, expressed in one to three sentences as factual expert knowledge. For example: "When the coefficient of variation exceeds 40 percent, the American Community Survey estimate is considered unreliable for most analytical purposes. The coefficient of variation is calculated as the ratio of the standard error to the estimate, where the standard error is derived from the margin of error divided by 1.645." This is not an instruction telling the model what to do. It is expert knowledge about what the data means, provided at the moment the model is interpreting a specific result.

### Latitude

![The latitude model: a four-level calibrated uncertainty scale for expert judgment.](assets/figures/F5_latitude_model.pdf){#fig-latitude}

Latitude calibrates how much interpretive freedom the model has when applying a judgment. Some statistical rules carry no flexibility: delivering an estimate from a geography that violates the minimum population threshold is harmful regardless of context. Others involve genuine tradeoffs where the right answer depends on the analytical purpose, and constraining the model to a single answer would make it less useful. Latitude encodes this distinction explicitly, so that hard rules arrive as hard rules and context-dependent guidance arrives as context to reason over rather than a constraint to follow. This connects to the observation in @kahneman2021 that professional experts exhibit significant variance in judgments that are nominally deterministic: latitude structures that variance intentionally rather than leaving it implicit in the judgment text.

### Triggers

Triggers are three to six keywords that activate retrieval when the item is relevant to a query. Triggers are authored to reflect how practitioners describe problems rather than how documents index topics, ensuring that a query about "small county poverty data" activates the reliability threshold item even though the query contains none of the technical vocabulary in the item text.

### Thread Edges

Thread edges connect related items into coherent retrieval bundles. When a user asks about small-area estimates, the system retrieves not just the reliability threshold item but also the margin-of-error interpretation item and the period-estimate caveat, the complete set of judgments a statistician would provide together. Thread structure ensures that pragmatic context arrives as a coherent professional assessment rather than isolated facts.

### Provenance

Provenance traces every judgment to its authoritative documentary source: the specific document, section, and page from which the expert knowledge was derived or against which it was validated. This enables audit of every claim in the system back to Census Bureau publications.

## What Pragmatics Are Not

Pragmatics are deliberately distinct from several related concepts:

They are not *retrieval-augmented generation*. RAG retrieves text passages from a document corpus by finding the nearest neighbors to a query embedding: a search over continuous similarity scores that returns different results depending on the embedding model, index state, and query phrasing. Pragmatics delivers structured expert judgment selected by exact topic match: the same query topic always returns the same items. More importantly, the content differs. RAG surfaces text that is semantically related to the query; pragmatics surfaces judgment that is specifically applicable to it. Related text and applicable judgment are not the same thing, and the gap between them is precisely what Section 2 describes.

They are not *prompt engineering*. Pragmatic content is domain knowledge, not model instructions. The system does not tell the model to "always warn about margins of error"; instead, it provides the expert knowledge that margins of error exceeding the estimate indicate unreliability, and allows the model's reasoning to incorporate that knowledge as it would incorporate any factual context.

They are not *an ontology*. The system does not attempt to represent the full relational structure of Census concepts, variables, geographies, and survey products. Language models already approximate this structure in their training data representations. Pragmatics provide the judgment layer that models cannot derive from relational structure alone.

They are not *constraints or guardrails*. The latitude system explicitly encodes where the model has freedom to exercise judgment. A wide-latitude item is not a rule to follow but context to consider. This reflects the reality that statistical consultation often involves professional judgment calls where multiple positions are defensible.

## Deterministic Delivery

A defining property of the pragmatics retrieval mechanism is determinism. When a query's topic is identified, the system maps it to a thread identifier, follows pre-compiled edges in a SQLite database, and returns the associated context items. This is a lookup, not a search. The same topic always produces the same context set.

This property was verified empirically across two independent replications of the full 39-query test battery plus the original evaluation run. All 39 queries produced identical context retrievals across all three runs, with zero mismatches. The determinism is not a tuned property or a statistical regularity. This result is a structural consequence of replacing similarity search with a compiled lookup.

The practical significance is architectural. RAG and GraphRAG systems incur retrieval overhead at every query: embedding lookups, similarity computations, or graph traversals that can return different results as indices are updated, models are versioned, or parameters change. This retrieval variance compounds with the inherent stochasticity of language model generation, producing variance at two stages of the pipeline. Pragmatics eliminates this compounding by paying the construction cost once, at development time, then serving compiled results from a static database at query time. Each query has zero retrieval variance and negligible retrieval overhead. In domains where the difference between a one-year and five-year estimate determines whether an answer is useful or harmful, this architectural property matters.

