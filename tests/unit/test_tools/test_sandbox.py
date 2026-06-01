"""
Unit tests for the sandboxed code executor.
These tests verify the security boundaries of the sandbox.
"""
import pytest
from tools.sandbox import execute_sandboxed
from core.exceptions import SandboxTimeoutError


@pytest.mark.asyncio
async def test_sandbox_simple_arithmetic():
    result = await execute_sandboxed("result = 2 + 2")
    assert result.success is True
    assert result.result == "4"


@pytest.mark.asyncio
async def test_sandbox_math_module():
    result = await execute_sandboxed("result = math.sqrt(16)")
    assert result.success is True
    assert result.result == "4.0"


@pytest.mark.asyncio
async def test_sandbox_sympy_integration():
    code = """
import sympy as sp
x = sp.Symbol('x')
result = sp.integrate(x**2, x)
"""
    result = await execute_sandboxed(code)
    assert result.success is True
    assert "x**3" in result.result or "x³" in result.result


@pytest.mark.asyncio
async def test_sandbox_blocks_os_import():
    result = await execute_sandboxed("import os; result = os.getcwd()")
    assert result.success is False
    assert result.error is not None


@pytest.mark.asyncio
async def test_sandbox_blocks_subprocess():
    result = await execute_sandboxed("import subprocess; result = subprocess.check_output('dir')")
    assert result.success is False


@pytest.mark.asyncio
async def test_sandbox_timeout():
    with pytest.raises(SandboxTimeoutError):
        await execute_sandboxed(
            "import time; time.sleep(999)",
            timeout=1.0,
        )


@pytest.mark.asyncio
async def test_sandbox_syntax_error():
    result = await execute_sandboxed("result = (((")
    assert result.success is False
    assert result.error is not None


@pytest.mark.asyncio
async def test_sandbox_division_by_zero():
    result = await execute_sandboxed("result = 1 / 0")
    assert result.success is False
    assert "division by zero" in (result.error or "").lower()


@pytest.mark.asyncio
async def test_sandbox_result_none_when_not_set():
    result = await execute_sandboxed("x = 5  # result not set")
    assert result.success is True
    assert result.result is None
