"""
Celery tasks for long-running solve jobs.
For problems that exceed typical HTTP timeout windows.
"""
from celery import shared_task
from workflows.celery_app import celery_app
from core.logging import get_logger

log = get_logger(__name__)


@celery_app.task(
    name="solve.async_solve",
    bind=True,
    max_retries=1,
    default_retry_delay=5,
    time_limit=120,
    soft_time_limit=90,
)
def async_solve_task(self, query: str, user_id: str, session_id: str) -> dict:
    """
    Background solve for long-running problems.
    The API immediately returns a task_id; the client polls for completion.

    Pattern:
        POST /solve  →  {"task_id": "abc123"}
        GET  /solve/status/abc123  →  {"status": "PENDING" | "SUCCESS", "result": ...}
    """
    import asyncio

    log.info("solve_task.started", query=query[:60], user_id=user_id)

    try:
        # We need to run async code in this sync Celery worker
        # Create a fresh event loop for this task
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        result = loop.run_until_complete(
            _run_solve(query=query, user_id=user_id, session_id=session_id)
        )
        loop.close()

        log.info("solve_task.completed", confidence=result.get("confidence"))
        return result

    except Exception as exc:
        log.error("solve_task.failed", error=str(exc))
        raise self.retry(exc=exc)


async def _run_solve(query: str, user_id: str, session_id: str) -> dict:
    """Inner async function — runs the LangGraph agent."""
    from agents.math_agent import get_math_graph
    from agents.state import AgentState
    from schemas.solve import ProblemType

    graph = get_math_graph()
    initial_state: AgentState = {
        "query": query,
        "session_history": [],
        "user_id": user_id,
        "problem_type": None,
        "selected_tools": [],
        "tool_results": [],
        "raw_solution": None,
        "steps": [],
        "latex_answer": None,
        "verified_solution": None,
        "confidence_score": 0.0,
        "identified_errors": [],
        "retry_count": 0,
        "final_answer": None,
        "tools_used": [],
        "error": None,
    }

    final_state = await graph.ainvoke(initial_state)
    return {
        "answer": final_state.get("final_answer", ""),
        "confidence": final_state.get("confidence_score", 0.0),
        "steps": final_state.get("steps", []),
        "tools_used": final_state.get("tools_used", []),
        "latex_answer": final_state.get("latex_answer"),
        "problem_type": (final_state.get("problem_type") or ProblemType.UNKNOWN).value,
    }
