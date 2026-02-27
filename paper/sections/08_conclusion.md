# Conclusion

<!-- Registry references: S2-010, S2-032, S3-003, PL-001, COST-003 -->

Federal statistical agencies have invested decades in making their data accessible and interpretable by machines, building the syntax and semantics layers that enable automated access to statistical products. Large language models have absorbed much of this infrastructure, demonstrating that they can translate natural language into domain-appropriate queries and retrieve correct data. The remaining gap is not in access or interpretation but in judgment: the expert assessment of whether retrieved data is fit for a specific purpose.

This paper has introduced pragmatics as a named, defined, and implementable concept for addressing this gap. Drawing on Morris's [-@morris1938] semiotic framework, we define pragmatics as structured expert judgment about fitness for use: the assessment that experienced statisticians provide reflexively but that no existing system delivers computationally.

We have provided empirical evidence that pragmatics works. A knowledge representation study comparing three conditions with identical data access demonstrated that 36 curated expert judgment items produce very large improvements in statistical consultation quality (Cohen's d = 1.440 vs. control, d = 0.922 vs. RAG), with the strongest effects on uncertainty communication (d = 1.353), the dimension most directly tied to fitness-for-use assessment. Pragmatic context achieves 91.2% fidelity to authoritative data sources, is 100% deterministic in its delivery, and costs nine cents per query.

The principle underlying these results extends beyond Census data. Just as curating training data reduces variance in what a model learns, curating expert judgment reduces variance in what a model concludes. The federal statistical community has the expertise. The task is to capture it, structure it, and deliver it at the point where decisions are being made, transforming data retrieval into statistical consultation.
