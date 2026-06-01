"""
Pydantic schemas for the /solve endpoint.
These are the shapes of data coming in from HTTP and going back out.
They are NOT the database models — see models/ for those.
"""
from typing import List, Optional
from enum import Enum
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ProblemType(str, Enum):
    ARITHMETIC = "arithmetic"
    SYMBOLIC = "symbolic"
    CONCEPTUAL = "conceptual"
    MIXED = "mixed"
    UNKNOWN = "unknown"


# ── Request ───────────────────────────────────────────────────────────────────
class SolveRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=2,
        max_length=2000,
        description="The math problem in plain text or LaTeX.",
        examples=["Integrate x^2 with respect to x", "What is 247 * 389?"],
    )
    session_id: Optional[str] = Field(
        None,
        description="Pass an existing session_id to continue a conversation. "
                    "Omit to start a new session.",
    )
    show_steps: bool = Field(True, description="Include step-by-step solution breakdown.")

    @field_validator("query")
    @classmethod
    def query_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Query cannot be blank.")
        return v.strip()


# ── Response pieces ───────────────────────────────────────────────────────────
class SolutionStep(BaseModel):
    step_number: int
    title: str
    explanation: str
    latex: Optional[str] = None


class SolveResponse(BaseModel):
    problem_id: str
    session_id: str
    query: str
    answer: str
    latex_answer: Optional[str] = None
    problem_type: ProblemType
    steps: List[SolutionStep] = []
    confidence: float = Field(..., ge=0.0, le=1.0)
    tools_used: List[str] = []
    cache_hit: bool = False
    latency_ms: float
    created_at: datetime

    model_config = {"from_attributes": True}


# ── History ───────────────────────────────────────────────────────────────────
class SolveHistoryItem(BaseModel):
    problem_id: str
    query: str
    answer: str
    confidence: float
    created_at: datetime

    model_config = {"from_attributes": True}
