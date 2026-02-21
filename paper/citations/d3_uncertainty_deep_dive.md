# D3 (Uncertainty Communication) — Deep Dive

## Key Finding
Largest effect across all five CQS dimensions: d=1.353 vs control, d=1.040 vs RAG (S2-032).

## Why Pragmatics Dominate D3

### 1. Codified Expert Reliability Thresholds
Pragmatics encode specific numeric boundaries models can't learn from documentation alone:
- CV > 40% = unreliable for most purposes
- Enables classification: "highly reliable," "cautionary," "unreliable" based on actual retrieved MOE

### 2. Statistical Interpretation Formulas
Procedural knowledge delivered at query time:
- SE = MOE / 1.645
- Confidence interval overlap rules for comparing estimates
- SE propagation for ratios and multi-geography aggregations

### 3. Informed Refusal > Confident Delivery of Unfit Data
Core D3 scoring principle. Pragmatics tell the model when NOT to provide a number:
- Small area: Loving County TX (pop ~64) → data suppressed/unreliable → redirect to alternatives
- Threshold awareness: 1-year ACS requires 65K+ population → prevents delivering misleading/nonexistent data

### 4. Information vs Judgment (RAG vs Pragmatics distinction)
- RAG "remembers" that MOEs exist (retrieves a chunk explaining what an MOE is)
- Pragmatics "evaluate" — "This specific MOE makes this specific estimate unreliable for this specific use case"

### 5. Calibrated Latitude
- `none` latitude on population thresholds = hard constraint
- `wide` latitude on reliability tradeoffs = practitioners legitimately disagree, nuanced response allowed

## Connection to NORC / Broader Framing
[TODO: Add NORC paper reference and connection]

## Paper Placement
Results section (Table or call-out box for D3 as exemplar dimension) and/or Discussion section 8.1 (why selectivity beats volume — D3 is the clearest demonstration).
