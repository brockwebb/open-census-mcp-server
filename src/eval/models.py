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


class QueryPair(BaseModel):
    """Paired control + treatment for one query."""
    query_id: str
    query_text: str
    category: str
    difficulty: str
    control: ResponseRecord
    treatment: ResponseRecord
