# COOS / Census MCP — Future Exploration & Enhancement Parking Lot

**Purpose**: Centralized registry of deferred ideas, research leads, and architectural enhancements. Items here are *not* committed work — they're options with documented rationale, to be evaluated against actual need when the time comes.

**Gate rule**: Nothing leaves this parking lot without (1) a validated need from test bench results or user feedback, and (2) a complexity budget that justifies the ROI.

---

## 🏗️ Architecture Enhancements

### AE-1: Ontology-Grounded Tool Discovery
**Source**: [Grounded Agents: Annotating Ontologies with Tool Definitions](https://medium.com/@aiwithakashgoyal/grounded-agents-annotating-ontologies-with-tool-definitions-b0950ba0217d)  
**Idea**: Store MCP tool capabilities as nodes in Neo4j linked to COOS concepts via `AFFORDS_OPERATION` relationships. Agent dynamically discovers valid operations per concept rather than relying on prompt engineering.  
**Current gap**: COOS concepts and MCP tools are connected implicitly through prompt design, not formally in the graph.  
**Pattern**: Define ontology (TTL) → materialize in Neo4j → attach tool metadata → agent queries graph for valid operations.  
**Complexity**: Medium. Requires schema extension + tool registration workflow.  
**When to evaluate**: When adding new MCP tools beyond the current three, or when prompt-based tool routing starts failing edge cases.

### AE-2: Decision Traces for Fitness Judgments
**Source**: [Agentic Context Graphs](https://medium.com/@aiwithakashgoyal/the-trillion-dollar-context-graph-turning-organizational-memory-into-your-greatest-asset-abd489241755)  
**Idea**: When the pragmatics layer fires a fitness-for-use judgment (e.g., "ACS 1-year unavailable for pop < 65K"), store the reasoning chain as a structured Decision Trace node in Neo4j — which guidance was consulted, what threshold triggered, what the recommendation was.  
**Value**: Auditable trail for statistical consultation quality. Training data for future evaluation. Pattern discovery across judgments.  
**Schema sketch**:
```
(:FitnessJudgment {
  query_context, 
  guidance_consulted[], 
  threshold_triggered, 
  recommendation, 
  timestamp
})-[:APPLIED_TO]->(:Variable)
 -[:REFERENCED]->(:MethodologyGuidance)
```
**Complexity**: Low-medium. Mostly logging infrastructure.  
**When to evaluate**: During test bench development — this is the natural instrumentation layer.

### AE-3: Hybrid Search Scoring Formula
**Source**: [Agentic Context Graphs, §5.1](https://medium.com/@aiwithakashgoyal/the-trillion-dollar-context-graph-turning-organizational-memory-into-your-greatest-asset-abd489241755)  
**Idea**: Weighted hybrid scoring: `0.6 * vector_similarity + 0.2 * entity_match + 0.1 * policy_match + 0.1 * recency`. Applicable to coarse-fine search weighting.  
**Current state**: Coarse-fine search exists but weighting is ad hoc.  
**Complexity**: Low. Parameterize existing search, grid-search over weights.  
**When to evaluate**: During search quality tuning phase.

### AE-4: Truth Maintenance Loop for Methodology Updates
**Source**: [Self-Evolving Neuro-Symbolic KG](https://medium.com/@aiwithakashgoyal/how-to-build-a-neuro-symbolic-medical-knowledge-graph-that-learns-reasons-and-self-corrects-f6d66e7e915a)  
**Idea**: When Census methodology changes (new population thresholds, revised MOE calculations), propagate updates systematically through the graph rather than manual editing. Detect contradiction → resolve → update KG → update affected pragmatics.  
**Complexity**: Medium-high. Requires change detection and propagation logic.  
**When to evaluate**: When onboarding second survey (CPS) or when ACS methodology changes force manual rework.

---

## 🔍 Search & Retrieval Enhancements

### SR-1: Multi-Representation Embeddings
**Source**: Internal (ACS Variable Search Refactor Plan)  
**Idea**: Embed variables multiple ways — description, use cases, synthetic queries — for richer semantic matching.  
**Complexity**: Medium. Multiple embedding passes + fusion logic.

### SR-2: Cross-Encoder Reranker
**Source**: Internal  
**Idea**: Train on (query, variable) pairs for +5-8% precision improvement.  
**Complexity**: Medium. Requires training data collection.

### SR-3: Query Expansion via LLM
**Source**: Internal  
**Idea**: Use LLM to generate query variations before search, improving recall.  
**Complexity**: Low-medium. Latency tradeoff.

### SR-4: Fine-Tune BGE on Census Domain
**Source**: Internal  
**Idea**: Domain-specific fine-tuning on census (query, variable) pairs.  
**Complexity**: High. Requires curated training set.  
**Gate**: Only after test bench proves generic embeddings are the bottleneck.

---

## 🤖 Agent Architecture Enhancements

### AG-1: Multi-Agent Ensemble (Deferred)
**Source**: [Agentic Context Graphs, §Multi-Agent Collaboration](https://medium.com/@aiwithakashgoyal/the-trillion-dollar-context-graph-turning-organizational-memory-into-your-greatest-asset-abd489241755)  
**Idea**: Specialized agents for compliance, methodology, geography, etc. with coordinated decision-making.  
**Current stance**: Single agent with methodology guidance is correct for now. The Jobs Doctrine applies — don't build orchestration complexity prematurely.  
**When to evaluate**: When test bench reveals systematic failures that a single agent can't address, or when cross-survey support (CPS + ACS) demands domain specialization.

### AG-2: ACE-Style Learning Loop
**Source**: [Agentic Context Graphs, §ACE Framework](https://medium.com/@aiwithakashgoyal/the-trillion-dollar-context-graph-turning-organizational-memory-into-your-greatest-asset-abd489241755)  
**Idea**: Record decision outcomes → analyze patterns → update playbooks. Generator → Reflector → Curator cycle.  
**Dependency**: Requires AE-2 (Decision Traces) as prerequisite instrumentation.  
**Complexity**: High. Full feedback loop with evaluation infrastructure.  
**When to evaluate**: After production deployment with real user queries generating outcome data.

### AG-3: GNN-Based Concept Discovery
**Source**: [Self-Evolving Neuro-Symbolic KG, §Neural Discovery Track](https://medium.com/@aiwithakashgoyal/how-to-build-a-neuro-symbolic-medical-knowledge-graph-that-learns-reasons-and-self-corrects-f6d66e7e915a)  
**Idea**: Graph Neural Networks over knowledge graph to discover latent patterns and predict missing relationships.  
**Current stance**: Not at the scale where this makes sense. COOS has ~330 concepts and ~37K variables — GNNs shine at 100K+ nodes with complex topology.  
**When to evaluate**: Post-multi-survey expansion when graph complexity warrants it.

---

## 📐 Knowledge Engineering Enhancements

### KE-1: Formal TTL-First Ontology Workflow
**Source**: [Grounded Agents](https://medium.com/@aiwithakashgoyal/grounded-agents-annotating-ontologies-with-tool-definitions-b0950ba0217d)  
**Idea**: Strict workflow: define ontology in TTL (RDF/OWL) → materialize in Neo4j → attach tool/pragmatics metadata. Currently we go concept JSON → TTL → Neo4j, which works but isn't formally grounded in RDF semantics.  
**Value**: Interoperability with semantic web standards, FAIR data principles, potential integration with other federal ontologies.  
**Complexity**: Medium. Requires RDF/OWL expertise and tooling (n10s plugin).  
**When to evaluate**: When interoperability with other federal knowledge systems becomes a requirement.

### KE-2: Negative Knowledge as Structured Guidance
**Source**: Internal (LLM Ontology Review)  
**Idea**: 56 rejected concepts transformed into active "don't go here" guidance. Already partially implemented.  
**Status**: Concept validated, implementation in progress.

### KE-3: Probabilistic Concept Assignment
**Source**: Internal (Spatial Topology Discovery)  
**Idea**: Data-driven concept assignment using embeddings rather than manual curation. Eliminates "uncategorized" problem.  
**Status**: Pipeline exists, needs integration with production system.

---

## 📊 Cross-Survey & Expansion

### CS-1: Cross-Survey Geographic Intelligence Sharing
**Source**: Internal (REQ-FUTURE-001)  
**Idea**: Share geographic resolution logic across federal surveys (CPS, SIPP, ACS) while maintaining survey-specific knowledge bases.  
**Gate**: Validation over premature abstraction. Test with CPS first.

### CS-2: BLS/CPS Domain Expansion
**Source**: Internal (Communications Strategy)  
**Idea**: Extend pragmatics and semantic intelligence to Current Population Survey and Bureau of Labor Statistics data.  
**Dependency**: Core ACS system must be validated first.

---

## 📝 Evaluation & Testing

### ET-1: Persona-Based Test Batteries
**Source**: Internal  
**Idea**: Test across user sophistication levels. Weight 80% toward edge cases.  
**Status**: Planned for test bench development.

### ET-2: Multi-Model Adversarial Evaluation
**Source**: Internal  
**Idea**: Test bench protocol across Claude, OpenAI, Gemini to validate model-agnostic value of pragmatics layer.  
**Status**: Evaluation prompt template exists. Needs systematic execution.

---

## 📚 References

| ID | Source | URL |
|----|--------|-----|
| REF-1 | Grounded Agents: Annotating Ontologies with Tool Definitions | [Medium](https://medium.com/@aiwithakashgoyal/grounded-agents-annotating-ontologies-with-tool-definitions-b0950ba0217d) |
| REF-2 | Agentic Context Graphs: Turning Organizational Memory Into Your Greatest Asset | [Medium](https://medium.com/@aiwithakashgoyal/the-trillion-dollar-context-graph-turning-organizational-memory-into-your-greatest-asset-abd489241755) |
| REF-3 | Self-Evolving Neuro-Symbolic Medical Knowledge Graph | [Medium](https://medium.com/@aiwithakashgoyal/how-to-build-a-neuro-symbolic-medical-knowledge-graph-that-learns-reasons-and-self-corrects-f6d66e7e915a) |
| REF-4 | Foundation Capital: AI's Trillion Dollar Opportunity — Context Graphs | [Foundation Capital](https://foundationcapital.com/context-graphs-ais-trillion-dollar-opportunity/) |

---

*Last updated: 2026-02-09*  
*Gate rule reminder: Validate need before graduating any item from this lot.*
