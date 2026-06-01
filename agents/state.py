"""
LangGraph AgentState — the single object that flows through every node.
Every node reads from and writes to this state dict.
TypedDict gives us type-safety without runtime overhead.
"""
from typing import List, Optional, TypedDict

from schemas.solve import ProblemType


class AgentState(TypedDict):
    # ── Input ──────────────────────────────────────────────────────────────────
    query: str
    session_history: List[dict]          # [{"role": "user"|"assistant", "content": "..."}]
    user_id: str

    # ── Router outputs ─────────────────────────────────────────────────────────
    problem_type: Optional[ProblemType]
    selected_tools: List[str]            # e.g. ["calculator", "sympy"]

    # ── Tool outputs ───────────────────────────────────────────────────────────
    tool_results: List[dict]             # [{"tool": "sympy", "result": "...", "success": bool}]

    # ── Reasoning outputs ──────────────────────────────────────────────────────
    raw_solution: Optional[str]
    steps: List[dict]                    # [{"step_number": 1, "title": "...", "explanation": "..."}]
    latex_answer: Optional[str]

    # ── Verifier outputs ───────────────────────────────────────────────────────
    verified_solution: Optional[str]
    confidence_score: float
    identified_errors: List[str]
    retry_count: int

    # ── Final assembled output ─────────────────────────────────────────────────
    final_answer: Optional[str]
    tools_used: List[str]
    error: Optional[str]
