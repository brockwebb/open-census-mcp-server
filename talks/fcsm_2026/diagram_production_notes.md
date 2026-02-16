# Diagram & Presentation Production Notes

**Date:** 2026-02-16
**Status:** Planning

## Diagram Toolchain Decision

Mermaid diagrams in `talks/fcsm_2026/*.mermaid.md` are **working drafts** for the notebook and GitHub documentation. They are NOT the final presentation format.

### Final presentation stack (from prior discussion):
- **ggplot2** (in `{r}` Quarto chunks) → statistical figures (data-driven)
- **D2 or Graphviz** (via `{bash}` or Quarto extensions) → architecture/conceptual diagrams
- **Quarto** compiles everything → PDF/HTML output

### Why not Mermaid for final output:
- MCP renderer shows literal `\n` in multi-line node labels (cosmetic but ugly)
- Limited typographic and layout control
- D2/Graphviz give full control over spacing, fonts, colors
- Everything compiles from command line, no IDE switching
- All code, all reproducible

### Migration path:
1. Keep Mermaid drafts as-is for documentation
2. When building final slides, translate each diagram to D2 or Graphviz
3. Embed in `.qmd` file as `{bash}` chunks
4. Quarto compiles alongside R/Python content

### Current Mermaid drafts to migrate:
- `evaluation_pipeline_overview.mermaid.md` — 5 diagrams (pipeline overview + 4 stage details)
- `v2_stage1_data_flow.mermaid.md` — detailed data flow (notebook-level, may not need slide version)
- `ov0_sidecar_architecture.mermaid.md` — future ConOps sidecar diagram

## No Figma. No IDE switching. Everything is code.
