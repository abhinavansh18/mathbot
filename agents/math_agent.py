"""
MathBot LangGraph agent graph.
Compiles the StateGraph once and reuses the compiled graph across requests.
"""
from functools import lru_cache

from langgraph.graph import END, StateGraph

from agents.state import AgentState
from agents.nodes.router_node import router_node
from agents.nodes.tools_node import tools_node
from agents.nodes.reasoner_node import reasoner_node
from agents.nodes.verifier_node import verifier_node
from agents.nodes.assembler_node import assembler_node
from core.config import settings


def _should_retry_or_finish(state: AgentState) -> str:
    """
    Conditional edge from verifier:
    - confidence >= threshold  → assemble final response
    - confidence < threshold and retries remaining → try tools again
    - retries exhausted → assemble best attempt
    """
    threshold = settings.VERIFICATION_CONFIDENCE_THRESHOLD
    if state["confidence_score"] >= threshold:
        return "assembler"
    if state["retry_count"] < 2:
        return "tools"
    # Give up retrying — send whatever we have
    return "assembler"


def build_math_graph():
    """Build and compile the LangGraph StateGraph."""
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("router", router_node)
    graph.add_node("tools", tools_node)
    graph.add_node("reasoner", reasoner_node)
    graph.add_node("verifier", verifier_node)
    graph.add_node("assembler", assembler_node)

    # Define edges
    graph.set_entry_point("router")
    graph.add_edge("router", "tools")
    graph.add_edge("tools", "reasoner")
    graph.add_edge("reasoner", "verifier")
    graph.add_conditional_edges(
        "verifier",
        _should_retry_or_finish,
        {
            "assembler": "assembler",
            "tools": "tools",
        },
    )
    graph.add_edge("assembler", END)

    return graph.compile()


@lru_cache(maxsize=1)
def get_math_graph():
    """
    Returns the compiled graph — cached so compilation happens only once
    (compilation is expensive; execution is cheap).
    """
    return build_math_graph()
