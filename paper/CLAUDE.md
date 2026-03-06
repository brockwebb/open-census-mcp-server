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

## Figure and Table Assets

**Style module:** `central_library/style/census_plot_style.py`, symlinked to:
- `paper/assets/census_plot_style.py` (paper figures)
- `talks/fcsm_2026/census_plot_style.py` (slide figures)

Uses plotnine (Python ggplot2) with U.S. Census Bureau xdgov Data Design Standards palette. All figure scripts import from this module. Do not define colors, fonts, or themes inline.

**Asset registry:** `paper/assets/figure_table_map.yaml` — single source of truth for all figures and tables. Contains:
- Figure/table metadata (title, description, section, type)
- Generation commands (source script, data files, build command)
- Output paths and dimensions
- Numbers registry cross-references
- Slide mapping (empty until deck is built)
- Variant tracking (paper PDF vs slide PNG)

When adding or modifying figures/tables, update `figure_table_map.yaml` first.

### Diagrams Are Built From Source

All diagrams are built artifacts. The source spec is the editable file; the image is disposable output.

| Tool | Source (edit this) | Output (disposable) |
|------|-------------------|---------------------|
| D2 | `*.d2` | `*.pdf` |
| PaperBanana | `*_method.txt` | `*.png` |
| draw.io | `*.drawio` | `*.png` (exported) |

To modify a diagram, edit the source file and regenerate. Never edit the output image directly.

Every entry in `figure_table_map.yaml` must include:
- `source_file` or `source_script` — the editable source
- `method_file` — the build spec (required for PaperBanana; the D2 file itself serves this role for D2 diagrams)
- `build_command` — the exact command to reproduce the output
- `provenance` — run ID or timestamp linking output to a specific generation

If the source file's modification timestamp is newer than the output file, the output is stale and must be regenerated. A mismatch between source and output is a deviation.

PaperBanana `*_method.txt` files are saved as companions alongside their outputs in `paper/assets/diagrams/paperbanana/`. These are the reproducible specs — the PNGs are regenerable from them.

**Figure generation:**
- Plotnine figures (F2a, F2b, F7, F8, F9): `python paper/assets/generate_figures.py --all`
- D2 diagrams (F3, F4, F5, F6): `bash paper/assets/diagrams/build_diagrams.sh`
- Tables (T1–T6): `python paper/assets/generate_tables.py --apply`

## Writing Conventions (Mandatory)

Two convention files govern this paper. Both must be read before any prose editing.

**General conventions** (apply to all Brock projects):
`/Users/brock/Documents/GitHub/central_library/crosswalks/fcsm_nist/WRITING_CONVENTIONS.md`

**Paper-specific conventions** (override or supplement general conventions for this paper):
`/Users/brock/Documents/GitHub/census-mcp-server/paper/WRITING_CONVENTIONS_PAPER.md`

Paper-specific rules take precedence over general rules when they conflict.

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

## Key Numbers

Do not invent or round numbers. Do not duplicate numbers in this file — they will drift.

**Source of truth chain:** V&V scripts → `results/` JSON → `paper/numbers_registry.md` (registry IDs) → section prose (cites registry IDs in comments).

This file is never authoritative for any statistic. Consult `numbers_registry.md` by registry ID.

## CC Task Protocol

**Never edit a CC task file that has already been handed off.** If a correction is needed after handoff, create a new task file with today's date and a descriptive suffix (e.g., `2026-03-05_rebuild_deterministic_diagram_v2.md`). Editing a running or completed task corrupts the audit trail and may interfere with an in-flight execution.

Default is always a new CC task. Only modify an existing task file if explicitly asked to.

Every CC task that involves figures must include an explicit line: **"DO NOT rebuild any figure not listed in this task."** CC has a documented tendency to rebuild all figures when given any figure-related task. This must be prevented by explicit scope restriction in every task file.

## Prose Editing Process

See `editing_tools/prose_editing_workflow.md` for the AI-assisted editing workflow. Short version: AI flags sentences in chat with proposed rewrites, human approves/rejects, CC applies approved edits as exact string replacements. No direct file edits without explicit approval.

Supporting tools in `editing_tools/`:
- `readability_scores.py` — Flesch-Kincaid grade per section
- `editing_tools_srs.md` — tool documentation and current FK baseline

## Repo-Level Context

See `../CLAUDE.md` for full project context (evaluation pipeline, vocabulary, architecture, conventions). This file covers paper-specific concerns only.

## Known Issues

1. `abstract.md` is TODO — write last, after body finalized
2. Em dashes throughout section files — need systematic purge
3. Section 3.1 uses bullet-point list for syntax/semantics/pragmatics — restructure to prose
4. Section 3.2 uses bold pseudo-headers — restructure to real subheadings or prose
5. Sidecar files in sections/ should be moved to `arc/` or deleted after confirming content is merged
6. `draft_v1.md` (non-qmd) is stale — may be an earlier concatenation; verify if still needed
7. ~~F1 (Semiotic Framework) not yet created~~ — DONE (v1.1, PaperBanana)
8. D2 source files still named F3_*, F4_*, etc. on disk despite v1.1 renumbering to F4-F7. yaml documents the mismatch. Cosmetic debt, no functional impact.
