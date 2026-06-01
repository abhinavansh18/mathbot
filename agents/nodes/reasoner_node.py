"""
Reasoner Node — takes tool results and generates a structured step-by-step solution.
This is the main LLM call where the actual math explanation is produced.
"""
import json

from langchain_groq import ChatGroq
from pydantic import BaseModel

from agents.state import AgentState
from core.config import settings
from core.logging import get_logger
from prompts.reasoner_prompt import get_reasoner_prompt

log = get_logger(__name__)


class ReasonerOutput(BaseModel):
    answer: str
    latex_answer: str | None
    steps: list[dict]     # [{"step_number": int, "title": str, "explanation": str}]
    raw_solution: str


async def reasoner_node(state: AgentState) -> AgentState:
    """
    Combines the original query + tool results into a coherent solution.
    """
    log.info("agent.reasoner.started")

    llm = ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=settings.LLM_MODEL,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
    )
    structured_llm = llm.with_structured_output(ReasonerOutput)
    prompt = get_reasoner_prompt()

    tool_summary = json.dumps(
        [
            {"tool": r["tool"], "result": r["result"]}
            for r in state.get("tool_results", [])
            if r["success"]
        ],
        indent=2,
    )

    try:
        result: ReasonerOutput = await structured_llm.ainvoke(
            prompt.format_messages(
                query=state["query"],
                tool_results=tool_summary,
                problem_type=state.get("problem_type", "unknown"),
                session_history=json.dumps(state.get("session_history", [])[-6:], indent=2),
            )
        )
        log.info("agent.reasoner.completed", steps=len(result.steps))
        return {
            **state,
            "raw_solution": result.raw_solution,
            "steps": result.steps,
            "latex_answer": result.latex_answer,
        }
    except Exception as exc:
        log.error("agent.reasoner.failed", error=str(exc))
        return {
            **state,
            "raw_solution": "Could not generate solution.",
            "steps": [],
            "error": str(exc),
        }
