# MathBot 🤖➗

> **AI-powered math problem solver** with LaTeX OCR, symbolic computation, step-by-step verification, and a production-grade REST API.
> Built with FastAPI · LangGraph · Groq (Llama 3.3 70B) · PostgreSQL · Redis

---

## What It Does

You send a math problem (text or image). MathBot:

1. **Classifies** the problem (arithmetic, symbolic, conceptual)
2. **Selects tools** — calculator, SymPy, or Wikipedia
3. **Solves it** step-by-step using a LangGraph agent
4. **Verifies** the answer with a confidence score (re-tries if below 80%)
5. **Returns** a structured response with LaTeX, steps, and confidence

---

## Architecture

```
CLIENT
  │
  ▼
[nginx]  ──  rate limiting, reverse proxy
  │
  ▼
[FastAPI]  ──  JWT auth, Pydantic validation, structured logging
  │
  ▼
[MathService]  ──  Redis cache check → agent → persist → cache write
  │
  ▼
[LangGraph Agent]
  │
  ├── Router Node    → classifies problem, selects tools
  ├── Tools Node     → calculator / SymPy / Wikipedia (sandboxed)
  ├── Reasoner Node  → step-by-step solution
  ├── Verifier Node  → confidence score, re-routes if < 0.8
  └── Assembler Node → formats final response
  │
  ▼
[PostgreSQL]  ──  problems, solutions, users, sessions
[Redis]       ──  session cache, query cache, rate limit counters
[Celery]      ──  async OCR and long-running solve tasks
```

---

## Features

| Feature | Details |
|---|---|
| **Text solver** | Plain language or LaTeX input |
| **Image OCR** | Upload a photo → extract LaTeX → solve |
| **Symbolic math** | Integrals, derivatives, equations via SymPy |
| **Step-by-step** | Numbered explanation with LaTeX formatting |
| **Confidence scoring** | 0.0–1.0, auto-retries below threshold |
| **Session memory** | Multi-turn conversation stored in Redis |
| **Auth** | JWT access + refresh tokens |
| **Rate limiting** | Per-user sliding window (Redis-backed) |
| **Caching** | Identical queries return instantly from Redis |
| **Metrics** | Prometheus endpoint at `/api/v1/health/metrics` |
| **Async OCR** | Celery worker — doesn't block API requests |

---

## Quick Start (5 minutes)

**Prerequisites:** Docker Desktop installed and running.

```bash
# 1. Clone
git clone https://github.com/yourusername/mathbot.git
cd mathbot

# 2. Configure
cp .env.example .env
# Edit .env — add your GROQ_API_KEY (free at console.groq.com)

# 3. Start everything
docker compose up --build

# 4. Open the API docs
# http://localhost:8000/docs
```

Full Windows setup: see [SETUP.md](SETUP.md)

---

## API Reference

Interactive docs auto-generated at **http://localhost:8000/docs**

### Solve a problem
```http
POST /api/v1/solve
Authorization: Bearer <your_token>

{
  "query": "Integrate x^2 with respect to x",
  "show_steps": true
}
```

Response:
```json
{
  "answer": "x**3/3 + C",
  "latex_answer": "\\frac{x^3}{3} + C",
  "problem_type": "symbolic",
  "confidence": 0.93,
  "steps": [
    {"step_number": 1, "title": "Apply power rule", "explanation": "..."}
  ],
  "tools_used": ["sympy"],
  "latency_ms": 2340.5
}
```

### Extract LaTeX from image
```http
POST /api/v1/ocr/extract
Authorization: Bearer <your_token>
Content-Type: multipart/form-data

file: <your_image.png>
```

### Register
```http
POST /api/v1/auth/register
{"email": "you@example.com", "password": "yourpass", "username": "yourname"}
```

---

## Project Structure

```
mathbot/
├── api/            HTTP layer — routes, middleware, auth
├── agents/         LangGraph graph + nodes
├── services/       Business logic (MathService, OCRService)
├── tools/          Calculator, SymPy, Wikipedia (sandboxed)
├── workflows/      Celery async tasks
├── prompts/        All LLM prompts as versioned templates
├── repositories/   Database access layer
├── models/         SQLAlchemy ORM models
├── schemas/        Pydantic request/response schemas
├── database/       Connection + Alembic migrations
├── cache/          Redis client + key builders
├── core/           Config, logging, security, exceptions, metrics
└── tests/          Unit, integration, and E2E tests
```

---

## Running Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/ -v

# Run only unit tests (fast, no DB needed)
pytest tests/unit/ -v

# Run with coverage report
pytest tests/ --cov=. --cov-report=html
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI 0.111 |
| Agent | LangGraph 0.1 |
| LLM | Groq — Llama 3.3 70B |
| Symbolic math | SymPy |
| OCR | pix2tex + Tesseract |
| Database | PostgreSQL 15 |
| Cache / Queue | Redis 7 + Celery |
| Auth | JWT (python-jose) |
| Logging | structlog (JSON) |
| Metrics | Prometheus |
| Containers | Docker + Docker Compose |
| CI | GitHub Actions |

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes and add tests
4. Run `ruff check .` and `pytest tests/unit/ -v`
5. Open a pull request

---

## License

MIT — see [LICENSE](LICENSE)
