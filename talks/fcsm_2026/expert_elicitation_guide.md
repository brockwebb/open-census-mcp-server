# Expert Elicitation Interview Guide
# Census Methodology — Tacit Knowledge Capture

**Purpose:** Surface expert statistical judgment that isn't in methodology handbooks
but is routinely shared informally between experienced practitioners and data users.

**Target:** Senior Census/survey methodologists (ACS, CPS, or cross-survey)

**Format:** Google Meet, recorded with permission, 30-45 minutes

**Output:** Candidate pragmatic items with expert provenance for review and approval

---

## Pre-Interview Checklist

- [ ] Confirm recording permission (verbal on-call + written via email)
- [ ] Confirm attribution preference: named, anonymous, or decide after review
- [ ] Google Form (blinded validation) completed BEFORE this interview
- [ ] Have 2-3 example pragmatic items ready to show if they ask "what do you mean?"
- [ ] Notepad ready for real-time flags (don't rely solely on transcript)

---

## Opening (2 minutes)

"Thanks for doing this. I'm building a system that helps AI tools give better
answers about Census data. The AI already knows how to pull the numbers — what
it's missing is the expert judgment about when those numbers are trustworthy
and when they're not. I want to capture the things you'd tell a colleague before
they use the data — the stuff that's in your head but not always in the handbook."

"I'll ask about 10 questions. There are no wrong answers. The most valuable
things are the warnings, caveats, and 'watch out for this' advice you've given
people over the years."

---

## Core Questions

### Block 1: Failure Modes (10-15 minutes)

These surface the highest-value pragmatics — the mistakes experts have seen
repeatedly and know how to prevent.

**Q1: The Recurring Mistake**
"What's the single most common mistake you've seen people make with [ACS/CPS]
data? The one that makes you wince every time?"

*If they go shallow ("people don't check margins of error"), push:*
"Can you give me a specific example where that led to a bad conclusion?"

**Q2: The Dangerous Misconception**
"Is there something people confidently believe about the data that's just wrong?
Something where their intuition leads them astray?"

*Push:* "Where does that misconception come from? Is there something in how
the data is presented that encourages it?"

**Q3: The Comparison Trap**
"When people compare estimates — across geographies, across years, across
surveys — where do they go wrong most often?"

*Push:* "Is there a specific comparison you've seen in a report or news article
that made you cringe?"

**Q4: The Small Area Problem**
"What do you wish every user knew before they pulled tract-level or small-area
data?"

*Push:* "At what point do you tell someone 'this estimate isn't usable'? How
do you make that judgment call?"

### Block 2: Hidden Knowledge (10-15 minutes)

These surface knowledge that exists in institutional memory but isn't well-documented.

**Q5: The Undocumented Rule**
"Is there anything about the data that you know from experience but that's hard
to find in official documentation? Something you'd only learn from working with
it for years?"

*Push:* "If a new analyst joined your team tomorrow, what's the first thing
you'd warn them about that isn't in any training manual?"

**Q6: The Methodology Change**
"Has there been a methodology change — in collection, processing, weighting,
or definitions — that people still don't account for when they do time series?"

*Push:* "How far back does that affect comparisons? Is there a clean break
year or is it gradual?"

**Q7: The Cross-Survey Confusion**
"When people mix up [ACS and CPS / ACS and Decennial / CPS and BLS data],
what specifically goes wrong? What are they conflating?"

*Push:* "If someone asked you 'what's the unemployment rate in [small county]'
and used ACS data, what would you tell them?"

### Block 3: Fitness-for-Use Judgment (10-15 minutes)

These surface the decision criteria experts use but rarely articulate.

**Q8: The Trust Threshold**
"How do you personally decide whether an estimate is reliable enough to use?
What's your mental checklist?"

*Push:* "Is that a CV threshold? A population floor? A gut feeling? Walk me
through your actual thought process."

**Q9: The Redirect**
"When someone asks for data that technically exists but you know isn't fit for
their purpose, how do you handle that? What do you point them to instead?"

*Push:* "Can you give me an example where the 'right' answer was 'don't use
this data for that question'?"

**Q10: The One Thing**
"If you could attach one sentence of advice to every ACS/CPS data download —
something every user would see before they use the numbers — what would it say?"

---

## Closing (2-3 minutes)

"This is incredibly helpful. Here's what happens next: I'll pull the key
insights from our conversation and write them up as structured items — each
one a specific piece of expert guidance with a citation back to you. I'll
send those to you to review before anything gets used. You can correct,
reword, or veto anything."

"Would you also be comfortable with me citing you by name in the research,
or would you prefer to be anonymous? Either way is fine — you can decide
after you see the write-ups."

---

## Post-Interview Processing

1. Download Google Meet transcript
2. Send transcript to expert for review/correction/redaction (within 48 hours)
3. Extract candidate pragmatic items from transcript
4. Format each as a ContextItem:
   - context_text: 1-3 sentences, expert's insight in structured form
   - latitude: assessed based on how absolute the guidance is
   - provenance: `{"sources": [{"document": "Expert interview", "subject": "[Name or Anonymous ID]", "date": "2026-XX-XX", "extraction_method": "interview"}], "confidence": "expert_judgment"}`
   - triggers: 3-6 retrieval hooks
5. Send formatted items back to expert for approval
6. Expert approves, corrects, or vetoes each item
7. Approved items enter staging with full provenance chain

## Attribution Options

| Level | Citation | Provenance |
|-------|----------|------------|
| Named | "J. Smith, personal communication, Feb 2026" | `"subject": "John Smith, Principal Architect ACS"` |
| Role only | "Senior ACS methodologist, personal communication" | `"subject": "Senior ACS methodologist, 30+ years"` |
| Anonymous | "Census domain expert" | `"subject": "Expert-001"` |
| Acknowledged | Name in acknowledgments, anonymous in citations | Mix of above |

Expert chooses after reviewing the formatted items, not before.

---

## Interviewer Notes

- Let them talk. The best pragmatics come from stories, not direct answers.
- When they say "well, it depends..." — that's latitude. Push for what it depends ON.
- When they say "everybody knows that..." — it's probably undocumented. Push for the source.
- When they get animated or frustrated — you've hit a real pain point. Stay there.
- Record exact phrases. "The MOE will eat your signal alive" is better than a sanitized rewrite.
- Flag anything they say that contradicts existing pragmatics — that's either a correction or a latitude difference.
- If they mention a specific incident, report, or policy decision — that's provenance gold. Get the details.
