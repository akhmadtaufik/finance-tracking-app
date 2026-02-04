"""
Receipts Router - Receipt scanning endpoints using AI vision.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status

from ..core.security import get_current_user
from ..services.ocr_service import ReceiptScanner, get_receipt_scanner
from ..schemas.receipt import ReceiptScanResponse, ReceiptItem

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
    - 400: Invalid file type
    - 429: Daily AI quota exceeded (use manual input)
    - 500: AI processing failed
    """,
    responses={
        200: {"description": "Receipt scanned successfully"},
        400: {"description": "Invalid file type"},
        429: {"description": "Daily AI Quota Exceeded"},
        500: {"description": "AI Processing Failed"},
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
    # Validate file type
    content_type = file.content_type or ""
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type: {content_type}. Allowed: JPEG, PNG, WebP",
        )

    # Read file bytes
    image_bytes = await file.read()

    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file uploaded"
        )

    # Get the correct MIME type for Gemini
    mime_type = ALLOWED_MIME_TYPES[content_type]

    # Scan the receipt
    result = await scanner.scan_image(image_bytes, mime_type)

    # Map result to response model
    items = [
        ReceiptItem(
            name=item.get("name", "Unknown"),
            price=item.get("price", 0),
            category_guess=item.get("category_guess"),
        )
        for item in result.get("items", [])
    ]

    return ReceiptScanResponse(
        receipt_date=result.get("date"),
        total_amount=result.get("total_amount"),
        items=items,
    )
