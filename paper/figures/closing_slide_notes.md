# Closing Slide: Best Practices for AI-Ready Federal Data

## Slide Title
"Best Practices for AI-Ready Federal Data"

## Three Bullets

### 1. Keep experimenting.
Things are moving fast. We need to stay engaged, test new approaches, and not be afraid to try things. There is no settled playbook yet.

### 2. Refactor for AI discovery, and keep strengthening what we do well.

**Front end (syntax/discovery):** Adopt the emerging web standards so AI systems can discover and consume our data natively, not just scrape it. WebMCP (Google, February 2026) and llms.txt are the two current standards for declaring tool-use capabilities and content maps to AI agents. This has implications for human users too — how people access data is changing.

**Data and metadata (semantics):** Keep doing what we're already good at: structured APIs, quality metadata, machine-readable formats. But use AI tools to help us do it faster and at scale — produce more, improve upon what we have, in a timely manner. AI can help us be better at the things we already do.

### 3. Start capturing expert judgment.
It's not about the numbers. It's the fitness-for-use judgment — when those numbers should and shouldn't be used, what the caveats are, what a senior statistician would tell you before you touch the data. That expertise lives in people's heads, and it walks out the door when they retire. Pragmatics is one approach to making it machine-deliverable. The data doesn't speak for itself. It never did.

## Full Slide Title Lineup

1. **Title slide** — (talk title + Seuss fork-in-the-road image)
2. **"The Map"** — Table of contents (Seussian rhyming)
3. **"A Brief History of Time"** — Timeline slide (fig_timeline_evolution.png)
4. **"MCP Catastrophe: RAG Fail to No Avail"** — Semantic smearing + RAG failure
5. **"All You Need Is Judgment"** — Semiotic triad (fig_semiotic_stack.png)
6. **"The Bake-Off"** — Experimental design (F6)
7. **"Go Go Pragmatics Rangers"** — Results (F8 forest plot)
8. **"The Golden Ticket: Pragmatics at Scale"** — Scaling the approach
9. **"Oh, the Places You'll Go!"** — Best practices closing (3 bullets)
10. **"I speak for the data, for the data have no tongues."** — Closing image (Lorax robot)

**Backup slides:**
- CQS Rubric (D1-D5) — backup_cqs_rubric.png
- Crosswalk Table 8 — backup_crosswalk_table8_wide.png
- Pragmatic anatomy — fig_pragmatic_anatomy_slide.png

---

## Opening Image Prompt (for OpenAI / NanoBanana)

> A whimsical, Seuss-inspired square illustration of a fork in a winding road. A small friendly robot stands at the fork, looking up at two paths. The left path is labeled "More Data" and leads into a foggy, cluttered landscape of towering stacks of documents and tangled wires disappearing into grey mist. The right path is labeled "Better Judgment" and leads upward toward a bright, clear sunrise over rolling hills with a few clean signposts along the way. The style is warm, hand-drawn, with soft watercolor-like flat fills, wobbly ink outlines, and a mid-century children's book illustration feel. Census color palette: navy blue (#112E51), warm orange (#FF7043), soft grey (#B0BEC5), light blue sky. The robot is small — the journey is bigger than the traveler. White or very light background. Square format. No other text besides the two path labels.

---

## Opening Slide: Table of Contents (Seussian)

**A Brief History of Time**
*where we built the data, line by line*

**The Great RAG Adventure**
*and other glorious failures of mine*

**Pragmatics: The Missing Layer**
*teaching machines to be a wiser data player*

**Oh, the Places You'll Go!**
*best practices for the road we don't yet know*

---

## Slide Bullets (what goes ON the slide)

1. **Keep experimenting.** The playbook isn't written yet.

2. **Refactor for AI discovery.** Adopt WebMCP, llms.txt. Use AI to scale the metadata and structured data work we already do well.

3. **Capture expert judgment.** It's not the numbers. It's the fitness-for-use knowledge that walks out the door when people retire.

---

## Closing Image
"I speak for the data, for the data have no tongues."
— Robot/Lorax illustration (fig_data_lorax.png)

## PaperBanana render command
```bash
cd /Users/brock/Documents/GitHub/census-mcp-server/paper/assets/diagrams/paperbanana && \
paperbanana generate \
  --input data_lorax_slide_method.txt \
  --caption "A friendly data robot standing on a pile of spreadsheets, speaking for the data" \
  --vlm-model gemini-3.1-pro-preview \
  --image-model gemini-3.1-flash-image-preview \
  --iterations 3
```

Deploy output to:
- `talks/fcsm_2026/assets/fig_data_lorax.png`
- `paper/figures/fig_data_lorax.png`

## Semantic smearing render command
```bash
cd /Users/brock/Documents/GitHub/census-mcp-server/paper/assets/diagrams/paperbanana && \
paperbanana generate \
  --input semantic_smearing_slide_method.txt \
  --caption "Semantic smearing: how LLM enrichment destroys retrieval discrimination in federal statistical data" \
  --vlm-model gemini-3.1-pro-preview \
  --image-model gemini-3.1-flash-image-preview \
  --iterations 3
```

Deploy output to:
- `talks/fcsm_2026/assets/fig_semantic_smearing_slide.png`
- `paper/figures/fig_semantic_smearing_slide.png`

## PDF to PNG conversions needed
```bash
brew install poppler  # if not installed
cd /Users/brock/Documents/GitHub/census-mcp-server/paper/assets/figures
pdftoppm -png -r 300 -singlefile F6_experimental_design.pdf ../../talks/fcsm_2026/assets/F6_experimental_design
pdftoppm -png -r 300 -singlefile F8_effect_sizes_forest.pdf ../../talks/fcsm_2026/assets/F8_effect_sizes_forest
# Also copy to paper/figures
pdftoppm -png -r 300 -singlefile F6_experimental_design.pdf ../../paper/figures/F6_experimental_design
pdftoppm -png -r 300 -singlefile F8_effect_sizes_forest.pdf ../../paper/figures/F8_effect_sizes_forest
```
