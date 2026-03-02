# FCSM 2026 + Publishing — Master Checklist
## Due: ~March 5, 2026 (slide deck to conference)
## Today: February 25, 2026 — 8 days
## Last updated: 2026-02-25

---

## STATUS UPDATE (2026-02-25)

**Crosswalk side quest: COMPLETE.** Published as companion article with standalone subcategory-level appendix. DOI: 10.5281/zenodo.18766095. This was the P0 blocker; it is cleared.

**Critical path change:** Paper is the primary deliverable, not slides. The talk is 15 minutes with ~5 slides. The real distribution is QR codes linking to:
1. Published preprint (Zenodo or arxiv)
2. One-page fact sheet (distilled from paper)
3. Published crosswalk (already has DOI)

The paper draft exists in full (8 sections + appendices, ~7,700 words body). Remaining work is formatting compliance, abstract, citation infrastructure, and rendering.

---

## WEEK 1 RETROSPECTIVE (Feb 20-25)

### Completed
- [x] **Publish FCSM x NIST crosswalk** — DOI: 10.5281/zenodo.18766095
- [x] **Two paper edits landed** — Section 5.2 (document-forward/failure-forward), Section 6.1 (selectivity across AI stack)
- [x] **Font decision: Palatino** — matches crosswalk, locked
- [x] **Paper handoff written** — `handoffs/2026-02-25_pragmatics_paper_formatting.md`
- [x] **CC task drafted** — paper/CLAUDE.md creation + writing conventions compliance

### Not completed (deprioritized, not failed)
- [ ] ~~Slides draft~~ — deferred; paper is critical path
- [ ] ~~Medium post of crosswalk~~ — deferred to post-FCSM

---

## P0 — Paper to Preprint (CRITICAL PATH)

### Paper formatting (CC tasks, mechanical)
- [ ] **Create `paper/CLAUDE.md`** — paper-specific project guide for future threads
- [ ] **Em dash purge** — zero tolerance per WRITING_CONVENTIONS.md, all 10 section files
- [ ] **Section 3 restructure** — eliminate bullet list (3.1) and bold pseudo-headers (3.2)
- [ ] **Add crosswalk citation** — Sections 4.5, 6.4, 9 (DOI: 10.5281/zenodo.18766095)
- [ ] **Rebuild draft_v1.qmd** — run build.py after all section edits

### Paper content (requires author judgment)
- [ ] **Write abstract** (~250 words) — `paper/abstract.md` is currently TODO
- [ ] **Create references.bib** — convert inline references to BibTeX, add crosswalk entry
- [ ] **Copy apa.csl** from crosswalk project to paper directory
- [ ] **Review figure/table placeholders** — confirm all `[INSERT FIGURE/TABLE]` markers have specs
- [ ] **Final read-through** — verify flow after all mechanical edits
- [ ] **Quarto render test** — build PDF, check formatting, fix any LaTeX issues

### Publication
- [ ] **Upload to Zenodo** — get DOI for preprint
- [ ] **Generate QR codes** — preprint URL, crosswalk DOI, fact sheet URL

---

## P1 — Talk Materials (supports paper launch)

