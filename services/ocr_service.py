"""
OCRService — validates uploaded images and extracts LaTeX.
Uses pix2tex as the primary extractor with Tesseract as a plain-text fallback.
"""
import asyncio
import io
from dataclasses import dataclass
from typing import Optional

from PIL import Image

from core.config import settings
from core.exceptions import ImageTooLargeError, OCRExtractionError, LowConfidenceOCRError
from core.logging import get_logger
from core.metrics import ocr_requests_total, ocr_confidence_score

log = get_logger(__name__)

ALLOWED_MIME_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}


@dataclass
class OCRResult:
    latex: str
    confidence: float
    raw_text: Optional[str]
    requires_user_confirmation: bool


class OCRService:
    def __init__(self):
        self._latex_model = None   # lazy-loaded — model is ~500MB

    def _get_latex_model(self):
        if self._latex_model is None:
            from pix2tex.cli import LatexOCR
            self._latex_model = LatexOCR()
        return self._latex_model

    async def validate_image(self, content: bytes, content_type: str) -> Image.Image:
        """Validates file size and type, returns a PIL Image."""
        max_bytes = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise ImageTooLargeError(
                f"Image exceeds {settings.MAX_IMAGE_SIZE_MB}MB limit."
            )
        try:
            image = Image.open(io.BytesIO(content))
            image.verify()                          # checks file integrity
            image = Image.open(io.BytesIO(content)) # re-open after verify
            return image.convert("RGB")
        except Exception as exc:
            raise OCRExtractionError(f"Cannot open image: {exc}") from exc

    async def extract_latex(self, image: Image.Image) -> OCRResult:
        """
        Runs pix2tex and Tesseract concurrently.
        Returns an OCRResult with a confidence score.
        """
        latex_result, tesseract_result = await asyncio.gather(
            self._run_pix2tex(image),
            self._run_tesseract(image),
            return_exceptions=True,
        )

        latex = None
        raw_text = None
        confidence = 0.0

        if isinstance(latex_result, str) and latex_result.strip():
            latex = latex_result.strip()
            confidence = 0.85   # pix2tex succeeded

        if isinstance(tesseract_result, str) and tesseract_result.strip():
            raw_text = tesseract_result.strip()
            if not latex:
                # Fall back to tesseract plain text
                latex = raw_text
                confidence = 0.55

        if not latex:
            ocr_requests_total.labels(status="failed").inc()
            raise OCRExtractionError("No text could be extracted from the image.")

        requires_confirmation = confidence < settings.OCR_CONFIDENCE_THRESHOLD
        ocr_confidence_score.observe(confidence)
        ocr_requests_total.labels(status="success").inc()

        log.info("ocr.extracted", confidence=confidence, requires_confirm=requires_confirmation)

        return OCRResult(
            latex=latex,
            confidence=confidence,
            raw_text=raw_text,
            requires_user_confirmation=requires_confirmation,
        )

    async def _run_pix2tex(self, image: Image.Image) -> str:
        """Runs pix2tex in a thread pool to avoid blocking the event loop."""
        loop = asyncio.get_event_loop()
        model = self._get_latex_model()
        return await loop.run_in_executor(None, model, image)

    async def _run_tesseract(self, image: Image.Image) -> str:
        """Runs Tesseract OCR as fallback."""
        try:
            import pytesseract
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, pytesseract.image_to_string, image)
        except Exception as exc:
            log.warning("ocr.tesseract_failed", error=str(exc))
            return ""
