# FCSM 2026 + Publishing — Master Checklist
## Due: ~March 5, 2026 (slide deck to conference)
## Today: February 20, 2026 — 13 days
## Last updated: 2026-02-20

---

## WEEK 1 (Feb 20-25): Foundation & First Publication

### P0 — Blocking everything else

- [ ] **Publish the FCSM×NIST crosswalk** (Zenodo + Medium)
  - Content: ALREADY WRITTEN (`reports/tevv/pure_crosswalk_part1.md` + `part2.md`)
  - Zenodo: combine into single PDF, upload, get DOI (1 hour)
  - Medium: light reformatting for web readability (2 hours)
  - WHY FIRST: establishes priority, gives you a citable reference for slides
  - DEPENDENCY: nothing — this is self-contained

- [ ] **Finalize CQS rubric spec v1.0**
  - File: `docs/verification/cqs_rubric_specification.md`
  - Status: exists, needs D6 framing update
  - D6 update: binary grounding gate (pass/fail by design), included for completeness
  - D1-D5: scored dimensions (0-1-2), the quality measurement
  - Content: three-way crosswalk table, D6 as gate, V2 methodology
  - CC TASK: mechanical update, ~30 min
  - WHY: need this clean for the paper and for handout

### P1 — Slide deck skeleton

