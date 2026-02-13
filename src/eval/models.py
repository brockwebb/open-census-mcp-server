"""Pydantic models for CQS evaluation data structures."""
from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime


class ToolCall(BaseModel):
    """Record of a single tool call during agent loop."""
    tool_name: str
    arguments: dict
    result: dict  # parsed JSON from tool response
    latency_ms: float


class ResponseRecord(BaseModel):
    """Complete record of one response (control or treatment)."""
    query_id: str
    condition: Literal["control", "treatment"]
    model: str
    system_prompt: str
    response_text: str
    tool_calls: list[ToolCall] = []
    pragmatics_returned: list[str] = []  # context_ids extracted from tool results
    total_latency_ms: float
    input_tokens: int
    output_tokens: int
    timestamp: datetime
    tools_offered: bool = False  # True when tools were passed to the API
    tool_rounds_used: int = 0  # Number of agent loop iterations used
    tool_rounds_exhausted: bool = False  # True if forced synthesis was needed


class QueryPair(BaseModel):
    """Paired control + treatment for one query."""
    query_id: str
    query_text: str
    category: str
    difficulty: str
    control: ResponseRecord
    treatment: ResponseRecord


class DimensionScore(BaseModel):
    """Score for a single CQS dimension."""
    score: int  # 0, 1, or 2
    confidence: int  # 1-5
    reasoning: str


class JudgeRecord(BaseModel):
    """Complete record of one judge evaluation."""
    query_id: str
    judge_model: str
    judge_vendor: str
    presentation_order: str  # "control_first" or "treatment_first"
    scores_response_a: dict[str, DimensionScore]  # D1-D6 -> DimensionScore
    scores_response_b: dict[str, DimensionScore]  # D1-D6 -> DimensionScore
    preference: str  # "A" / "B" / "tie"
    preference_reasoning: str
    response_a_label: str  # "control" or "treatment"
    response_b_label: str  # "control" or "treatment"
    latency_ms: float
    input_tokens: int
    output_tokens: int
    timestamp: datetime
    run_id: str
    raw_response: str  # Full judge response for debugging
    parse_success: bool  # Whether JSON parsing succeeded
    pass_number: int = 1  # 1-6, which pass this measurement came from
