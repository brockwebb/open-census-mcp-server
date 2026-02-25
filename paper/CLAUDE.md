# Pragmatics Paper — Project Guide

## What This Is

Research paper: "Pragmatics as Point-of-Decision Expert Judgment for Federal Statistical Data"
Target venues: FCSM 2026 Research Conference (talk), Zenodo/arxiv (preprint)

## Build System

**Source files (edit these):**
- `frontmatter.yml` — YAML/PDF config (Palatino, 11pt, letter, 1in margins, xelatex)
- `abstract.md` — abstract text (~250 words, TODO)
- `sections/01_introduction.md` through `sections/10_appendices.md` — body sections
- `citations/` — citation context files (markdown, for author reference)

**Build artifact (never edit directly):**
- `draft_v1.qmd` — assembled by `build.py`

**Build command:**
```bash
cd paper && python build.py           # assemble .qmd only
cd paper && python build.py --render  # assemble + quarto render to PDF
cd paper && python build.py --open    # assemble + render + open PDF
```

**Assembly order** (defined in `build.py`):
1. `sections/01_introduction.md`
2. `sections/02_semantic_smearing.md`
3. `sections/03_pragmatics.md`
4. `sections/04_method.md`
5. `sections/05_results.md`
6. `sections/06_discussion.md`
7. `sections/07_limitations_future.md`
8. `sections/08_conclusion.md`
9. `sections/09_references.md`
10. `sections/10_appendices.md`

**Sidecar files (NOT assembled, working notes only):**
- `sections/05_extraction_pipeline.md` — merged into 04_method.md
- `sections/08_discussion_sidecar.md` — merged into 06_discussion.md
- `sections/00_abstract.md` — superseded by `abstract.md` at project root

## Formatting Decisions (Locked)

| Setting | Value | Rationale |
|---------|-------|-----------|
| Body font | Palatino | Matches published crosswalk; renders well |
| Mono font | Source Code Pro | Standard |
| Font size | 11pt | Standard article |
| Margins | 1in | Standard |
| Engine | xelatex | Required for system fonts |
| Line stretch | 1.25 | Readability |
| Number sections | yes | Academic standard |
| TOC | no | Article, not report |

## Writing Conventions (Mandatory)

These rules are inherited from `central_library/crosswalks/fcsm_nist/WRITING_CONVENTIONS.md` and apply to all section files.

### Zero tolerance
- **No em dashes.** Replace with commas, semicolons, colons, parenthetical rewrites, or sentence restructuring.
- **No bold in running prose.** Bold is for headings, table headers, figure captions only. If emphasis is needed, use italics sparingly or rewrite the sentence to be stronger.
- **No bullet points in prose sections.** Write in paragraphs. Lists are for appendices, tables, and enumerated reference content only.
- **No "novel."** Say what makes it different instead.
- **"Confabulation" not "hallucination."** Consistent with NIST AI 600-1.

### Style
- Lead with the point (exception: building a case for resistant audiences).
- Italics for emphasis on key contrast words, sparingly.
- No bold pseudo-headers in prose (e.g., `**The problem.**` followed by text). Use a real `###` subheading or write a strong topic sentence.
- Specificity is kindness. Name the chapter, section, number.
- "Fitness for use" is FCSM's core concern. Name it explicitly.
- Vendor diversity ≠ statistical independence. Say what is actually shared and different.

## Citation Infrastructure

**Current state:** References are inline markdown at the end of each section that uses them, plus a collected list in `sections/09_references.md`. No `.bib` file yet.

**Target state:** BibTeX (`references.bib`) + APA CSL (`apa.csl`). Can reuse `apa.csl` from the crosswalk project at `central_library/crosswalks/fcsm_nist/apa.csl`.

**Crosswalk citation to add:**
```bibtex
@techreport{webb2026crosswalk,
  author = {Webb, Brock},
  title  = {When {AI} Enters Federal Statistics: A Crosswalk Between Data Quality and {AI} Trustworthiness Frameworks},
  year   = {2026},
  month  = feb,
  doi    = {10.5281/zenodo.18766095},
  url    = {https://doi.org/10.5281/zenodo.18766095}
}
```

This should be cited in:
- Section 4.5 (Method) — for TEVV framework grounding
- Section 6.4 (Implications) — for the crosswalk as coordination tool
- Section 9 (References) — bibliography entry

## Key Numbers (from `numbers_registry.md`)

Do not invent or round numbers. All statistics come from `paper/numbers_registry.md` or the evaluation pipeline outputs in `results/`. Key figures:
- Pragmatics vs Control: d = 1.440
- Pragmatics vs RAG: d = 0.922
- D3 (uncertainty): d = 1.353 vs control, d = 1.040 vs RAG
- Fidelity: 91.2% (pragmatics), 74.6% (RAG), 78.3% (control)
- Pragmatic items: 36 (34 pipeline + 2 manual)
- RAG chunks: 311
- Source pages: 354
- Determinism: 100% (39/39, 2 replications, 0 mismatches)
- Cost: $0.09/query marginal (Sonnet), $0.14 (Opus)

## Repo-Level Context

See `../CLAUDE.md` for full project context (evaluation pipeline, vocabulary, architecture, conventions). This file covers paper-specific concerns only.

## Known Issues

1. `abstract.md` is TODO — write last, after body finalized
2. Em dashes throughout section files — need systematic purge
3. Section 3.1 uses bullet-point list for syntax/semantics/pragmatics — restructure to prose
4. Section 3.2 uses bold pseudo-headers — restructure to real subheadings or prose
5. Sidecar files in sections/ should be moved to `arc/` or deleted after confirming content is merged
6. `draft_v1.md` (non-qmd) is stale — may be an earlier concatenation; verify if still needed