- [ ] **Create slide outline** (10-15 min talk = 8-12 slides max)
  - Slide 1: Title + session context
  - Slide 2: Timeline (2006 → 2011 → 2017 → 2020 → 2024 → now) — visual
  - Slide 3: The problem (Excel frowny face + semantic smearing one-liner)
  - Slide 4: Two frameworks, same gap (semiotic triad + Bloom's — diagram)
  - Slide 5: NIST has 12 crosswalks, zero from us (the table, simplified)
  - Slide 6: What pragmatics are (one example, anatomy)
  - Slide 7: How it works (simple flow diagram)
  - Slide 8: The evaluation (FCSM × NIST → CQS → TEVV, one diagram)
  - Slide 9: Results (92% vs 65%, the table)
  - Slide 10: The best practice (capture expert judgment, third layer)
  - Slide 11: References + Zenodo DOI + contact
  - FORMAT: decide tool (Google Slides? PPTX? Keynote?)

---

## WEEK 2 (Feb 26 - Mar 5): Polish & Handout

### P1 — Slide production

- [ ] **Build slides** from outline above
  - Visual-heavy, minimal text per slide
  - Timeline graphic (can be simple)
  - Excel frowny face icon — memorable, do it
  - Flow diagrams: reuse/simplify from existing mermaid
  - Results table: clean, three rows, stark numbers
  - CC TASK for diagram generation if needed

### P1 — Handout (PDF fact sheet)

- [ ] **One-page fact sheet PDF** — the take-away
  - Content: problem, insight, what pragmatics are, one example, how evaluated, key result
  - Include Zenodo DOI for crosswalk
  - Include contact info
  - FORMAT: designed PDF
  - v2 of the fact sheet with TEVV framing added

### P2 — Practice

- [ ] **Dry run the talk** at least once out loud
  - Time it — 10-15 min is tight
  - The script v3 is ~12 min read aloud at conversational pace
  - Identify what to cut if running long (crosswalk detail is first to compress)

---

## PARALLEL TRACK: Publishing (can overlap with slide work)

### Already done or nearly done:
- [x] Crosswalk written (Parts 1 & 2)
- [x] Evaluation results in hand (V2 complete, Stage 3 fidelity complete)
- [x] CQS framework designed and documented
- [x] Talking script v3 drafted with TEVV drop
- [x] Fact sheet v1 drafted
- [x] Adversarial Q&A with 19 prepared rebuttals
- [x] Semantic smearing empirical evidence (two corpora)
- [x] D6 framing resolved: binary grounding gate, included for completeness

### Publication sequence:

| # | What | Where | Status | Effort | When |
|---|------|-------|--------|--------|------|
| 1 | FCSM×NIST Crosswalk | Zenodo (DOI) + Medium | Written, needs formatting | 3 hours | Week 1 |
| 2 | Pragmatics Fact Sheet | PDF handout for FCSM | Drafted, needs design + TEVV | 2 hours | Week 2 |
| 3 | Pragmatics Explainer | Medium | Script v3 is the skeleton | 3 hours | Week 2 or post-FCSM |
| 4 | Full Paper | Zenodo or SSRN | Outline exists | 20+ hours | Post-FCSM |
| 5 | NIST Crosswalk Submission | aiframework@nist.gov | Pure crosswalk + cover letter | 4 hours | Post-FCSM |
| 6 | arxiv Preprint | arxiv cs.AI | Needs endorser + LaTeX | Unknown | When endorser found |

### NOT blocking FCSM (do after):
- [ ] Full paper draft
- [ ] NIST submission
- [ ] arxiv (needs endorser — start asking at FCSM)
- [ ] Additional Medium articles (RAG failure, semantic smearing, etc.)
- [ ] Expert validation interviews (Stage 4)

---

## MATERIALS INVENTORY

### Have (ready or near-ready):
- Talking script v3 (with TEVV drop, crosswalk section, Q&A) ✓
- Crosswalk Parts 1 & 2 (publication quality) ✓
- CQS rubric spec (needs D6 gate framing update) ~
- Paper outline ✓
- Evaluation results: Stage 2 V2 complete ✓
- Pipeline fidelity: Stage 3 complete (91.2% vs 74.6% vs 78.3%) ✓
- Semantic smearing evidence (RoBERTa + MiniLM, two corpora) ✓
- Pragmatics vocabulary doc ✓
- Authoring guide ✓
- 35 ACS pragmatic items in staging ✓
- Adversarial Q&A with 19 prepared rebuttals ✓
- Fact sheet v1 ✓
- Elevator script (short/long versions) ✓
- TEVV methodology document ✓
- Always-ground thesis with pre/post evidence ✓

### Need to create:
- [ ] Slide deck (8-12 slides)
- [ ] PDF handout (1-page fact sheet v2, designed)
- [ ] Zenodo upload of crosswalk (PDF formatting)
- [ ] Medium post of crosswalk (web formatting)

### Nice to have but NOT blocking:
- Mermaid diagrams rendered as images for slides
- Backup slides (deep-dive on any section)
- Printed handouts (depends on FCSM logistics)

---

## DECISION LOG

| Decision | Options | Resolution |
|----------|---------|------------|
| Slide tool | Google Slides / PPTX / Keynote | TBD |
| First publication | arxiv / Zenodo / Medium / SSRN | Zenodo (DOI) + Medium (reach) |
| Handout format | Markdown / PDF / printed | Designed PDF, bring printed copies |
| Crosswalk: submit to NIST now or after? | Before FCSM / After | After — get feedback first |
| Full paper timing | Before FCSM / After | After — slides + handout are enough |
| D6 treatment | Drop / Binary gate / Scored | Binary gate, included for completeness |
| CQS dimensions | D1-D5 only / D1-D6 | D1-D6: five scored + one binary gate |

---

## DAILY TARGETS (suggested)

**Thu Feb 20:** Zenodo upload of crosswalk (get DOI), CQS v1.0 update (CC task) ← TODAY
**Fri Feb 21:** Medium post of crosswalk, slide outline finalized
**Sat-Sun Feb 22-23:** Buffer / catch up
**Mon Feb 24:** Start building slides
**Tue Feb 25:** Slides draft complete
**Wed Feb 26:** Fact sheet PDF v2 designed
**Thu Feb 27:** Dry run talk, time it, adjust
**Fri Feb 28:** Polish slides based on dry run
**Sat-Sun Mar 1-2:** Buffer
**Mon Mar 3:** Final slide polish, print handouts if needed
**Tue Mar 4:** Submit / upload slide deck
**Wed Mar 5:** Travel / prep day if needed
