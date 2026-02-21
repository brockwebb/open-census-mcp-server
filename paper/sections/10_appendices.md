# Appendices

## Appendix A: Complete Test Battery

The full 39-query test battery with category labels and edge case classifications is available in the project repository at `src/eval/battery/queries.yaml`.

[TODO: Include or reference the full query list]

---

## Appendix B: Consultation Quality Score (CQS) Rubric

The CQS rubric specifies five scored dimensions (D1–D5) and one binary grounding gate (D6). Full specification is available at `docs/verification/cqs_rubric_specification.md`.

| Dimension | Name | Scoring |
|-----------|------|---------|
| D1 | Accuracy of Statistical Claims | 0 / 1 / 2 |
| D2 | Completeness of Relevant Information | 0 / 1 / 2 |
| D3 | Appropriate Uncertainty Communication | 0 / 1 / 2 |
| D4 | Clarity of Explanation | 0 / 1 / 2 |
| D5 | Avoidance of Harmful Misinterpretation | 0 / 1 / 2 |
| D6 | Grounding Gate (binary) | pass / fail |

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
