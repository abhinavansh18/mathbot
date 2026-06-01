"""
Integration tests for POST /api/v1/solve.
These tests hit the real FastAPI app with a real (test) database and mocked LLM/agent.
"""
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime
from schemas.solve import ProblemType


def _mock_graph_result(answer="4", problem_type=ProblemType.ARITHMETIC):
    return {
        "query": "2 + 2",
        "session_history": [],
        "user_id": "test-user-id-123",
        "problem_type": problem_type,
        "selected_tools": ["calculator"],
        "tool_results": [{"tool": "calculator", "result": answer, "success": True}],
        "raw_solution": f"The answer is {answer}",
        "steps": [{"step_number": 1, "title": "Add", "explanation": f"2 + 2 = {answer}"}],
        "latex_answer": None,
        "verified_solution": f"The answer is {answer}",
        "confidence_score": 0.95,
        "identified_errors": [],
        "retry_count": 0,
        "final_answer": answer,
        "tools_used": ["calculator"],
        "error": None,
    }


@pytest.mark.asyncio
async def test_solve_requires_auth(client):
    response = await client.post("/api/v1/solve", json={"query": "2 + 2"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_solve_success(client, auth_headers):
    with patch("services.math_service.get_math_graph") as mock_graph_fn:
        mock_graph = AsyncMock()
        mock_graph.ainvoke = AsyncMock(return_value=_mock_graph_result())
        mock_graph_fn.return_value = mock_graph

        response = await client.post(
            "/api/v1/solve",
            json={"query": "What is 2 + 2?", "show_steps": True},
            headers=auth_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "4"
    assert data["confidence"] == 0.95
    assert data["cache_hit"] is False
    assert "problem_id" in data
    assert "session_id" in data


@pytest.mark.asyncio
async def test_solve_validates_empty_query(client, auth_headers):
    response = await client.post(
        "/api/v1/solve",
        json={"query": "   "},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_solve_validates_query_too_short(client, auth_headers):
    response = await client.post(
        "/api/v1/solve",
        json={"query": "x"},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "redis" in data


@pytest.mark.asyncio
async def test_liveness_endpoint(client):
    response = await client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"
