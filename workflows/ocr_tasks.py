"""
Celery tasks for OCR processing.
Offloads the heavy pix2tex model inference from FastAPI request threads.
"""
import io
import base64
from celery import shared_task
from PIL import Image

from workflows.celery_app import celery_app
from core.logging import get_logger

log = get_logger(__name__)


@celery_app.task(
    name="ocr.extract_latex",
    bind=True,
    max_retries=2,
    default_retry_delay=3,
)
def extract_latex_task(self, image_b64: str) -> dict:
    """
    Accepts a base64-encoded image string, runs OCR, returns result dict.
    Called as: extract_latex_task.delay(base64.b64encode(image_bytes).decode())
    """
    try:
        image_bytes = base64.b64decode(image_b64)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        from pix2tex.cli import LatexOCR
        model = LatexOCR()
        latex = model(image)

        log.info("ocr_task.completed", latex_length=len(latex))
        return {"success": True, "latex": latex, "confidence": 0.85}

    except Exception as exc:
        log.error("ocr_task.failed", error=str(exc))
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            return {"success": False, "error": str(exc), "latex": "", "confidence": 0.0}
