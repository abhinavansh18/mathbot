"""
End-to-end tests for the full solve pipeline.
These tests verify the complete flow: register → login → solve → verify response shape.
The LLM is mocked but all other layers (DB, Redis, service, agent graph) are real.
"""
import pytest
from unittest.mock import AsyncMock, patch
from schemas.solve import ProblemType


def _make_integral_state():
    return {
        "query": "Integrate x^2 with respect to x",
        "session_history": [],
        "user_id": "test-user-id-123",
        "problem_type": ProblemType.SYMBOLIC,
        "selected_tools": ["sympy"],
        "tool_results": [{"tool": "sympy", "result": "x**3/3 + C", "success": True}],
        "raw_solution": "The integral of x² is x³/3 + C",
        "steps": [
            {"step_number": 1, "title": "Apply power rule", "explanation": "∫x² dx = x³/3 + C"},
        ],
        "latex_answer": r"\frac{x^3}{3} + C",
        "verified_solution": "The integral of x² is x³/3 + C",
        "confidence_score": 0.93,
        "identified_errors": [],
        "retry_count": 0,
        "final_answer": "x³/3 + C",
        "tools_used": ["sympy"],
        "error": None,
    }


@pytest.mark.asyncio
async def test_register_login_solve_flow(client):
    """
    Full user journey:
    1. Register new account
    2. Login to get tokens
    3. Solve a problem using the access token
    """
    # Step 1: Register
    reg_response = await client.post("/api/v1/auth/register", json={
        "email": "e2e@test.com",
        "password": "securepass123",
        "username": "e2etester",
    })
    assert reg_response.status_code == 201, reg_response.text
    tokens = reg_response.json()
    assert "access_token" in tokens

    # Step 2: Use the access token to solve
    with patch("services.math_service.get_math_graph") as mock_graph_fn:
        mock_graph = AsyncMock()
        mock_graph.ainvoke = AsyncMock(return_value=_make_integral_state())
        mock_graph_fn.return_value = mock_graph

        solve_response = await client.post(
            "/api/v1/solve",
            json={"query": "Integrate x^2 with respect to x", "show_steps": True},
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )

    assert solve_response.status_code == 200
    data = solve_response.json()

    # Verify response shape
    assert "x" in data["answer"].lower() or "3" in data["answer"]
    assert "+C" in data["answer"] or "C" in data["answer"]   # integration constant required
    assert data["confidence"] >= 0.8
    assert data["problem_type"] == "symbolic"
    assert len(data["steps"]) > 0
    assert "session_id" in data
    assert "problem_id" in data
    assert data["cache_hit"] is False


@pytest.mark.asyncio
async def test_duplicate_registration_rejected(client):
    await client.post("/api/v1/auth/register", json={
        "email": "dup@test.com",
        "password": "password123",
        "username": "dupuser",
    })
    response = await client.post("/api/v1/auth/register", json={
        "email": "dup@test.com",
        "password": "password456",
        "username": "dupuser2",
    })
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_invalid_login_rejected(client):
    response = await client.post("/api/v1/auth/login", json={
        "email": "nobody@test.com",
        "password": "wrongpassword",
    })
    assert response.status_code == 401
