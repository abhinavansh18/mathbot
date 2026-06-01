"""
Verifier Node — scores the solution's confidence and corrects errors.
If confidence < threshold, the graph re-routes back to tools_node.
"""
from pydantic import BaseModel

from langchain_groq import ChatGroq
from agents.state import AgentState
from core.config import settings
from core.logging import get_logger
from core.metrics import agent_confidence_score
from prompts.verifier_prompt import get_verifier_prompt

log = get_logger(__name__)


class VerifierOutput(BaseModel):
    confidence: float               # 0.0 – 1.0
    is_mathematically_valid: bool
    identified_errors: list[str]
    corrected_solution: str | None
    verification_notes: str


async def verifier_node(state: AgentState) -> AgentState:
    """
    Independently re-checks the solution.
    Uses a low temperature to get a consistent, critical assessment.
    """
    log.info("agent.verifier.started", retry_count=state.get("retry_count", 0))

    llm = ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=settings.LLM_MODEL,
        temperature=0.0,
        max_tokens=512,
    )
    structured_llm = llm.with_structured_output(VerifierOutput)
    prompt = get_verifier_prompt()

    try:
        result: VerifierOutput = await structured_llm.ainvoke(
            prompt.format_messages(
                query=state["query"],
                solution=state.get("raw_solution", ""),
                problem_type=state.get("problem_type", "unknown"),
            )
        )

        # Record metric
        agent_confidence_score.observe(result.confidence)

        final_solution = result.corrected_solution or state.get("raw_solution", "")
        new_retry_count = state.get("retry_count", 0) + (
            1 if result.confidence < settings.VERIFICATION_CONFIDENCE_THRESHOLD else 0
        )

        log.info(
            "agent.verifier.completed",
            confidence=result.confidence,
            valid=result.is_mathematically_valid,
            errors=result.identified_errors,
        )
        return {
            **state,
            "confidence_score": result.confidence,
            "identified_errors": result.identified_errors,
            "verified_solution": final_solution,
            "retry_count": new_retry_count,
        }

    except Exception as exc:
        log.error("agent.verifier.failed", error=str(exc))
        # On verifier failure, pass through with low confidence
        return {
            **state,
            "confidence_score": 0.5,
            "identified_errors": [f"Verifier failed: {str(exc)}"],
            "verified_solution": state.get("raw_solution", ""),
            "retry_count": state.get("retry_count", 0) + 1,
        }
