"""
Receipt Scanner Service using Google Gemini Flash Vision.

This service handles receipt image processing and extraction of
structured data (items, prices, dates) using AI vision capabilities.

Uses Gemini's native Structured Outputs (response_schema) to guarantee
100% valid JSON and lock the response keys, eliminating JSONDecodeError
and schema hallucination issues.
"""

import json

import typing_extensions as typing

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from fastapi import HTTPException, status

from ..core.config import settings


# ──────────────────────────────────────────────
#  Structured Output Schemas (TypedDict)
# ──────────────────────────────────────────────


class ReceiptItem(typing.TypedDict):
    """Schema for a single receipt line-item."""

    name: str
    price: int
    category_guess: str


class ExpectedReceipt(typing.TypedDict):
    """Top-level schema enforced on every Gemini response."""

    date: str
    total_amount: int
    items: list[ReceiptItem]


class ReceiptScanner:
    """
    Receipt scanner using Google Gemini Flash Vision model.

    Extracts structured data from receipt images including:
    - Purchased items and their prices
    - Transaction date
    - Total amount
    - Category guesses for each item

    Uses `response_schema` to enforce output shape at the API level,
    preventing prompt drift and JSON formatting errors.
    """

    SYSTEM_PROMPT = """Analyze this shopping receipt image. Extract every purchased item, its final price, and the transaction date.
    Attempt to guess the category based on the item name.
Rules:
- Date should be in YYYY-MM-DD format.
- Indonesian receipts commonly print dates as DD-MM-YY (e.g. 23-02-26 means 23 Feb 2026, NOT 2023-02-26). Always interpret two-digit years as 20XX. When ambiguous, prefer DD-MM-YY over YY-MM-DD.
- Prices should be strictly numeric.
- Category must be one of: Food, Transport, Shopping, Entertainment, Bills, Health, Hygiene, Education, Other."""

    def __init__(self):
        """Initialize the Gemini model with API key configuration."""
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    def _parse_json_response(self, response_text: str) -> dict:
        """
        Parse JSON from AI response.

        With response_mime_type="application/json" the model is guaranteed
        to return a valid JSON string (no markdown fences), so this parser
        is intentionally minimal.
        """
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to parse AI response as JSON: {str(e)}\nRaw: {response_text}",
            )

    async def scan_image(
        self, image_bytes: bytes, mime_type: str = "image/jpeg"
    ) -> dict:
        """
        Scan a receipt image and extract structured data.

        Args:
            image_bytes: Raw bytes of the receipt image.
            mime_type: MIME type of the image (default: image/jpeg).

        Returns:
            dict: Parsed receipt data with date, total_amount, and items.

        Raises:
            HTTPException: 429 if quota exceeded, 500 for other errors.
        """
        try:
            # Create image part for the model
            image_part = {"mime_type": mime_type, "data": image_bytes}

            # Generate content with structured output enforcement
            response = self.model.generate_content(
                [self.SYSTEM_PROMPT, image_part],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Low temperature for consistent output
                    response_mime_type="application/json",
                    response_schema=ExpectedReceipt,
                ),
            )

            # Check if response was blocked
            if not response.text:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="AI could not process the image. The image may be unreadable or blocked.",
                )

            # Parse the JSON response
            extracted_data = self._parse_json_response(response.text)

            # Post-process items to Title Case
            if "items" in extracted_data:
                for item in extracted_data["items"]:
                    if "name" in item and isinstance(item["name"], str):
                        item["name"] = item["name"].title()

            return extracted_data

        except google_exceptions.ResourceExhausted:
            # Free tier quota exceeded
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Daily AI Quota Exceeded. Please input transaction manually.",
            )
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            # Handle all other errors (blurry images, API issues, etc.)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI Processing Failed: {str(e)}",
            )


# Singleton instance for dependency injection
receipt_scanner = ReceiptScanner()


def get_receipt_scanner() -> ReceiptScanner:
    """Dependency injection function for ReceiptScanner."""
    return receipt_scanner
