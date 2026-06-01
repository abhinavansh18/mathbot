"""
Unit tests for the router node — problem classification and tool selection.
The LLM call is mocked so tests run offline and are deterministic.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from agents.nodes.router_node import router_node
from agents.state import AgentState
from schemas.solve import ProblemType


def _base_state(query: str) -> AgentState:
    return {
        "query": query,
        "session_history": [],
        "user_id": "test-user",
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


class MockRouterOutput:
    def __init__(self, problem_type, selected_tools):
        self.problem_type = problem_type
        self.selected_tools = selected_tools
        self.reasoning = "test"


@pytest.mark.asyncio
async def test_router_classifies_arithmetic():
    with patch("agents.nodes.router_node.ChatGroq") as MockLLM:
        mock_llm_instance = MagicMock()
        mock_llm_instance.with_structured_output.return_value.ainvoke = AsyncMock(
            return_value=MockRouterOutput(ProblemType.ARITHMETIC, ["calculator"])
        )
        MockLLM.return_value = mock_llm_instance

        state = await router_node(_base_state("What is 247 * 389?"))

    assert state["problem_type"] == ProblemType.ARITHMETIC
    assert "calculator" in state["selected_tools"]
    assert "sympy" not in state["selected_tools"]


@pytest.mark.asyncio
async def test_router_classifies_integral():
    with patch("agents.nodes.router_node.ChatGroq") as MockLLM:
        mock_llm_instance = MagicMock()
        mock_llm_instance.with_structured_output.return_value.ainvoke = AsyncMock(
            return_value=MockRouterOutput(ProblemType.SYMBOLIC, ["sympy"])
        )
        MockLLM.return_value = mock_llm_instance

        state = await router_node(_base_state("Integrate x^2 dx"))

    assert state["problem_type"] == ProblemType.SYMBOLIC
    assert "sympy" in state["selected_tools"]


@pytest.mark.asyncio
async def test_router_falls_back_on_llm_error():
    """When LLM call fails, router should default to MIXED with all tools."""
    with patch("agents.nodes.router_node.ChatGroq") as MockLLM:
        mock_llm_instance = MagicMock()
        mock_llm_instance.with_structured_output.return_value.ainvoke = AsyncMock(
            side_effect=Exception("LLM API error")
        )
        MockLLM.return_value = mock_llm_instance

        state = await router_node(_base_state("Some problem"))

    assert state["problem_type"] == ProblemType.MIXED
    assert "sympy" in state["selected_tools"]
    assert "calculator" in state["selected_tools"]


@pytest.mark.asyncio
async def test_router_conceptual_uses_wikipedia():
    with patch("agents.nodes.router_node.ChatGroq") as MockLLM:
        mock_llm_instance = MagicMock()
        mock_llm_instance.with_structured_output.return_value.ainvoke = AsyncMock(
            return_value=MockRouterOutput(ProblemType.CONCEPTUAL, ["wikipedia"])
        )
        MockLLM.return_value = mock_llm_instance

        state = await router_node(_base_state("What is the Pythagorean theorem?"))

    assert state["problem_type"] == ProblemType.CONCEPTUAL
    assert "wikipedia" in state["selected_tools"]
