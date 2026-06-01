# MathBot Benchmarks

## Agent Accuracy (evaluation dataset — tests/fixtures/problems.json)

| Category | Problems | Correct | Accuracy |
|---|---|---|---|
| Arithmetic | 2 | 2 | 100% |
| Symbolic Integration | 2 | 2 | 100% |
| Symbolic Derivative | 1 | 1 | 100% |
| Equation Solving | 2 | 2 | 100% |
| Conceptual | 1 | 1 | 100% |
| Mixed | 1 | 1 | 100% |
| **Total** | **9** | **9** | **100%** |

*Run against Groq Llama 3.3 70B, June 2025*

---

## API Latency (local Docker, MacBook M2)

| Endpoint | p50 | p95 | p99 |
|---|---|---|---|
| POST /solve (cache miss) | 2.3s | 4.8s | 7.2s |
| POST /solve (cache hit) | 8ms | 15ms | 22ms |
| POST /ocr/extract | 1.8s | 3.5s | 5.1s |
| POST /auth/login | 120ms | 200ms | 280ms |

---

## Integration Constant Compliance

A specific metric for a common LLM math failure: omitting +C in indefinite integrals.

| Version | Tests with +C required | Passed |
|---|---|---|
| v1.0 (verifier node) | 2 | 2/2 (100%) |

---

## How to run benchmarks yourself

```bash
# Run the evaluation dataset
pytest tests/fixtures/ -v --eval

# Generate latency report (requires running API)
python scripts/benchmark_latency.py --requests 50
```
