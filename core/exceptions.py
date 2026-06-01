"""
Domain exception hierarchy.
Raise these from services; the API layer maps them to HTTP status codes.
"""


class MathBotError(Exception):
    """Base for all application errors."""
    pass


# ── Auth ─────────────────────────────────────────────────────────────────────
class AuthenticationError(MathBotError):
    """Invalid or missing credentials."""
    pass


class TokenExpiredError(AuthenticationError):
    """JWT token has expired."""
    pass


# ── Rate Limiting ─────────────────────────────────────────────────────────────
class RateLimitExceededError(MathBotError):
    """User has exceeded their request quota."""
    pass


# ── Validation ───────────────────────────────────────────────────────────────
class ValidationError(MathBotError):
    """Input data failed validation."""
    pass


class ImageTooLargeError(ValidationError):
    """Uploaded image exceeds the size limit."""
    pass


class UnsupportedFileTypeError(ValidationError):
    """Uploaded file type is not supported."""
    pass


# ── OCR ──────────────────────────────────────────────────────────────────────
class OCRExtractionError(MathBotError):
    """LaTeX could not be extracted from image."""
    pass


class LowConfidenceOCRError(OCRExtractionError):
    """OCR result confidence is below threshold."""
    def __init__(self, confidence: float):
        self.confidence = confidence
        super().__init__(f"OCR confidence too low: {confidence:.2f}")


# ── Agent ────────────────────────────────────────────────────────────────────
class AgentTimeoutError(MathBotError):
    """Agent exceeded maximum execution time."""
    pass


class AgentMaxIterationsError(MathBotError):
    """Agent exceeded maximum iteration count."""
    pass


class SandboxExecutionError(MathBotError):
    """Code execution in sandbox failed."""
    pass


class SandboxTimeoutError(SandboxExecutionError):
    """Sandboxed code exceeded time limit."""
    pass


# ── LLM ──────────────────────────────────────────────────────────────────────
class LLMError(MathBotError):
    """Generic LLM API error."""
    pass


class LLMRateLimitError(LLMError):
    """LLM provider rate limit hit."""
    pass


# ── Persistence ──────────────────────────────────────────────────────────────
class NotFoundError(MathBotError):
    """Requested resource does not exist."""
    def __init__(self, resource: str, resource_id: str):
        super().__init__(f"{resource} '{resource_id}' not found.")
