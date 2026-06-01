"""
Unit tests for MathService.
Agent and repositories are mocked — we test orchestration logic only.
"""
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from services.math_service import MathService
from schemas.solve import SolveRequest, ProblemType
from cache.client import CacheClient


def _make_service(mock_db=None, mock_redis=None, user_id="user-123"):
    db = mock_db or AsyncMock()
    redis = mock_redis or AsyncMock()

    # Patch CacheClient methods
    cache = AsyncMock(spec=CacheClient)
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)

    service = MathService(db=db, cache=cache, user_id=user_id)
    service.cache = cache
    service.problem_repo = AsyncMock()
    service.solution_repo = AsyncMock()
    service.session_repo = AsyncMock()
    service.session_repo.get = AsyncMock(return_value=None)
    return service


def _make_graph_result(answer="4", confidence=0.95):
    return {
        "query": "2 + 2",
        "session_history": [],
        "user_id": "user-123",
        "problem_type": ProblemType.ARITHMETIC,
        "selected_tools": ["calculator"],
        "tool_results": [{"tool": "calculator", "result": "4", "success": True}],
        "raw_solution": f"The answer is {answer}",
        "steps": [{"step_number": 1, "title": "Calculate", "explanation": "2 + 2 = 4"}],
        "latex_answer": None,
        "verified_solution": f"The answer is {answer}",
        "confidence_score": confidence,
        "identified_errors": [],
        "retry_count": 0,
        "final_answer": answer,
        "tools_used": ["calculator"],
        "error": None,
    }


@pytest.mark.asyncio
async def test_solve_returns_response_on_success():
    service = _make_service()

    with patch("services.math_service.get_math_graph") as mock_graph_fn:
        mock_graph = AsyncMock()
        mock_graph.ainvoke = AsyncMock(return_value=_make_graph_result())
        mock_graph_fn.return_value = mock_graph

        request = SolveRequest(query="2 + 2", show_steps=True)
        response = await service.solve(request)

    assert response.answer == "4"
    assert response.confidence == 0.95
    assert response.cache_hit is False


@pytest.mark.asyncio
async def test_solve_returns_cache_hit():
    service = _make_service()

    cached_data = {
        "problem_id": "abc",
        "session_id": "sess-1",
        "query": "2 + 2",
        "answer": "4",
        "latex_answer": None,
        "problem_type": "arithmetic",
        "steps": [],
        "confidence": 0.95,
        "tools_used": ["calculator"],
        "cache_hit": True,
        "latency_ms": 10.0,
        "created_at": datetime.utcnow().isoformat(),
    }
    service.cache.get = AsyncMock(return_value=json.dumps(cached_data))

    request = SolveRequest(query="2 + 2")
    response = await service.solve(request)

    assert response.cache_hit is True
    assert response.answer == "4"


@pytest.mark.asyncio
async def test_solve_persists_to_db():
    service = _make_service()
    service.problem_repo.create = AsyncMock()
    service.solution_repo.create = AsyncMock()

    with patch("services.math_service.get_math_graph") as mock_graph_fn:
        mock_graph = AsyncMock()
        mock_graph.ainvoke = AsyncMock(return_value=_make_graph_result())
        mock_graph_fn.return_value = mock_graph

        await service.solve(SolveRequest(query="2 + 2"))

    service.problem_repo.create.assert_called_once()
    service.solution_repo.create.assert_called_once()
