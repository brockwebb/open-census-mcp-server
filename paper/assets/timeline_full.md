# Full Timeline: 60 Years of Teaching Machines to Read Our Labels

## Purpose
Long-form reference timeline for speaker notes, handout, and fact sheet.
Slide version uses ~9 markers; this captures the complete arc.

## The Arc
"Sixty years of teaching machines to read our labels. Zero years of teaching them our judgment."

---

## Pre-History: Before There Was Light

| Year | Event | Layer | Notes |
|------|-------|-------|-------|
| 1950s | Early ML concepts (Turing, Samuel) | — | Theoretical foundations |
| 1966-68 | MARC I/II (Library of Congress) | Syntax | First systematic machine-readable metadata. Librarians were doing "structure/label/describe for machine consumption" 60 years ago. |
| 1971 | Project Gutenberg | Syntax | Earliest digital text corpus |

## The Census Digital Era (slide starts here)

| Year | Event | Layer | Notes |
|------|-------|-------|-------|
| 1986 | TIGER files | Syntax | Census Bureau's first digital geographic boundary files. The origin point for machine-readable federal spatial data. Audience at Census lived this. |
| 1994 | Dublin Core metadata initiative | Syntax | Cross-domain metadata standardization |
| 1995 | Census Bureau first website | Syntax | Data access goes online |
| 1998 | FGDC metadata standards | Syntax | Geospatial metadata formalized |

## The XML/Standards Decade

| Year | Event | Layer | Notes |
|------|-------|-------|-------|
| 2000 | SDMX development begins | Syntax | Statistical Data and Metadata Exchange — specifically for statistical agencies |
| 2001 | XML-based exchange standards proliferate | Syntax | The precursor work to Schema.org. Important: it took 10 years to formalize. |
| 2009 | data.gov launches | Syntax | Under Obama. 250,000+ datasets in every format imaginable. The mandate without the judgment. A glorified dumping ground of 1000x different file formats. |

## The Formalization Wave

| Year | Event | Layer | Notes |
|------|-------|-------|-------|
| 2011 | Schema.org launches | Syntax/Semantics | Google, Bing, Yahoo, Yandex joint effort. Formalized what XML community had been doing for a decade. |
| 2011 | Federal open data mandate begins | Syntax | Push toward machine-readable federal data. Executive Order 13642 formally issued 2013. |
| 2011 | IBM Watson wins Jeopardy | Semantics | Public demonstration of ML on structured knowledge |

## The AI Inflection

| Year | Event | Layer | Notes |
|------|-------|-------|-------|
| 2014 | GANs (Goodfellow et al.) | — | Generative adversarial networks. Opened generative AI but hit mode collapse bottleneck. |
| 2015 | Diffusion models theorized (Sohl-Dickstein et al.) | — | Theoretical foundation. Would take 5 years to become practical. |
| 2017 | "Attention Is All You Need" (Vaswani et al.) | Semantics | Transformer architecture. LLMs begin absorbing syntactic and semantic layers that metadata catalogs were designed to provide. The metadata infrastructure we spent decades building becomes partially redundant — models learned it from training corpus. |
| 2018 | Evidence Act / OPEN Data Act | Syntax | Foundations for Evidence-Based Policymaking Act. OPEN Data Act baked in. Federal mandate to make data open and machine-readable. Still solving the 2011 problem. |

## The Generative Era

| Year | Event | Layer | Notes |
|------|-------|-------|-------|
| 2020 | DDPM (Ho et al.) | — | Denoising Diffusion Probabilistic Models. Made diffusion practical. Competitive with GANs for image generation. |
| 2021 | Diffusion beats GANs (Dhariwal & Nichol) | — | Established diffusion as new state-of-the-art for image synthesis. |
| 2022 | Latent Diffusion / Stable Diffusion | — | Rombach et al. Diffusion in latent space — efficiency breakthrough enabling consumer-grade image generation. |
| 2022 (Nov) | ChatGPT launches | Semantics | GPT-3.5. First usable generative AI at scale. The moment "everyone" understood what LLMs could do. |
| 2023 (Mar) | GPT-4 | Semantics | Frontier model capability jump |

## The Tool/Protocol Era

| Year | Event | Layer | Notes |
|------|-------|-------|-------|
| 2024 (Nov) | MCP protocol (Anthropic) | Semantics/Tooling | Model Context Protocol. Gives models structured tool access. |
| 2025 (Feb) | Mercury dLLM (Inception Labs) | Paradigm | First commercial diffusion-based LLM. ~1000 tokens/sec on H100s. 10-14x faster than autoregressive frontier models. Diffusion applied to language, not just images. |
| 2026 (Feb) | WebMCP, IndexNow, AI-ready web standards | New front end | Bing, Brave adoption Feb 10 2026. The new front door for AI discovery. |
| 2025-26 | FCSM AI-ready data initiatives | Middle | Federal committees extending quality frameworks for ML. Still solving the 2011 problem better, not the 2025 problem. |
| 2026 (Feb) | Mercury 2 (Inception Labs) | Paradigm | ~1000 tok/sec vs Claude 4.5 Haiku at ~89 tok/sec, GPT-5 Mini at ~71 tok/sec. First reasoning dLLM. Diffusion is no longer a curiosity — it's a production architecture. |

## The Missing Layer

| Year | Event | Layer | Notes |
|------|-------|-------|-------|
| 2026 | **Pragmatics** | **Judgment** | Nobody's doing this yet. The capstone. Expert judgment delivered at the point of statistical reasoning. Not discovery (front end), not structure (middle) — fitness-for-use assessment. d=1.440 over baseline. 36 curated items outperform 311 RAG chunks. |

---

## Three-Lane Framing (for slide visualization)

1. **The Middle (40 years, ongoing):** Structure/label/describe. TIGER → XML → Schema.org → Evidence Act. We're still doing this. Need to do it faster and more efficiently.

2. **The New Front End (2024-26):** MCP → WebMCP → AI-ready standards. The leapfrog for discovery and retrieval. Ensures authoritative content reaches models. But diminishing returns without judgment.

3. **The Missing Back End (2026):** Pragmatics. The capstone nobody's building. Transforms data lookup into statistical consultation. Without this, faster retrieval just means faster wrong answers.

---

## Speaker Note Punchlines

- "Before 1986 there was darkness." (plays well at Census — they lived the TIGER era)
- "It took a decade to formalize what the XML community was already doing. Now we're watching the same pattern with MCP. But pragmatics? Nobody's even started the clock."
- "data.gov: the mandate without the judgment. 250,000 datasets in every format imaginable."
- "They're solving the 2011 problem better, not the 2025 problem."
- "Sixty years of teaching machines to read our labels. Zero years of teaching them our judgment."
- "Mercury 2 is generating at 1000 tokens/sec. The architecture for HOW to generate text is still in flux. And nobody's addressing WHAT judgment to attach to it."
- "The future isn't more trillions of parameters. It's the paring down — removing the junk. Highly curated official information is gold for models."

---

## Slide Version (~9 markers)

| Year | Marker |
|------|--------|
| 1986 | TIGER — Census goes digital |
| 2001 | XML exchange standards |
| 2011 | Schema.org + open data mandate |
| 2017 | Transformers |
| 2018 | Evidence Act |
| 2022 | ChatGPT |
| 2024 | MCP |
| 2025 | Diffusion LLMs |
| 2026 | WebMCP |
| 2026 | **? — the missing layer** |

---

## Status: REFERENCE MATERIAL
For speaker notes, handout, and fact sheet development.
Slide visualization to be designed separately.
