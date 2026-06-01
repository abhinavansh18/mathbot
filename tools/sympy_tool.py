"""
SymPy Tool — solves symbolic math problems (integrals, derivatives, equations).
Runs inside the sandbox to prevent any code injection.
"""
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from core.config import settings
from core.logging import get_logger
from tools.sandbox import execute_sandboxed

log = get_logger(__name__)

# System prompt that turns natural language into SymPy code
_SYMPY_CODEGEN_SYSTEM = """You are a SymPy code generator.
Given a math problem, output ONLY valid Python code using sympy (imported as `sp`).
Rules:
- Store the final answer in a variable named `result`
- Include +C for indefinite integrals: result = str(sp.integrate(...)) + " + C"
- Never use print()
- Never import anything other than sympy
- Output raw Python only — no markdown, no explanation
"""


async def run_sympy(query: str) -> str:
    """
    1. Ask the LLM to generate SymPy code for the query.
    2. Execute that code in the sandbox.
    3. Return the string result.
    """
    # Step 1: generate code
    llm = ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=settings.LLM_MODEL,
        temperature=0.0,
        max_tokens=512,
    )
    messages = [
        SystemMessage(content=_SYMPY_CODEGEN_SYSTEM),
        HumanMessage(content=f"Problem: {query}\n\nWrite SymPy code:"),
    ]
    response = await llm.ainvoke(messages)
    code = response.content.strip()

    # Strip markdown fences if the LLM adds them anyway
    if code.startswith("```"):
        code = "\n".join(
            line for line in code.splitlines()
            if not line.startswith("```")
        )

    log.info("tool.sympy.code_generated", code_length=len(code))

    # Step 2: execute in sandbox
    sandbox_result = await execute_sandboxed(code)
    if sandbox_result.success and sandbox_result.result is not None:
        log.info("tool.sympy.success")
        return str(sandbox_result.result)
    else:
        error = sandbox_result.error or "SymPy execution failed"
        log.warning("tool.sympy.failed", error=error)
        return f"SymPy error: {error}"