### Slides (minimal, ~5 slides)
- [ ] **Slide 1:** Title + affiliation + QR code to preprint
- [ ] **Slide 2:** The problem (syntax/semantics solved, pragmatics missing)
- [ ] **Slide 3:** What pragmatics are (one example, anatomy diagram)
- [ ] **Slide 4:** Results table (3 conditions, key numbers, d values)
- [ ] **Slide 5:** Implications + QR codes (preprint, crosswalk, fact sheet)
- FORMAT: Google Slides or Keynote (TBD, doesn't matter for 5 slides)

### Fact sheet (1-page PDF, distilled from paper)
- [ ] **Draft fact sheet v2** — problem, insight, method, key result, QR codes
- [ ] **Design and render** — clean PDF layout
- [ ] **Print copies** if FCSM logistics support handouts

### Dry run
- [ ] **Practice talk once** — 15 minutes is tight, time it

---

## P2 — Post-FCSM (not blocking)

- [ ] Medium post: crosswalk article (web-readable version)
- [ ] Medium post: pragmatics explainer (talk script v3 as skeleton)
- [ ] arxiv submission (needs endorser; start asking at FCSM)
- [ ] NIST crosswalk submission (aiframework@nist.gov)
- [ ] Expert validation interviews (Stage 4)
- [ ] Additional Medium articles (RAG failure, semantic smearing, etc.)

---

## DAILY TARGETS (revised)

**Tue Feb 25 (today):**
- CC task file finalized and handed to Claude Code
- Master checklist updated (this file)

**Wed Feb 26:**
- CC task execution: CLAUDE.md + em dash purge + Section 3 restructure + crosswalk citation + rebuild
- Start abstract draft

**Thu Feb 27:**
- Abstract finalized
- Create references.bib from inline references
- Copy apa.csl, test Quarto render

**Fri Feb 28:**
- Fix any Quarto rendering issues
- Final read-through of assembled paper
- Start fact sheet v2

**Sat-Sun Mar 1-2:**
- Fact sheet designed and rendered
- Upload preprint to Zenodo, get DOI
- Generate QR codes

**Mon Mar 3:**
- Build 5 slides with QR codes
- Dry run talk

**Tue Mar 4:**
- Polish slides, print fact sheets if applicable
- Submit/upload slide deck

**Wed Mar 5:**
- Buffer / travel day

---

## MATERIALS INVENTORY

### Have (ready or near-ready):
- [x] Full paper draft (8 sections + appendices, ~7,700 words body)
- [x] Evaluation results: Stage 2 V2 certified
- [x] Pipeline fidelity: Stage 3 complete (91.2% vs 74.6% vs 78.3%)
- [x] Crosswalk published (DOI: 10.5281/zenodo.18766095)
- [x] Quarto frontmatter configured (Palatino, 11pt, letter)
- [x] build.py working (sections → .qmd assembly)
- [x] Talking script v3
- [x] Adversarial Q&A with 19 prepared rebuttals
- [x] Semantic smearing empirical evidence
- [x] Numbers registry (all statistics sourced)
- [x] CQS rubric specification
- [x] Fact sheet v1

### Need to create:
- [ ] paper/CLAUDE.md
- [ ] Abstract (~250 words)
- [ ] references.bib (BibTeX)
- [ ] Clean PDF render (Quarto)
- [ ] Fact sheet v2 (with TEVV framing + QR codes)
- [ ] 5 slides
- [ ] QR codes (preprint, crosswalk, fact sheet)
- [ ] Zenodo preprint upload

---

## DECISION LOG

| Decision | Options | Resolution |
|----------|---------|------------|
| Critical path | Slides-first / Paper-first | **Paper-first** — paper IS the deliverable, slides are wayfinding |
| Font | Source Sans Pro / Palatino | **Palatino** — matches crosswalk, renders well |
| Slide count | 8-12 / 5 | **5 slides** — 15 min talk, QR codes do the heavy lifting |
| Slide tool | Google Slides / PPTX / Keynote | TBD (doesn't matter for 5 slides) |
| First publication | arxiv / Zenodo / SSRN | Zenodo (DOI) for preprint; arxiv if endorser found at FCSM |
| Handout format | Markdown / PDF / printed | Designed PDF fact sheet, print if logistics allow |
| Em dashes | Keep some / Zero tolerance | **Zero tolerance** per WRITING_CONVENTIONS.md |
| Section 3 bullets | Keep / Restructure to prose | **Restructure** — paragraphs, not lists |
| Section 3 bold pseudo-headers | Keep / Convert to ### / Rewrite | **Convert to ### subheadings** |
| Crosswalk citation | Inline only / BibTeX | Add inline now; convert to BibTeX with rest of refs |
| D6 treatment | Drop / Binary gate / Scored | Binary gate, included for completeness |

---

## DEPENDENCY GRAPH

```
CC Task (CLAUDE.md + compliance) ──► Rebuild .qmd ──► Abstract ──► references.bib ──► Quarto render
                                                                                          │
                                                                                          ▼
                                                                                    Zenodo upload
                                                                                          │
                                                                                          ▼
                                                                              QR codes ──► Slides
                                                                                  │
                                                                                  ▼
                                                                             Fact sheet
```
