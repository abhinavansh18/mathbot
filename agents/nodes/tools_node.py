"""
Tools Node — runs the tools selected by the router and collects their outputs.
Each tool runs in a sandboxed subprocess with a hard timeout.
"""
import asyncio

from agents.state import AgentState
from core.logging import get_logger
from core.metrics import tool_calls_total
from tools.calculator import run_calculator
from tools.sympy_tool import run_sympy
from tools.wikipedia import run_wikipedia

log = get_logger(__name__)

TOOL_REGISTRY = {
    "calculator": run_calculator,
    "sympy": run_sympy,
    "wikipedia": run_wikipedia,
}


async def tools_node(state: AgentState) -> AgentState:
    """
    Runs all selected tools concurrently (asyncio.gather).
    Failed tools are recorded as error results — they don't crash the pipeline.
    """
    selected = state.get("selected_tools", [])
    query = state["query"]

    log.info("agent.tools.started", tools=selected, retry=state.get("retry_count", 0))

    async def run_tool(tool_name: str) -> dict:
        tool_calls_total.labels(tool_name=tool_name).inc()
        fn = TOOL_REGISTRY.get(tool_name)
        if not fn:
            return {"tool": tool_name, "result": None, "success": False, "error": "Unknown tool"}
        try:
            result = await fn(query)
            return {"tool": tool_name, "result": result, "success": True}
        except Exception as exc:
            log.warning("agent.tool.failed", tool=tool_name, error=str(exc))
            return {"tool": tool_name, "result": None, "success": False, "error": str(exc)}

    tool_results = await asyncio.gather(*[run_tool(t) for t in selected])
    successful = [r["tool"] for r in tool_results if r["success"]]

    log.info("agent.tools.completed", successful=successful)
    return {
        **state,
        "tool_results": list(tool_results),
        "tools_used": successful,
        "retry_count": state.get("retry_count", 0),
    }
