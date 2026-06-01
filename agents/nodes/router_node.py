"""
Router Node — classifies the problem type and decides which tools to invoke.
Runs first in the graph. Output populates state["problem_type"] and state["selected_tools"].
"""
from langchain_groq import ChatGroq
from pydantic import BaseModel

from agents.state import AgentState
from core.config import settings
from core.logging import get_logger
from core.metrics import tool_calls_total
from prompts.router_prompt import get_router_prompt
from schemas.solve import ProblemType

log = get_logger(__name__)


class RouterOutput(BaseModel):
    problem_type: ProblemType
    selected_tools: list[str]
    reasoning: str


async def router_node(state: AgentState) -> AgentState:
    """
    Uses a structured LLM call to classify the problem and pick tools.
    Falls back to MIXED / all tools on any error.
    """
    log.info("agent.router.started", query=state["query"][:80])

    llm = ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=settings.LLM_MODEL,
        temperature=0.0,        # deterministic classification
        max_tokens=256,
    )
    structured_llm = llm.with_structured_output(RouterOutput)
    prompt = get_router_prompt()

    try:
        result: RouterOutput = await structured_llm.ainvoke(
            prompt.format_messages(query=state["query"])
        )
        log.info(
            "agent.router.completed",
            problem_type=result.problem_type,
            tools=result.selected_tools,
        )
        return {
            **state,
            "problem_type": result.problem_type,
            "selected_tools": result.selected_tools,
        }
    except Exception as exc:
        log.warning("agent.router.failed", error=str(exc))
        return {
            **state,
            "problem_type": ProblemType.MIXED,
            "selected_tools": ["calculator", "sympy", "wikipedia"],
        }
