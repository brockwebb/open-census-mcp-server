# Appendices

## Appendix A: Complete Test Battery

The full 39-query test battery with category labels and edge case classifications is available in the project repository at `src/eval/battery/queries.yaml`.

[TODO: Include or reference the full query list]

---

## Appendix B: Consultation Quality Score (CQS) Rubric

The CQS rubric specifies five quality dimensions (D1–D5), each scored 0–2. Full specification is available at `docs/verification/cqs_rubric_specification.md`. Grounding compliance is reported as a Stage 3 pipeline verification metric alongside fidelity and auditability.

| Dimension | Name | Scoring |
|-----------|------|---------|
| D1 | Accuracy of Statistical Claims | 0 / 1 / 2 |
| D2 | Completeness of Relevant Information | 0 / 1 / 2 |
| D3 | Appropriate Uncertainty Communication | 0 / 1 / 2 |
| D4 | Clarity of Explanation | 0 / 1 / 2 |
| D5 | Avoidance of Harmful Misinterpretation | 0 / 1 / 2 |

**Stage 3 verification metrics (pipeline behavior, not CQS dimensions):**
- Fidelity: 91.2% (pragmatics), 74.6% (RAG), 78.3% (control)
- Auditability: 72.8% (pragmatics), 8.1% (control)
- Grounding compliance: 100% — all 39 pragmatics queries consulted methodology guidance before data interpretation

[TODO: Include full rubric text or reference]

---

## Appendix C: System Prompts

System prompts used for each experimental condition are available in `src/eval/agent_loop.py`. The base system prompt was shared across all conditions. The pragmatics condition received an additional prompt segment activating the methodology guidance tool.

[TODO: Include or excerpt the prompts]

---

## Appendix D: Design Correction Post-Mortem

The V1 evaluation design contained a confound: the pragmatics condition had access to a methodology guidance tool that the control and RAG conditions lacked, making tool access — not knowledge representation — the independent variable. This was identified and corrected in V2, where all conditions received identical data tools and differed only in methodology support form. Full documentation is in `docs/decisions/ADR-011-v2-evaluation-design-correction.md`.

---

## Appendix E: Pragmatic Item Catalog

The 36 pragmatic items in the ACS pack, with context text, latitude, triggers, thread edges, and provenance, are available in `staging/acs/*.json` (18 category files).

[TODO: Include summary table or full catalog]
