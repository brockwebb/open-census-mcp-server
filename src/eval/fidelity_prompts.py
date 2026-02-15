"""Fidelity check prompts for Stage 3 evaluation.

Treatment verification extracts and verifies claims against tool call data.
Control auditability classifies claim specificity for external verification.
"""

TREATMENT_VERIFICATION_PROMPT = """You are verifying the factual accuracy of a Census data response by checking every claim against the tool call data that was used to generate it.

## Your Task

Extract EVERY verifiable claim from the response (numbers, percentages, variable codes, FIPS codes, table names, MOEs) and verify each against the tool call results.

## Tool Call Data Available

{tool_data}

## Response to Verify

{response_text}

## Verification Rules

For each claim, determine:
- **match**: Claim matches tool call data exactly (within rounding for percentages)
- **mismatch**: Claim contradicts tool call data
- **no_source**: Claim has no corresponding value in tool call data
- **calculation_correct**: Calculated value (e.g., percentage, rate) is mathematically correct given source data
- **calculation_incorrect**: Calculated value is mathematically wrong given source data

## Output Format

Return a JSON object with this structure:
```json
{{
  "claims": [
    {{
      "claim_text": "The exact text of the claim from the response",
      "claim_type": "value|percentage|variable_code|fips_code|table_name|moe|calculation",
      "tool_source": "Description of which tool call and field this comes from",
      "verdict": "match|mismatch|no_source|calculation_correct|calculation_incorrect",
      "detail": "Brief explanation of verification"
    }}
  ]
}}
```

Extract ALL verifiable claims. Be thorough. If the response says "B17001_002E = 492,910", that's 2 claims (variable code + value).
"""


CONTROL_AUDITABILITY_PROMPT = """You are classifying the auditability of claims in a Census data response that was generated WITHOUT access to Census data tools.

## Your Task

Extract every factual/quantitative claim and classify how auditable it is for external verification.

## Response to Classify

{response_text}

## Classification Rules

For each claim, assign specificity:
- **auditable**: Has table/variable code + vintage/year + geography + specific value (e.g., "B19013 median household income in 2022 for California: $84,097")
- **partially_auditable**: Has 2 of 3 required identifiers (table OR vintage OR geography missing, but has specific value)
- **unauditable**: Lacks table, vintage, or geography identifiers (e.g., "approximately 12-13%", "recent data shows...")
- **non_claim**: Not a factual claim (methodology explanation, general context, definitions)

## Output Format

Return a JSON object with this structure:
```json
{{
  "claims": [
    {{
      "claim_text": "The exact text of the claim from the response",
      "claim_type": "quantitative|qualitative|methodological",
      "specificity": "auditable|partially_auditable|unauditable|non_claim",
      "detail": "Brief explanation of classification"
    }}
  ]
}}
```

Extract ALL claims. Include vague statements like "recent surveys suggest" (unauditable) and specific citations (auditable).
"""


def build_treatment_prompt(response_text: str, tool_calls: list[dict]) -> str:
    """Build treatment verification prompt with tool call data.

    Args:
        response_text: The treatment response to verify
        tool_calls: List of successful get_census_data tool calls with results

    Returns:
        Complete prompt for treatment verification
    """
    # Format tool call data for readability
    tool_data_lines = []
    for i, call in enumerate(tool_calls, 1):
        tool_data_lines.append(f"## Tool Call {i}")
        tool_data_lines.append(f"Arguments: {call.get('arguments', {})}")
        tool_data_lines.append(f"Data: {call.get('data', [])}")
        tool_data_lines.append("")

    tool_data = "\n".join(tool_data_lines)

    return TREATMENT_VERIFICATION_PROMPT.format(
        tool_data=tool_data,
        response_text=response_text
    )


def build_control_prompt(response_text: str) -> str:
    """Build control auditability prompt.

    Args:
        response_text: The control response to classify

    Returns:
        Complete prompt for control auditability classification
    """
    return CONTROL_AUDITABILITY_PROMPT.format(response_text=response_text)


RAG_FIDELITY_PROMPT = """You are verifying the factual accuracy of a Census data response by checking every claim against the reference materials that were retrieved and provided to the model.

## Your Task

Extract EVERY verifiable claim from the response and verify each against the retrieved reference materials.

## Retrieved Reference Materials

{chunk_data}

## Response to Verify

{response_text}

## Verification Rules

For each claim, determine:
- **match**: Claim is supported by the retrieved reference materials
- **mismatch**: Claim contradicts the retrieved reference materials
- **no_source**: Claim has no corresponding content in retrieved materials
- **calculation_correct**: Calculated value is mathematically correct given source data
- **calculation_incorrect**: Calculated value is mathematically wrong given source data

## Output Format

Return a JSON object with this structure:
```json
{{
  "claims": [
    {{
      "claim_text": "The exact text of the claim from the response",
      "claim_type": "value|methodology|definition|geographic|threshold|recommendation",
      "chunk_source": "Which chunk (by number) this comes from, or 'none'",
      "verdict": "match|mismatch|no_source|calculation_correct|calculation_incorrect",
      "detail": "Brief explanation of verification"
    }}
  ]
}}
```

Extract ALL verifiable claims. Include methodology claims (e.g., "ACS uses a rolling sample"), definition claims (e.g., "MOE is at 90% confidence"), and recommendation claims (e.g., "use 5-year estimates for small areas").
"""


def build_rag_fidelity_prompt(response_text: str, chunk_data: str) -> str:
    """Build RAG fidelity verification prompt with retrieved chunks.

    Args:
        response_text: The RAG response to verify
        chunk_data: Formatted string of retrieved chunks

    Returns:
        Complete prompt for RAG fidelity verification
    """
    return RAG_FIDELITY_PROMPT.format(
        response_text=response_text,
        chunk_data=chunk_data
    )
