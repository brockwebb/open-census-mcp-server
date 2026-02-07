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

## Theory References

| ID | Title | Source URL | Local Path | Status |
|----|-------|------------|------------|--------|
| THEORY-001 | Semiotic DQ Foundations | See semiotic_dq_foundations.md | `theory/semiotic_dq_foundations.md` | 🟢 |

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
