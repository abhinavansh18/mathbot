"""
/api/v1/ocr — upload an image, get extracted LaTeX back.
"""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from api.middleware.auth import get_current_user
from core.exceptions import ImageTooLargeError, OCRExtractionError
from schemas.ocr import OCRResponse
from services.ocr_service import OCRService

router = APIRouter()
_ocr_service = OCRService()   # singleton — lazy-loads the model on first call


@router.post(
    "/extract",
    response_model=OCRResponse,
    summary="Extract LaTeX from an image",
    description="Upload a PNG/JPG image of a math problem. Returns LaTeX and a confidence score.",
)
async def extract_latex(
    file: UploadFile = File(..., description="Image file (PNG, JPG, JPEG, WEBP)"),
    user_id: str = Depends(get_current_user),
) -> OCRResponse:
    content = await file.read()
    content_type = file.content_type or "application/octet-stream"

    try:
        image = await _ocr_service.validate_image(content, content_type)
        result = await _ocr_service.extract_latex(image)
    except ImageTooLargeError as exc:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc))
    except OCRExtractionError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    return OCRResponse(
        latex=result.latex,
        confidence=result.confidence,
        requires_user_confirmation=result.requires_user_confirmation,
        raw_text=result.raw_text,
    )
