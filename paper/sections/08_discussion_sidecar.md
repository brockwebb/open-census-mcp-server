# Section 8.3: Implications for Federal Statistical Agencies — The Sidecar Pattern

<!-- GAP-014: Discussion narrative covering MCP sidecar architecture advantages -->
<!-- Registry references: COST-001–013, EFF-001–008, S2-010–012, RAG-001–007 -->

## The Delivery Architecture Matters

The empirical results establish that curated expert judgment improves statistical consultation quality. But the mechanism of delivery — how that judgment reaches the reasoning model — has practical implications that may matter as much as the quality differential itself.

The Census MCP Server implements pragmatics as a server-side API resource. When a client model calls `get_methodology_guidance`, the MCP server performs a deterministic graph lookup, bundles the relevant context items, and returns them alongside the Census data response. The client receives expert judgment as structured data in the same response envelope as the statistical estimates. No client-side infrastructure is required: no FAISS index to build and maintain, no embedding model to download and version, no chunk strategy to tune, no vector database to operate.

This is the sidecar pattern applied to expert judgment delivery. The pragmatics pack runs alongside the data API, not inside the client.

## Central Maintenance, Distributed Benefit

The operational advantage of server-side delivery is that domain expertise improves in one place and benefits all clients simultaneously. When a Census methodology specialist identifies a new fitness-for-use concern — a sampling frame change, a geographic boundary revision, a reliability threshold update — the pragmatics pack is updated once in the authoring pipeline and recompiled. Every MCP-connected client receives the updated judgment on the next query without client-side changes, reindexing, or redeployment.

Contrast this with the RAG architecture evaluated in this study. Each RAG client must maintain its own chunked index: source documents must be acquired, chunked according to a chosen strategy, embedded with a specific model, and indexed in a local or hosted vector store. When source documents are updated, each client must re-chunk and re-index. When embedding models improve, each client must re-embed. The operational burden scales linearly with the number of clients. For a federal statistical agency serving thousands of data consumers, this is not a sustainable delivery model for expert methodology guidance.

The pragmatics sidecar inverts this cost structure. The authoring cost is concentrated — one expert curates the pack. The delivery cost is marginal — $0.09 per query at Sonnet pricing, $0.14 at Opus (COST-003, COST-012). For context, the full 39-query evaluation battery cost $4.42 at production Sonnet rates (COST-002). The cost of providing expert statistical judgment to every query is negligible relative to the API compute cost the client is already incurring.

## Multi-Vendor Validation as Architectural Test

The evaluation design provides an unintentional but informative test of the sidecar architecture's vendor independence. Three judge models from three vendors (Anthropic Claude, OpenAI GPT, Google Gemini) all consumed pragmatic context delivered via the same MCP interface and consistently scored pragmatics-assisted responses higher across all five quality dimensions (S2-020–024). The MCP protocol is model-agnostic by design — any client that speaks MCP receives identical expert judgment regardless of the reasoning model behind it.

This vendor independence has strategic implications for federal agencies. Adopting pragmatics does not require commitment to a specific model vendor. As reasoning models improve or change, the pragmatics layer remains stable. As agencies evaluate different LLM providers for security, cost, or capability reasons, the expert judgment infrastructure travels with the data, not with the model. This aligns with the Jobs Doctrine principle that motivated the architecture: structural solutions survive model obsolescence, while prompt engineering and model-specific tuning do not.

## Cost-Effectiveness

The cost analysis reveals that pragmatics is 2.2 times more cost-effective than RAG per unit of quality improvement (COST-005). This ratio measures CQS points gained per marginal dollar spent relative to the control condition: pragmatics achieves 6.28 CQS points per marginal dollar versus RAG's 2.83 (COST-004). The pragmatics condition costs more in absolute terms ($0.113 vs $0.082 per query at Sonnet pricing, COST-001), because the structured context items are longer than top-5 retrieved chunks. But the quality return on that investment is disproportionately higher — a d=0.922 improvement over RAG for a 38% cost increase, versus RAG's d=0.546 improvement over control for a 196% cost increase.

At scale, the marginal cost of expert judgment delivery is dominated by input token pricing. The 36 pragmatic items average 21.8 items delivered per query (EFF-008), consuming approximately 16,100 characters of context (EFF-007). As input token costs continue to decline — a trend that has been consistent across model generations — the absolute cost of pragmatics delivery will decrease while the quality advantage, which is structural rather than cost-dependent, remains.

## The Scaling Pattern

The ACS pack evaluated in this study is one domain-specific bundle in what could become a broader ecosystem. The architecture supports additional packs for the Current Population Survey (CPS), the Survey of Income and Program Participation (SIPP), the decennial census, and other federal statistical products. Each pack would contain domain-specific expert judgment curated by specialists in that survey's methodology.

Critically, some pragmatic knowledge is cross-survey. Geographic hierarchy rules, FIPS code resolution logic, and period estimate interpretation apply across multiple federal surveys. The pack architecture supports shared geographic intelligence modules that multiple survey-specific packs can reference, avoiding redundant curation of common knowledge while maintaining survey-specific precision where methodology diverges.

A community contribution model — where federal statisticians, academic demographers, and experienced data users contribute and review pragmatic items — would address the scalability limitation of single-expert curation identified in the Limitations section. The authoring pipeline (Neo4j → staging → compile → SQLite) already supports this workflow; the missing component is the governance structure for multi-contributor quality assurance.
