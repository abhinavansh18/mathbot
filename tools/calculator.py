"""
Calculator Tool — executes arithmetic expressions inside the sandbox.
"""
from tools.sandbox import execute_sandboxed
from core.logging import get_logger

log = get_logger(__name__)


async def run_calculator(query: str) -> str:
    """
    Extracts a numeric expression from the query and evaluates it safely.
    The LLM's router node decides when to call this.
    """
    # The code below is sent to the sandbox — `result` is the variable it must set.
    code = f"""
import math
# Evaluate the numeric expression extracted from: {repr(query)}
# Try to parse a simple expression; the LLM should have reduced to numbers already.
expression = {repr(query)}
# Attempt eval with math context
result = eval(expression, {{"__builtins__": {{}}}}, vars(math))
"""
    sandbox_result = await execute_sandboxed(code)
    if sandbox_result.success and sandbox_result.result is not None:
        log.info("tool.calculator.success", query=query[:60])
        return str(sandbox_result.result)
    else:
        error = sandbox_result.error or "Unknown calculation error"
        log.warning("tool.calculator.failed", error=error)
        return f"Calculator error: {error}"
