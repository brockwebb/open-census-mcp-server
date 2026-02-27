# AI-Assisted Prose Editing Workflow

**Context:** LLM-generated academic prose requires human editorial judgment. Current AI tooling (Claude Code, Cursor, etc.) excels at mechanical text operations but lacks the judgment to distinguish redundant framing from intentional emphasis, or throat-clearing from necessary hedging.

## The Problem

Prose quality edits are high-judgment, low-automation. A grep can find "It is worth noting that" but cannot decide whether a 40-word sentence should be split at the subordinate clause or rewritten entirely. Fully automated editing produces bland, uniform prose. Fully manual editing doesn't leverage AI capability.

## Workflow: Split Judgment from Execution

1. **AI reads section, flags specific sentences** with the convention violated and a proposed rewrite. Output to chat, never directly to files.
2. **Human approves, rejects, or modifies** each proposed edit in conversation.
3. **AI batches approved edits as exact string replacements** and sends to a code execution agent (Claude Code, etc.) for mechanical application.
4. **Build verification** confirms no structural damage.

## Why This Works

- Judgment stays in the interactive loop where human and AI can negotiate meaning
- File manipulation stays in the deterministic tool where exact-match replacement is reliable
- No edit touches a file without explicit human approval
- The audit trail is the conversation itself

## Current Limitations (Feb 2026)

- No UI for inline markup/accept/reject (like Word track changes or Google Docs suggestions)
- Conversation context window constrains how many sections can be reviewed per session
- No persistent "editing session" state between threads — each new thread re-reads files
- CC cannot preview edits in-place; human must mentally map string replacements to document

## Future: What Would Fix This

- A diff-preview mode: AI proposes edits as a rendered side-by-side diff before applying
- Persistent editing state across sessions (which edits were approved, which sections reviewed)
- Inline annotation tool: AI marks up a document with comments, human resolves them
- Batch approval UI: review 20 proposed edits as a checklist rather than sequential chat turns
