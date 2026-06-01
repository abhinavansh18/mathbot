"""
Pydantic schemas for the /ocr endpoint.
"""
from typing import Optional
from pydantic import BaseModel, Field


class OCRResponse(BaseModel):
    latex: str = Field(..., description="Extracted LaTeX expression.")
    confidence: float = Field(..., ge=0.0, le=1.0)
    requires_user_confirmation: bool = Field(
        ...,
        description="True when confidence is below the threshold — prompt the user to review.",
    )
    raw_text: Optional[str] = Field(None, description="Plain-text fallback from Tesseract.")


class OCRSolveRequest(BaseModel):
    latex: str = Field(..., description="LaTeX string (possibly edited by the user after OCR).")
    session_id: Optional[str] = None
    show_steps: bool = True
