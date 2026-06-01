"""
MathService — orchestrates the full solve pipeline.
  1. Check Redis cache
  2. Load session history
  3. Run LangGraph agent
  4. Persist result to PostgreSQL
  5. Write to Redis cache
  6. Return structured response
"""
import json
import time
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from agents.math_agent import get_math_graph
from agents.state import AgentState
from cache.client import CacheClient
from cache.keys import solve_cache_key, session_key
from core.config import settings
from core.exceptions import AgentTimeoutError
from core.logging import get_logger
from core.metrics import (
    solve_requests_total,
    solve_latency_seconds,
    cache_operations_total,
)
from repositories.problem_repository import ProblemRepository
from repositories.solution_repository import SolutionRepository
from repositories.session_repository import SessionRepository
from schemas.solve import SolveRequest, SolveResponse, SolutionStep, ProblemType

log = get_logger(__name__)


class MathService:
    def __init__(
        self,
        db: AsyncSession,
        cache: CacheClient,
        user_id: str,
    ):
        self.db = db
        self.cache = cache
        self.user_id = user_id
        self.problem_repo = ProblemRepository(db)
        self.solution_repo = SolutionRepository(db)
        self.session_repo = SessionRepository(db)

    async def solve(self, request: SolveRequest) -> SolveResponse:
        start = time.monotonic()

        # ── 1. Cache check ────────────────────────────────────────────────────
        cache_key = solve_cache_key(request.query)
        cached = await self.cache.get(cache_key)
        if cached:
            cache_operations_total.labels(result="hit").inc()
            data = json.loads(cached)
            data["cache_hit"] = True
            log.info("solve.cache_hit", query=request.query[:60])
            return SolveResponse(**data)

        cache_operations_total.labels(result="miss").inc()

        # ── 2. Load session history ───────────────────────────────────────────
        session_id = request.session_id or str(uuid.uuid4())
        session_history = await self._load_session(session_id)

        # ── 3. Run agent ──────────────────────────────────────────────────────
        initial_state: AgentState = {
            "query": request.query,
            "session_history": session_history,
            "user_id": self.user_id,
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

        graph = get_math_graph()
        try:
            final_state: AgentState = await graph.ainvoke(
                initial_state,
                config={"recursion_limit": settings.AGENT_MAX_ITERATIONS},
            )
        except Exception as exc:
            log.error("solve.agent_failed", error=str(exc))
            raise AgentTimeoutError(str(exc)) from exc

        # ── 4. Build response ─────────────────────────────────────────────────
        latency_ms = (time.monotonic() - start) * 1000
        solve_latency_seconds.observe(latency_ms / 1000)

        steps = [
            SolutionStep(**s) for s in (final_state.get("steps") or [])
        ] if request.show_steps else []

        problem_type = final_state.get("problem_type") or ProblemType.UNKNOWN
        solve_requests_total.labels(status="success", problem_type=problem_type.value).inc()

        response = SolveResponse(
            problem_id=str(uuid.uuid4()),
            session_id=session_id,
            query=request.query,
            answer=final_state.get("final_answer", "No answer generated."),
            latex_answer=final_state.get("latex_answer"),
            problem_type=problem_type,
            steps=steps,
            confidence=final_state.get("confidence_score", 0.0),
            tools_used=final_state.get("tools_used", []),
            cache_hit=False,
            latency_ms=round(latency_ms, 2),
            created_at=datetime.utcnow(),
        )

        # ── 5. Persist & cache (fire-and-forget) ──────────────────────────────
        await self._persist(response)
        await self._update_session(session_id, request.query, response.answer)
        await self.cache.set(cache_key, response.model_dump_json())

        return response

    # ── Private helpers ───────────────────────────────────────────────────────
    async def _load_session(self, session_id: str) -> list[dict]:
        """Returns recent message history from Redis (fast) or PostgreSQL (cold)."""
        cached = await self.cache.get(session_key(session_id))
        if cached:
            return json.loads(cached)

        session = await self.session_repo.get(session_id)
        if session and session.messages_json:
            return json.loads(session.messages_json)
        return []

    async def _persist(self, response: SolveResponse) -> None:
        """Writes the problem and solution to PostgreSQL."""
        try:
            problem = await self.problem_repo.create(
                problem_id=response.problem_id,
                user_id=self.user_id,
                session_id=response.session_id,
                query=response.query,
                problem_type=response.problem_type.value,
            )
            await self.solution_repo.create(
                problem_id=response.problem_id,
                answer=response.answer,
                latex_answer=response.latex_answer,
                steps_json=json.dumps([s.model_dump() for s in response.steps]),
                confidence=response.confidence,
                tools_used=",".join(response.tools_used),
                latency_ms=response.latency_ms,
            )
        except Exception as exc:
            log.error("solve.persist_failed", error=str(exc))

    async def _update_session(self, session_id: str, query: str, answer: str) -> None:
        """Appends this exchange to the session history in Redis."""
        cached = await self.cache.get(session_key(session_id))
        history = json.loads(cached) if cached else []
        history.append({"role": "user", "content": query})
        history.append({"role": "assistant", "content": answer})
        # Keep only last 20 messages to control token usage
        history = history[-20:]
        await self.cache.set(session_key(session_id), json.dumps(history))
