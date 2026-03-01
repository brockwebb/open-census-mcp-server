# Pragmatics: Structured Expert Judgment

<!-- Registry references: PL-001, PL-004, DET-001–004 -->
<!-- Citation files: core_argument.md, federal_data_evolution_arc.md, d3_uncertainty_deep_dive.md -->

## The Semiotic Foundation

Charles Morris's [-@morris1938] *Foundations of the Theory of Signs* introduced a tripartite framework for understanding how signs function: syntax concerns the formal relationships between signs, semantics concerns the relationship between signs and the objects they denote, and pragmatics concerns the relationship between signs and their interpreters, specifically the contextual conditions under which signs are appropriately used. This framework has been foundational in linguistics, philosophy of language, and information science for nearly nine decades.

Applied to federal statistical data, the three layers map directly to the infrastructure that agencies have built and the gap that remains.

*Syntax* encompasses the structural layer: APIs, machine-readable formats, data transmission protocols, table schemas, and the formal rules governing how data is organized and accessed. This layer is mature. The Census Bureau's API, standardized file formats, and programmatic access points represent decades of investment in making data structurally available to machines.

*Semantics* encompasses the meaning layer: variable descriptions, concept classifications, geographic hierarchies, survey documentation, and the metadata that allows a consumer to understand what a data element represents. This layer is well-developed and continues to improve through AI-ready data initiatives.

*Pragmatics* encompasses the judgment layer: the expert assessment of whether a particular data element is appropriate for a particular use, given the specific context of the question being asked. This layer does not exist as a computationally deliverable resource in any federal statistical system.

The distinction between semantics and pragmatics is critical to understanding why metadata alone is insufficient for statistical consultation.

| | Semantics | Pragmatics |
|---|---|---|
| **Answers** | What is this number? | Is this number fit for my purpose? |
| **Source** | Data dictionaries, API metadata | Methodology handbooks, technical documentation, expert judgment |
| **Example** | B19013_001E = median household income, inflation-adjusted dollars, ACS 5-year | MOE may render this estimate unreliable at pop. 8,000; 5-year = 60-month rolling average; comparing to decennial requires methodology reconciliation |

: Semantics versus pragmatics for a single Census variable. {#tbl-sem-vs-prag}

The semantic information is in the metadata. The pragmatic judgment is scattered across methodology documentation, disconnected from the data it governs, or exists as tacit expertise that experienced statisticians apply but have never formalized.

## What a Pragmatic Is

A pragmatic is a structured unit of expert judgment about fitness for use. It is not an instruction, a rule, a constraint, or a lookup table. It is a factual statement of the kind a senior statistician would make to a colleague before they use a particular data product: the professional assessment that transforms a data retrieval into a statistical consultation. In library science terms, pragmatics serve the role a skilled reference librarian plays: not retrieving information, but advising whether the retrieved information is fit for the patron's purpose.

![Anatomy of a pragmatic, showing the five structural components using ACS-MOE-002 (coefficient of variation threshold) as an example.](assets/figures/F4_pragmatic_item_anatomy.pdf){#fig-anatomy}

Each pragmatic has five components.

### Context Text

Context text is the judgment itself, expressed in one to three sentences as factual expert knowledge. For example: "When the coefficient of variation exceeds 40 percent, the American Community Survey estimate is considered unreliable for most analytical purposes. The coefficient of variation is calculated as the ratio of the standard error to the estimate, where the standard error is derived from the margin of error divided by 1.645." This is not an instruction telling the model what to do. It is expert knowledge about what the data means, provided at the moment the model is interpreting a specific result.

### Latitude

![The latitude model: a four-level calibrated uncertainty scale for expert judgment.](assets/figures/F5_latitude_model.pdf){#fig-latitude}

Latitude encodes the calibrated uncertainty of the judgment itself, on a four-level scale. A pragmatic with latitude *none* represents hard consensus: no reasonable expert disagrees that the one-year American Community Survey requires a population of at least 65,000. A pragmatic with latitude *narrow* represents strong professional agreement with rare exceptions; the 40 percent coefficient of variation threshold is widely accepted but not universally applied. A pragmatic with latitude *wide* acknowledges genuine context-dependence: whether to use one-year or five-year estimates involves a tradeoff between recency and reliability that depends on the specific analytical purpose. A pragmatic with latitude *full* provides background context that informs but does not constrain; the American Community Survey replaced the decennial census long form beginning in 2005.

Latitude is not a metadata annotation. It is a calibrated uncertainty model over expert judgment, encoding not just what practitioners know but how confidently the field holds that knowledge and where reasonable experts disagree. This connects to the observation in @kahneman2021 that professional experts exhibit significant variance in judgments that are nominally deterministic. Latitude structures that variance explicitly rather than leaving it implicit.

### Triggers

Triggers are three to six keywords that activate retrieval when the item is relevant to a query. Triggers are authored to reflect how practitioners describe problems rather than how documents index topics, ensuring that a query about "small county poverty data" activates the reliability threshold item even though the query contains none of the technical vocabulary in the item text.

### Thread Edges

Thread edges connect related items into coherent retrieval bundles. When a user asks about small-area estimates, the system retrieves not just the reliability threshold item but also the margin-of-error interpretation item and the period-estimate caveat, the complete set of judgments a statistician would provide together. Thread structure ensures that pragmatic context arrives as a coherent professional assessment rather than isolated facts.

### Provenance

Provenance traces every judgment to its authoritative documentary source: the specific document, section, and page from which the expert knowledge was derived or against which it was validated. This enables audit of every claim in the system back to Census Bureau publications.

## What Pragmatics Are Not

Pragmatics are deliberately distinct from several related concepts:

They are not *retrieval-augmented generation*. RAG retrieves passages from a document corpus based on embedding similarity. Pragmatics delivers curated expert judgment through deterministic graph traversal. The retrieval mechanism, the content, and the failure modes are fundamentally different.

They are not *prompt engineering*. Pragmatic content is domain knowledge, not model instructions. The system does not tell the model to "always warn about margins of error"; instead, it provides the expert knowledge that margins of error exceeding the estimate indicate unreliability, and allows the model's reasoning to incorporate that knowledge as it would incorporate any factual context.

They are not *an ontology*. The system does not attempt to represent the full relational structure of Census concepts, variables, geographies, and survey products. Language models already approximate this structure in their training data representations. Pragmatics provide the judgment layer that models cannot derive from relational structure alone.

They are not *constraints or guardrails*. The latitude system explicitly encodes where the model has freedom to exercise judgment. A wide-latitude item is not a rule to follow but context to consider. This reflects the reality that statistical consultation often involves professional judgment calls where multiple positions are defensible.

## Deterministic Delivery

A defining property of the pragmatics retrieval mechanism is determinism. When a query's topic is identified, the system maps it to a thread identifier, traverses defined edges in the graph structure, and collects the relevant context nodes. This is a lookup, not a search. The same topic always produces the same context set.

This property was verified empirically across two independent replications of the full 39-query test battery plus the original evaluation run. All 39 queries produced identical context retrievals across all three runs, with zero mismatches. The determinism is not a tuned property or a statistical regularity. It is a structural consequence of replacing similarity search with graph traversal.

The practical significance is that pragmatics eliminates one source of compounding variance in the AI pipeline. Language model generation is inherently stochastic: the same input can produce different outputs. When retrieval is also stochastic, as in RAG and GraphRAG systems, variance compounds at both stages. Pragmatics reduces this tax by making the grounding deterministic while accepting that reasoning remains stochastic. The lighthouse is fixed. The ship still navigates, but toward a stable signal.

