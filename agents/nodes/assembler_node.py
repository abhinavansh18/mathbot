"""
Assembler Node — last node in the graph.
Packages the verified solution, steps, and metadata into the final state shape
that services/math_service.py will read.
"""
from agents.state import AgentState
from core.logging import get_logger
from schemas.solve import ProblemType

log = get_logger(__name__)


async def assembler_node(state: AgentState) -> AgentState:
    """
    Pure transformation — no LLM calls.
    Picks the best available answer and normalises the state.
    """
    # Prefer verified solution; fall back to raw
    final_answer = (
        state.get("verified_solution")
        or state.get("raw_solution")
        or "Unable to solve — please try rephrasing the problem."
    )

    problem_type = state.get("problem_type") or ProblemType.UNKNOWN

    log.info(
        "agent.assembler.completed",
        confidence=state.get("confidence_score", 0.0),
        steps=len(state.get("steps", [])),
        tools=state.get("tools_used", []),
    )

    return {
        **state,
        "final_answer": final_answer,
        "problem_type": problem_type,
        "tools_used": state.get("tools_used", []),
        "steps": state.get("steps", []),
        "latex_answer": state.get("latex_answer"),
        "confidence_score": state.get("confidence_score", 0.0),
    }
