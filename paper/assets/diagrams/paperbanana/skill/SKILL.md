---
name: paperbanana-diagram
description: >
  Author publication-quality diagram specifications (method.txt files) from paper
  prose and draw.io sketches, following federal data visualization standards and
  Tufte design principles. Use when creating, modifying, or regenerating conceptual
  diagrams, architecture figures, or visual explanations for academic papers or
  presentations. Triggers: 'diagram', 'architecture figure', 'method.txt',
  'PaperBanana', 'draw.io', or requests for visual figures that are NOT statistical
  plots (those use plotnine/census_plot_style.py). The method.txt output can be
  rendered by any image generation tool (PaperBanana, Gemini web UI, ChatGPT, etc.).
  This skill covers: paper prose interpretation → draw.io sketch interpretation →
  method.txt spec authoring → deployment → figure_table_map.yaml registration.
---

# Diagram Specification Skill

## What This Does

Translates paper prose and draw.io sketches into method.txt specs — structured
prompts that any image generation tool can render into publication-quality diagrams.

## The Pipeline

```
Paper prose + draw.io sketch  →  method.txt (the product)  →  any renderer  →  PNG
```

- **Paper prose** is the authoritative source of what the diagram communicates
- **draw.io sketch** provides spatial layout and component hierarchy
- **method.txt** is the build spec and the deliverable of this skill
- **PNG** is disposable output, regenerable from method.txt by any tool

To change a diagram: edit the method.txt, re-render. Never edit the PNG.

## Writing the method.txt

The method.txt is a structured prompt using draw.io's shape vocabulary (rounded
rectangles, cylinders, arrows, containers). This vocabulary is standard and in
every image model's training data.

### Required Sections

```
DIAGRAM: <Title>
ASPECT RATIO: <W:H> and logical pixel dimensions
STYLE: Publication constraints

=== LAYOUT OVERVIEW ===
Spatial arrangement in plain English.

=== [PANEL/SECTION NAME] ===
Per section: nodes (shape, fill hex, border hex, labels, font sizes),
arrows (direction, label, style), internal components, annotations.

=== COLOR PALETTE ===
Exact hex values from xdgov. See references/xdgov_colors.md

=== TYPOGRAPHY ===
Font families and sizes per element type.

=== DO NOT ===
Explicit prohibitions.
```

### Spec Discipline: What Belongs in a method.txt

A method.txt describes WHAT to draw. Every sentence must be falsifiable
against the rendered output — you can point at the PNG and say "this
sentence is satisfied" or "this sentence is violated." If you cannot
do that, the sentence does not belong.

Include:
- Shapes, positions, colors (hex values), dimensions, labels, font sizes
- Spatial relationships (above, inside, left-of, connected-to)
- Explicit constraints and prohibitions

Do not include:
- Motivation or rationale ("this communicates the gap")
- Emotional direction ("should feel empty", "conspicuously absent")
- Metaphors or analogies ("like a river", "think of...")
- Style commentary ("something Jobs would approve of")
- Audience context ("they lived through this era")
- Redundant restatement of constraints in different words

Every extra word is a word the renderer can hallucinate from. Shorter
specs with precise constraints produce better renders than verbose specs
with editorial guidance.

### The Translation Step Is Where Errors Happen

The critical skill is **faithful translation** from paper prose to method.txt.
Every detail in the prose must appear in the spec. Common failures:

- Components described as "inside" a server rendered as "adjacent to"
- Tool names changed (e.g., "Pragmatics MCP Server" → "Expert Judgment Server")
- Data paths simplified or made asymmetric when the paper describes symmetry
- Internal architecture flattened (two tools inside one server → two separate servers)
- Labels invented that don't match the paper's terminology

**Read the paper description carefully. Translate literally. When uncertain, ask.**

### Tufte Design Principles (Mandatory)

- **Maximize data-ink ratio.** Every mark carries information. If removing an
  element loses no meaning, remove it.
- **No chartjunk.** No decorative scales, ornamental borders, background textures,
  gradient fills, drop shadows, 3D effects, or clip art.
- **No redundancy.** If the visual structure communicates the comparison, do not
  add a summary table restating it.
- **Small multiples.** Side-by-side panels with shared structure for comparison.
- **Label directly.** Label components on the diagram. Avoid legends that force
  symbol decoding by cross-reference.
- **Precision is respect.** If a component has two internal tools, show two.
  If a data path passes through an MCP server, show the MCP server. Do not
  simplify for visual convenience.

### Color Palette: xdgov Federal Data Design Standards

Full reference: `references/xdgov_colors.md`
Source: https://xdgov.github.io/data-design-standards/components/colors

**Featured colors:**

| Name | Hex | Semantic role in our diagrams |
|------|-----|------|
| Teal | #0095A8 | Data/science components |
| Navy | #112E51 | Authoritative/system components |
| Dark Blue | #205493 | LLM, knowledge components |
| Orange | #FF7043 | Novel/this-paper's contribution |
| Grey | #78909C | Baseline/existing (e.g., RAG) |
| Dark Grey | #4B636E | Muted text, annotations |

Use exact hex values from xdgov. Do not approximate. Do not substitute from
memory — read the reference file.

### Typography

- All text: serif (Georgia preferred)
- Title: 18px bold
- Panel headers: 14px bold
- Node labels: 10px bold (headers) + 9px (body)
- Arrow labels: 9px muted (#4B636E)
- Annotations: 9px italic muted

## Rendering

The method.txt can be rendered by any image generation tool. Common options:

- **PaperBanana CLI** — multi-agent framework with VLM critic loop
- **Gemini web UI** (Nano Banana) — paste method.txt as prompt
- **Any image model** — the spec is a structured prompt, not tool-specific

When using any renderer: read the project's config files for model names,
API key variable names, and version numbers. **Do not substitute model names
or env var names from training knowledge — they are stale.** Read the config.

## Human Review (Mandatory)

No renderer reliably enforces domain-specific correctness. Verify:

- Architectural accuracy (do boxes/arrows match the actual system?)
- Label correctness (do names match the paper's terminology?)
- Tufte compliance (no chartjunk, no redundancy, direct labeling)
- Color fidelity (xdgov hex values, not approximations)
- Internal vs external placement (inside means inside, not adjacent)

If review fails → edit method.txt → re-render.

## Deployment and Registration

Copy approved output:
```
<renderer output>  →  paper/assets/diagrams/fig_<n>.png
```

Method.txt stays as the companion build spec. Register in `figure_table_map.yaml`:

```yaml
F<N>:
  title: "..."
  figure_type: paperbanana
  generation:
    tool: <renderer used>
    source_file: "paper/assets/diagrams/<n>.drawio"    # if exists
    method_file: "paper/assets/diagrams/paperbanana/<n>_method.txt"
    build_command: "<exact command used to render>"
    provenance: "<run ID or timestamp>"
  output:
    paper: "diagrams/fig_<n>.png"
```

**Required fields:** method_file, build_command, provenance.
**Staleness rule:** method_file mtime > output mtime → regenerate.

## CC Task Files

Completed tasks stay in `paper/cc_tasks/` as artifact history. Never delete them.
