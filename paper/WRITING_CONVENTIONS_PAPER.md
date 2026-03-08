# Writing Conventions

Rules learned through editing the FCSM × NIST crosswalk article. Apply to all academic/research documents.

## Terminology

- **"Confabulation" not "hallucination."** Consistent with NIST AI 600-1 usage. Hallucination implies perception; confabulation implies construction of false knowledge presented as real.
- **"Risk management" not "governance"** when referring to NIST AI RMF. It is a risk management framework, not a governance framework. "Governance" is a broader umbrella; using it overstates NIST's scope.
- **"Fitness for use"** is FCSM's core concern. Name it explicitly, especially in sections where it matters (e.g., FCSM-only dimensions). Do not assume the reader infers it.
- **"Novel" is banned.** Everything is novel to someone. Say what makes it different instead.
- **No em dashes.** Zero tolerance. Use commas, semicolons, colons, or restructure.
- **"Shared vocabulary" is wrong framing** when both communities have vocabulary. The problem is the absence of a shared reference for how their vocabularies relate — a translation layer, not a missing lexicon.
- **"Typology"** = a classification system of types. Correct term for the five mapping types. Standard in social science and governance literature.

## Formatting

- **Bold: headings, labels, and almost nothing else.** In academic writing, bold is reserved for document structure (headings, subheadings, table/figure captions) and occasionally key terms on first introduction. It does not belong in running prose. If a sentence needs emphasis, rewrite it to be stronger; if a section needs structure, use an actual heading. Bolded prose sentences read as slide deck, not journal article. The test: *Is there a structural reason (heading, label)? Could clearer wording do the job instead?* If the answer to the second question is yes, do not bold.
- **No bold pseudo-headers in prose.** Patterns like `**The problem.**` followed by prose are informal shorthand. If the content warrants sub-structure, use a proper `###` subheading. If it does not warrant a subheading, write a strong topic sentence and let it stand without formatting.
- **Italic run-in heads for labeled-list prose.** Limitations, future work, and enumerated conditions use italic leads followed by a period and the prose sentence: `*Single domain.* The evaluation was conducted...` This is APA Level 4 convention adapted to markdown. Use when items are parallel, scan-worthy, and don't warrant full subheadings.
- **Italics for emphasis:** Standard academic convention. Use on the key contrast word or phrase, not the entire sentence. Sparingly.
- **No bullet points in prose sections.** Write in paragraphs. Lists are for structured reference content (tables, appendices, enumerated items).

## Structure

- **Lead with the point.** The value proposition or key finding opens the section. Supporting evidence follows. Do not bury the lead.
- **Exception to lead-with-the-point:** When the conclusion is more credible as a discovery than an assertion — i.e., persuading a resistant audience. In those cases, build the case first, then land the conclusion.
- **Specificity is kindness.** Vague claims waste the reader's effort. Name the chapter, the section, the implementation, the number. If you can be more specific, be more specific.

## Claims and Framing

- **Don't attribute errors to tools when you made the error.** If the research process produced a wrong result that you caught and corrected, say so. "We made this error, caught it, and corrected it" is more credible than "the AI system made this error."
- **Distinguish threat models from demonstrated attacks.** Plausible risk scenarios grounded in established literature should be framed as "could enable" not "can enable," with a note that these are threat-model scenarios, not demonstrated attacks through your system.
- **Scope verification claims precisely.** Graph verification checks structural coherence, not semantic correctness. Multi-vendor agreement provides evidence against correlated bias, not proof of independence. Name what the evidence actually shows.
- **Vendor diversity ≠ statistical independence.** Models from different vendors share overlapping public training corpora and architectural lineage (transformer-based, RLHF-tuned). They have different proprietary data, fine-tuning objectives, and default behaviors. Say what's actually shared and what's actually different.
- **Initial and final statistics both matter.** When reporting agreement metrics, include the initial-stage values alongside the post-arbitration values. Reporting only the best number is cherry-picking.

## Voice

- **This is evaluation framework translation, not empirical validation.** The crosswalk is expert judgment applied in institutional context. Like any translation, it is interpretive and temporal. Do not overclaim empirical rigor for what is fundamentally a governance translation exercise.
- **Coordination framing, not default-behavior framing.** The problem is not that agencies default to one framework. The problem is that without a shared crosswalk, each agency independently interprets how frameworks relate, producing inconsistent approaches. The crosswalk is a coordination tool.

## Prose Quality

- **No throat-clearing.** Delete "It is worth noting that," "It is important to recognize," "It should be noted that," and similar preambles. Start with the point.
- **No redundant framing.** If a paragraph states a finding, it does not need a second sentence restating it in different words. One statement, then evidence or implication.
- **No hedging stacks.** One hedge per claim maximum. "May suggest" is fine. "May potentially be considered to suggest" is not.
- **No self-congratulation.** The results speak. Delete "remarkably," "notably," "strikingly," "importantly." If the result is remarkable, the numbers show it.
- **Sentence length.** If a sentence exceeds 35 words, split it or find the clause that can become its own sentence. Technical precision is not an excuse for run-on syntax.
- **Prefer active voice.** "We tested" not "It was tested." Passive is acceptable when the actor is irrelevant or unknown.
- **Prefer short declarative sentences over compound joins.** Do not use semicolons or commas to jam two independent thoughts into one sentence. If two clauses can each stand as a sentence, they usually should. Compound sentences are acceptable when the clauses are genuinely interdependent, but defaulting to periods produces cleaner prose.
- **One idea per paragraph.** If a paragraph covers two distinct points, it is two paragraphs.
- **Minimum two sentences per paragraph in prose sections.** A single sentence standing alone as a paragraph is almost always either a transition that belongs attached to the preceding or following paragraph, or an underdeveloped idea. Definitional passages and labeled-list items are exempt.
- **Avoid nominalizations.** "Explains" not "provides an explanation of." "Differs" not "exhibits a difference from." Convert noun constructions back to verbs wherever possible.
- **Pronoun antecedents must be unambiguous.** "This" and "It" opening a sentence must refer to a noun stated in the immediately preceding sentence. If the referent is a clause or an idea rather than a named noun, rewrite: "This finding" not "This."
- **Tense consistency.** Results and experimental actions are past tense. Claims about the system, framework, or paper are present tense. Do not mix within a paragraph.
- **First-person consistency.** Use "we" throughout. Do not drift to "the authors," "one," or "the paper." "We" is appropriate for single-author academic work and preferred over passive constructions.

## Paper-Specific Rules (Pragmatics Paper Only)

These rules apply to the FCSM 2026 pragmatics paper and override or supplement the
general conventions above where they conflict.

### Vocabulary

- **No "graph traversal" language.** The runtime retrieval mechanism is a SQLite
  lookup, not a graph traversal. Use "SQLite lookup," "compiled lookup," or
  "deterministic lookup." Do not use "graph traversal," "traverse the graph,"
  "graph query," or similar phrasing. This applies to all sections, figures, captions,
  and appendices.
- **"Knowledge representation study" not "ablation study."** The study design compares
  representation methods, not ablates components. Never use "ablation."
- **"Confabulate"/"confabulation" not "hallucinate"/"hallucination."** Consistent with
  NIST AI 600-1 and already mandated in general conventions. Repeated here for emphasis.

### Framing

- **"Open-source MCP server for Census data retrieval"** not "Census Bureau API tools."
  The tool is Brock's open-source server (cite @webb2025censusmcp), not an official
  Census Bureau product.
