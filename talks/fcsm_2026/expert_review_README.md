# Expert Review Materials

## Status: SCAFFOLD — Do not deploy until V2 Stage 1 responses are integrated

## Overview
Domain expert validation of three AI systems answering Census data questions.
Blinded rank-order evaluation via Google Form, followed by optional debrief
and elicitation interview.

## Workflow Order (THIS ORDER IS MANDATORY)
1. Expert completes Google Form (cold, blinded) — NO prior discussion of systems
2. Collect and analyze form responses
3. Send debrief one-pager to those who opted in
4. Solicit interview participation during debrief
5. Conduct elicitation interviews (see expert_elicitation_guide.md)
6. Extract and format candidate pragmatics from transcripts
7. Send formatted items to expert for review/approval

## Files in this directory

| File | Status | Purpose |
|------|--------|---------|
| expert_review_README.md | Current | This file |
| expert_review_form.md | TODO | 20 blinded queries, 3 responses each, from V2 Stage 1 |
| expert_review_key.json | TODO | Randomization mapping (A/B/C → condition) |
| expert_review_debrief.md | TODO | One-pager explaining the three conditions and findings |
| expert_elicitation_guide.md | DONE | Interview protocol for tacit knowledge capture |

## Google Form Structure

### Intro Page
"I'm testing three different AI systems designed to answer Census data questions.
For each question below, you'll see the original question and three responses
(A, B, C) in randomized order. Please rank them 1st, 2nd, 3rd based on which
response you'd trust most if someone were making a real-world decision with
this data. If you spot anything wrong or concerning, there's an optional
comment box. Should take about 20 minutes. Thank you for your time."

### Query Pages (20 pages, one per query)
Each page shows:
- The original question (with any persona context)
- Response A (randomized condition)
- Response B (randomized condition)
- Response C (randomized condition)
- Rank: 1st choice [A/B/C], 2nd choice [A/B/C], 3rd choice [A/B/C]
- Optional: "Anything wrong or concerning about these responses?" [free text]

### Closing Page
"Thank you for completing this review. Your expert judgment is invaluable.

A few optional follow-up questions:

1. Overall, how would you rate the quality of these AI responses for Census
   data questions? [1-5 scale: 1=Dangerous, 2=Poor, 3=Acceptable, 4=Good, 5=Excellent]

2. Would you like to receive a debrief explaining what the three systems were
   and how they differed? [Yes/No]

3. If yes, preferred email: [text field]

4. Any other comments about AI-assisted Census data consultation? [free text]"

## Query Selection Criteria (20 of 39)
Target distribution:
- 8 normal queries (breadth coverage)
- 4 small area / reliability edge cases
- 4 geographic edge cases
- 2 temporal comparison
- 2 ambiguity / product mismatch

Prioritize queries where LLM judge scores diverged between conditions,
plus the D3/D4 high-delta cases where pragmatics showed strongest advantage.

## Blinding Requirements
CRITICAL: Responses must be deblinded of condition tells before deployment.

Strip or neutralize:
- RAG tells: "reference materials," "methodology documentation provided,"
  "documents available to me," "based on the provided context"
- Pragmatics tells: "After consulting methodology guidance," "The methodology
  tool indicates," explicit tool call references
- Control tells: generally clean but verify

Behavioral patterns (V2 should be clean but verify):
- V1 had a fatal tell: control/RAG said "visit data.census.gov" while
  pragmatics returned actual data. V2 equalizes tool access so all three
  conditions should return real data. VERIFY THIS before deployment.

After stripping, read Q1, Q10, Q20 end-to-end to confirm no tells remain.
Check for dangling artifacts from find-and-delete ("in ." or "according to ,").

## Regeneration Dependency
The form content CANNOT be generated until the V2 Stage 1 response files
are confirmed clean. Source files:
- results/v2_redo/stage1/control_responses_20260216_055354.jsonl
- results/v2_redo/stage1/rag_responses_20260216_055354.jsonl
- results/v2_redo/stage1/pragmatics_responses_20260216_074817.jsonl

## Analysis Plan
- Kendall's W (concordance) across expert reviewers
- Kendall's W between expert rankings and LLM judge rankings
- Per-query comparison: expert rank vs CQS composite rank
- Qualitative: catalog all "concerning" comments by condition
- If experts and LLM judges agree directionally → validates eval framework
- If they disagree → more interesting, report both

## Participation
- Voluntary, no compensation
- Peer collaboration / expert consultation model
- Attribution preference collected after review, not before
- Interview solicitation happens at debrief stage, not during form
