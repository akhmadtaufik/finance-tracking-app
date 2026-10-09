"""
Receipts Router - Receipt scanning endpoints using AI vision.
"""

from datetime import date
from fastapi import APIRouter, Depends, UploadFile, File, status
import magic
from pydantic import ValidationError

from ..core.security import get_current_user
from ..services.ocr_service import ReceiptScanner, ReceiptScanException, get_receipt_scanner
from ..schemas.receipt import ReceiptScanResponse, ReceiptItem, ReceiptScanError


router = APIRouter(prefix="/receipts", tags=["Receipts"])

# Allowed image MIME types
ALLOWED_MIME_TYPES = {
    "image/jpeg": "image/jpeg",
    "image/jpg": "image/jpeg",
    "image/png": "image/png",
    "image/webp": "image/webp",
}


@router.post(
    "/scan",
    response_model=ReceiptScanResponse,
    status_code=status.HTTP_200_OK,
    summary="Scan a receipt image",
    description="""
    Upload a receipt image to extract structured data using AI vision.
    
    **Supported formats:** JPEG, PNG, WebP
    
    **Returns:** Date, total amount, and list of items with prices and category guesses.
    
    **Error Codes:**
    - EMPTY_FILE (400): Empty file uploaded
    - INVALID_FILE_TYPE (400): Unsupported MIME extension
    - FILE_TOO_LARGE (413): File size exceeds 5MB
    - INVALID_MAGIC_BYTES (415): File content is not a real image
    - AI_QUOTA_EXCEEDED (429): Daily Gemini API quota exhausted
    - AI_IMAGE_UNREADABLE (422): Image unreadable or blocked by safety filter
    - AI_TIMEOUT (504): Gemini inference timed out
    - AI_SERVICE_UNAVAILABLE (503): Gemini service unreachable
    - AI_AUTH_FAILED (500): AI service credentials issue
    - AI_PROCESSING_ERROR (500): Technical processing error
    """,
    responses={
        200: {"description": "Receipt scanned successfully", "model": ReceiptScanResponse},
        400: {"description": "Bad Request (Empty file / Invalid type)", "model": ReceiptScanError},
        413: {"description": "Payload Too Large (Exceeds 5MB)", "model": ReceiptScanError},
        415: {"description": "Unsupported Media Type (Invalid Magic Bytes)", "model": ReceiptScanError},
        422: {"description": "Unprocessable Image (Unreadable / Blurry)", "model": ReceiptScanError},
        429: {"description": "Daily AI Quota Exceeded", "model": ReceiptScanError},
        500: {"description": "Internal AI Processing Failed", "model": ReceiptScanError},
        503: {"description": "AI Service Unavailable", "model": ReceiptScanError},
        504: {"description": "AI Gateway Timeout", "model": ReceiptScanError},
    },
)
async def scan_receipt(
    file: UploadFile = File(..., description="Receipt image file (JPEG, PNG, WebP)"),
    current_user: dict = Depends(get_current_user),
    scanner: ReceiptScanner = Depends(get_receipt_scanner),
) -> ReceiptScanResponse:
    """
    Scan a receipt image and extract structured data.

    Uses Google Gemini Flash Vision to:
    - Extract item names and prices
    - Detect transaction date
    - Calculate total amount
    - Guess categories for each item
    """
    if file.size and file.size > 5 * 1024 * 1024:
        raise ReceiptScanException(
            message="Ukuran file melebihi batas 5MB",
            code="FILE_TOO_LARGE",
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            retryable=False,
            action_hint="retake_photo",
        )

    # Validate file type using extensions
    content_type = file.content_type or ""
    if content_type not in ALLOWED_MIME_TYPES:
        raise ReceiptScanException(
            message=f"Tipe file '{content_type}' tidak didukung. Harap gunakan JPEG, PNG, atau WebP",
            code="INVALID_FILE_TYPE",
            status_code=status.HTTP_400_BAD_REQUEST,
            retryable=False,
            action_hint="retake_photo",
        )

    # Read file bytes
    image_bytes = await file.read()

    if not image_bytes:
        raise ReceiptScanException(
            message="File struk kosong",
            code="EMPTY_FILE",
            status_code=status.HTTP_400_BAD_REQUEST,
            retryable=False,
            action_hint="retake_photo",
        )

    # Pre-check file size from read bytes in case file.size was None
    if len(image_bytes) > 5 * 1024 * 1024:
        raise ReceiptScanException(
            message="Ukuran file melebihi batas 5MB",
            code="FILE_TOO_LARGE",
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            retryable=False,
            action_hint="retake_photo",
        )

    # Magic bytes validation
    actual_mime = magic.from_buffer(image_bytes, mime=True)
    if actual_mime not in ALLOWED_MIME_TYPES:
        raise ReceiptScanException(
            message=f"Tanda tangan file tidak valid ({actual_mime}). Harap unggah gambar asli",
            code="INVALID_MAGIC_BYTES",
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            retryable=False,
            action_hint="retake_photo",
        )

    # Get the correct MIME type for Gemini
    mime_type = ALLOWED_MIME_TYPES[content_type]

    # Scan the receipt
    user_id = str(current_user.get("id")) if current_user else None
    result = await scanner.scan_image(image_bytes, mime_type, user_id=user_id)

    # Map result to response model
    raw_date = result.get("date")
    cleaned_date = raw_date if (raw_date and str(raw_date).strip()) else date.today()

    try:
        items = [
            ReceiptItem(
                name=item.get("name", "Unknown"),
                price=item.get("price", 0),
                category_guess=item.get("category_guess"),
            )
            for item in result.get("items", [])
        ]

        return ReceiptScanResponse(
            receipt_date=cleaned_date,
            total_amount=result.get("total_amount"),
            items=items,
        )
    except ValidationError as err:
        raise ReceiptScanException(
            message="Format data hasil scan tidak valid atau gagal diproses.",
            code="AI_INVALID_STRUCTURE",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            retryable=True,
            action_hint="retry",
        ) from err

