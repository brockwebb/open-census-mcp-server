# Reference Document Catalog

> **Principle:** No vaporware. Every document we cite must exist locally.

## Status Legend
- 🟢 Downloaded & verified
- 🟡 URL identified, not downloaded
- 🔴 Needed, not yet sourced

---

## ACS Documentation

### Core Handbooks

| ID | Title | Version | Source URL | Local Path | Status |
|----|-------|---------|------------|------------|--------|
| ACS-GEN-001 | Understanding and Using ACS Data: What All Data Users Need to Know | 2020 | [census.gov](https://www.census.gov/content/dam/Census/library/publications/2020/acs/acs_general_handbook_2020.pdf) | `acs/acs_general_handbook_2020.pdf` | 🟢 |
| ACS-RES-001 | Understanding and Using ACS Data: What Researchers Need to Know | 2020 | [census.gov](https://www.census.gov/content/dam/Census/library/publications/2020/acs/acs_researchers_handbook_2020.pdf) | `acs/acs_researchers_handbook_2020.pdf` | 🟡 |
| ACS-PUMS-001 | Understanding and Using ACS PUMS Files | 2020 | [census.gov](https://www.census.gov/content/dam/Census/library/publications/2020/acs/acs_pums_handbook_2020.pdf) | `acs/acs_pums_handbook_2020.pdf` | 🟡 |

### Technical Documentation

| ID | Title | Source URL | Local Path | Status |
|----|-------|------------|------------|--------|
| ACS-TECH-001 | ACS Technical Documentation Portal | [census.gov](https://www.census.gov/programs-surveys/acs/technical-documentation.html) | N/A (web portal) | 🟡 |
| ACS-METH-001 | ACS Research & Methodology | [census.gov](https://www.census.gov/programs-surveys/acs/methodology.html) | N/A (web portal) | 🟡 |
| ACS-SF-001 | ACS Summary File Handbook | [nhgis](https://assets.nhgis.org/original-data/acs/acs_summary-file_handbook_2019.pdf) | `acs/acs_summary_file_handbook_2019.pdf` | 🟡 |

### Subject & Code Documentation

| ID | Title | Source URL | Status |
|----|-------|------------|--------|
| ACS-SUBJ-001 | Subject Definitions | [census.gov](https://www.census.gov/programs-surveys/acs/technical-documentation/code-lists.html) | 🟡 |
| ACS-CODE-001 | Code Lists | [census.gov](https://www.census.gov/programs-surveys/acs/technical-documentation/code-lists.html) | 🟡 |

---

## CPS Documentation

| ID | Title | Source URL | Local Path | Status |
|----|-------|------------|------------|--------|
| CPS-TECH-001 | CPS Technical Documentation | [census.gov](https://www.census.gov/programs-surveys/cps/technical-documentation.html) | N/A (web portal) | 🟡 |
| BLS-HOM-001 | BLS Handbook of Methods Ch. 1 | [bls.gov](https://www.bls.gov/opub/hom/cps/) | `cps/bls_hom_cps.pdf` | 🟡 |

---

## Federal AI-Ready Data Policy

| ID | Title | Source URL | Local Path | Status |
|----|-------|------------|------------|--------|
| FED-AI-001 | FCSM 25-03: AI-Ready Federal Statistical Data (May 2025) | [statspolicy.gov](https://statspolicy.gov/assets/fcsm/files/docs/FCSM.25.03_AI-Ready-Extension-Data-Quality.pdf) | N/A (cited, not downloaded) | 🟡 |
| FED-AI-002 | Dept. of Commerce: Generative AI and Open Data (Jan 2025) | [commerce.gov](https://www.commerce.gov/sites/default/files/2025-01/GenerativeAI-Open-Data.pdf) | N/A (cited, not downloaded) | 🟡 |

**Context:** These documents represent the federal policy landscape this project responds to. FCSM 25-03 extends traditional data quality for ML use cases. The Commerce report focuses on making open data GenAI-ready. Both anchor the talk's argument that current guidance addresses syntax and semantics but misses pragmatics.

---

## Theory References

| ID | Title | Source URL | Local Path | Status |
|----|-------|------------|------------|--------|
| THEORY-001 | Semiotic DQ Foundations | See semiotic_dq_foundations.md | `theory/semiotic_dq_foundations.md` | 🟢 |
| THEORY-002 | A Theory of Usable Information Under Computational Constraints (Xu et al., ICLR 2020) | [arXiv:2002.10689](https://arxiv.org/abs/2002.10689) | N/A (cited, not downloaded) | 🟡 |

**THEORY-002 relevance:** Formal basis for pragmatics layer. V-information shows bounded observers (LLMs) gain usable information from preprocessing (packs), extraction is inherently asymmetric/lossy, and misspecified representations still outperform MI-based approaches. Supports ADR-004 always-ground pattern, pragmatics-over-ontology architecture, and lossy-but-sufficient extraction philosophy.

---

## Download Instructions

Priority downloads (curl or manual):
```bash
# ACS General Handbook (PRIMARY SOURCE)
curl -o docs/references/acs/acs_general_handbook_2020.pdf \
  "https://www.census.gov/content/dam/Census/library/publications/2020/acs/acs_general_handbook_2020.pdf"

# ACS Researchers Handbook
curl -o docs/references/acs/acs_researchers_handbook_2020.pdf \
  "https://www.census.gov/content/dam/Census/library/publications/2020/acs/acs_researchers_handbook_2020.pdf"

# ACS Summary File Handbook
curl -o docs/references/acs/acs_summary_file_handbook_2019.pdf \
  "https://assets.nhgis.org/original-data/acs/acs_summary-file_handbook_2019.pdf"
```

After download, update status to 🟢 and add SHA256 hash.

---

## Extraction Priority

For pragmatics layer, extract from these docs in order:

1. **ACS-GEN-001** - Population thresholds, MOE guidance, comparison rules, period estimates
2. **ACS-RES-001** - Researcher-specific caveats, PUMS considerations
3. **BLS-HOM-001** - CPS methodology for cross-survey pragmatics
