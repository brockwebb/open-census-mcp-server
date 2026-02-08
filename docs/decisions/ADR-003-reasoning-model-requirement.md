# ADR-003: Reasoning Model Requirement

## Status
Accepted

## Context
Testing revealed that lightweight agent prompts fail catastrophically 
on models below reasoning threshold (Haiku 3.5). Failures include:
- Wrong tool selection (Hugging Face papers for recipes)
- Ignoring conditional logic
- Defaulting to system prompt behaviors over user instructions

## Decision
**Minimum caller requirement: Haiku 3.5 or equivalent reasoning capability.**

MCP design assumes caller can:
- Route to appropriate tools based on intent
- Interpret bundled guidance
- Follow conditional logic ("if X, then check Y")

MCP will NOT:
- Compensate for weak reasoning with complex routing
- Include LLM inside MCP
- Build multiple fallback strategies for model tiers

MCP WILL:
- Validate requests (hard stops on impossible data)
- Bundle guidance in every response
- Return structured data for caller to interpret

## Consequences
- Users on weaker models get degraded experience (acceptable)
- Forced obsolescence of pre-reasoning models (intentional)
- Simpler MCP architecture
- Clear support boundary

## Rationale
Jobs Doctrine on Creative Destruction: In his 2005 Stanford commencement 
address, Steve Jobs described death as "very likely the single best 
invention of life... it clears out the old to make way for the new."

At Apple, Jobs applied this as willingness to kill successful products 
to introduce superior technology—ensuring the company never became 
stagnant by clinging to past successes.

Applied here: We will not architect around legacy model limitations. 
Building compensatory complexity to support pre-reasoning models creates 
technical debt that prevents the system from evolving. The old must be 
allowed to become obsolete so the new can thrive.
