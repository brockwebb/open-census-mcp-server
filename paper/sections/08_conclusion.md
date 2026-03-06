# Conclusion

<!-- Registry references: S2-010, S2-032, S3-003, PL-001, COST-003 -->

Large language models (LLMs) arrive well-informed about federal statistics, but familiarity with data is not the same as fitness-for-use judgment. They cannot reliably evaluate margins of error, interpret period estimates, or recognize when an estimate is too unreliable to report. Much of this judgment is scattered across documentation or embedded in professional practice, never consolidated where an AI system can reliably reach it.

This paper has introduced pragmatics as a named, defined, and implementable concept for addressing this gap. Drawing on Morris's [-@morris1938] semiotic framework, we define pragmatics as structured expert judgment about fitness for use: the assessment that experienced statisticians provide reflexively but that no existing system delivers computationally.

We have provided empirical evidence that pragmatics works. A knowledge representation study comparing three conditions with identical data access demonstrated that 36 curated expert judgment items produce very large improvements in statistical consultation quality (Cohen's d = 1.440 vs. control, d = 0.922 vs. RAG), with the strongest effects on uncertainty communication (d = 1.353), the dimension most directly tied to fitness-for-use assessment. Pragmatic context achieves 91.2% fidelity to authoritative data sources and delivers methodology context through deterministic lookup on every query, at a cost more per query than RAG but with 2.2 times more quality improvement per dollar spent.

The architecture is domain-agnostic; the content is domain-specific. Just as curating training data reduces variance in what a model learns, curating expert judgment reduces variance in what a model concludes. The federal statistical community has the expertise. The task is to capture it, structure it, and deliver it at the point where decisions are being made, transforming data retrieval into statistical consultation.

## Use of AI in This Work {.unnumbered}

This article was developed with the assistance of large language models (Anthropic Claude, Google Gemini, OpenAI ChatGPT) for brainstorming, drafting, and iterating prose. All analytical conclusions reflect the author's professional assessment. All AI-generated content was reviewed and validated by the author.
