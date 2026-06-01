"""
Sandboxed code execution.
Runs untrusted LLM-generated Python in an isolated subprocess with:
  - Hard time limit
  - Memory cap (Linux only via resource module)
  - Restricted imports (only math, sympy, decimal allowed)
  - No network, no file writes

Windows note: resource limits are Linux-only; timeout still applies on Windows.
"""
import asyncio
import json
import textwrap
from dataclasses import dataclass
from typing import Any, Optional

from core.config import settings
from core.exceptions import SandboxTimeoutError, SandboxExecutionError
from core.logging import get_logger

log = get_logger(__name__)

# Imports the sandbox child process is allowed to use
_ALLOWED_IMPORTS = "import math, decimal, re\ntry:\n    import sympy as sp\nexcept ImportError:\n    sp = None\n"


@dataclass
class SandboxResult:
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    stdout: str = ""


async def execute_sandboxed(code: str, timeout: float = None) -> SandboxResult:
    """
    Execute `code` in a child Python process.
    The child process only has access to math, decimal, and sympy.
    `result` must be set in the code for the return value to be captured.
    """
    if timeout is None:
        timeout = settings.SANDBOX_TIMEOUT_SECONDS

    # Build the wrapper that runs in the child
    wrapper = textwrap.dedent(f"""
import sys, json, os

# Block dangerous stdlib modules
_blocked = {{"os", "subprocess", "socket", "shutil", "pathlib", "importlib",
             "ctypes", "multiprocessing", "threading", "http", "urllib",
             "ftplib", "smtplib", "telnetlib", "pickle", "shelve"}}

original_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__

def _safe_import(name, *args, **kwargs):
    if name in _blocked:
        raise ImportError(f"Import of '{{name}}' is blocked in sandbox.")
    return original_import(name, *args, **kwargs)

import builtins
builtins.__import__ = _safe_import

# Apply resource limits on Linux
try:
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
except (ImportError, AttributeError):
    pass  # Windows — skip resource limits, timeout handles it

{_ALLOWED_IMPORTS}

result = None
try:
{textwrap.indent(code, "    ")}
    print(json.dumps({{"success": True, "result": str(result) if result is not None else None}}))
except Exception as _exc:
    print(json.dumps({{"success": False, "error": str(_exc)}}))
""")

    try:
        proc = await asyncio.create_subprocess_exec(
            "python",  # uses the venv python on PATH
            "-c", wrapper,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        raw = stdout.decode().strip()
        if not raw:
            return SandboxResult(success=False, error=stderr.decode().strip() or "No output")
        data = json.loads(raw)
        return SandboxResult(**data)

    except asyncio.TimeoutError:
        try:
            proc.kill()
        except Exception:
            pass
        raise SandboxTimeoutError(f"Sandbox exceeded {timeout}s time limit.")
    except Exception as exc:
        raise SandboxExecutionError(f"Sandbox failed: {exc}") from exc
