# Architecture Overview

## Why FastAPI instead of Streamlit?

Streamlit is a prototyping tool. It runs as a single process, stores state in session memory,
cannot serve multiple users independently, and cannot expose a proper REST API.

FastAPI separates the backend from any frontend. It supports async I/O natively, has automatic
OpenAPI documentation, integrates directly with Pydantic for validation, and supports dependency
injection for clean testing. The original Streamlit app could be kept as a UI and talk to the
FastAPI backend — both can coexist.

## Why LangGraph instead of initialize_agent?

`initialize_agent` is a black box. You cannot see which node runs next, you cannot inject
custom logic between steps, and you cannot control retry behaviour precisely.

LangGraph exposes every step as an explicit node in a graph. The edges between nodes can be
conditional (e.g., "if confidence < 0.8, route back to tools"). This makes the agent's
behaviour testable, debuggable, and modifiable without touching the LLM prompt.

## Why PostgreSQL + Redis instead of just one database?

They solve different problems.

PostgreSQL is for structured, relational, persistent data — users, problems, solutions.
It provides ACID guarantees, which means a solution is either saved completely or not at all.

Redis is for fast, ephemeral data — sessions, rate limit counters, query caches.
Reading a session from Redis takes <1ms. Reading from PostgreSQL takes 10–50ms.
For a chat application where every message needs session history, this difference is felt immediately.

## Why Celery for OCR?

The pix2tex model takes 1–5 seconds to run. If this runs synchronously in a FastAPI request
handler, the API thread is blocked during that entire time, and no other requests can be processed.

Celery offloads the work to a separate process. The API receives the upload, queues the OCR job,
and returns immediately. The client can poll for the result. This keeps API latency fast
regardless of how slow the OCR computation is.

## Why sandboxed subprocess execution?

The original code used `exec()` with LLM-generated code inside the main process.
If the LLM generates malicious code (or makes a mistake that causes an infinite loop),
it runs with full access to the filesystem, network, and environment variables.

The sandbox runs code in a child process with:
- A hard timeout (process killed if it exceeds N seconds)
- Memory limits on Linux (via the `resource` module)
- Blocked dangerous imports (`os`, `subprocess`, `socket`, etc.)

If the sandboxed code crashes or hangs, the parent process is unaffected.

## Request Flow (detailed)

```
POST /api/v1/solve
    │
    ├── LoggingMiddleware: bind request_id to log context
    ├── RateLimitMiddleware: check Redis counter for user+route
    ├── OAuth2 dependency: validate JWT, extract user_id
    ├── Pydantic: validate SolveRequest schema
    │
    └── MathService.solve()
            │
            ├── CacheClient.get(solve_cache_key(query))
            │   ├── HIT  → return SolveResponse (cache_hit=True)
            │   └── MISS → continue
            │
            ├── SessionRepository / Redis → load session history
            │
            ├── LangGraph graph.ainvoke(initial_state)
            │   ├── router_node    → problem_type, selected_tools
            │   ├── tools_node     → run tools concurrently
            │   ├── reasoner_node  → step-by-step solution
            │   ├── verifier_node  → confidence score
            │   │   ├── < 0.8 and retries < 2 → back to tools_node
            │   │   └── >= 0.8 or retries == 2 → assembler_node
            │   └── assembler_node → final_answer, tools_used, steps
            │
            ├── ProblemRepository.create()  (async, PostgreSQL)
            ├── SolutionRepository.create() (async, PostgreSQL)
            ├── CacheClient.set(cache_key, response, ttl=3600)
            ├── Redis session update
            │
            └── return SolveResponse
```
