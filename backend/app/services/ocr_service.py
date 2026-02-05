"""
Receipt Scanner Service using Google Gemini Flash Vision.

This service handles receipt image processing and extraction of
structured data (items, prices, dates) using AI vision capabilities.
"""

import json
import re
from typing import Optional

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from fastapi import HTTPException, status

from ..core.config import settings


class ReceiptScanner:
    """
    Receipt scanner using Google Gemini Flash Vision model.

    Extracts structured data from receipt images including:
    - Purchased items and their prices
    - Transaction date
    - Total amount
    - Category guesses for each item
    """

    SYSTEM_PROMPT = """Analyze this shopping receipt image. Extract every purchased item, its price, and the date.
Return strictly a JSON object with no additional text. Attempt to guess the category based on the item name.

Expected format:
{
  "date": "YYYY-MM-DD",
  "total_amount": 100000,
  "items": [
    {"name": "Item Name", "price": 3500, "category_guess": "Food"},
    {"name": "Another Item", "price": 5000, "category_guess": "Hygiene"}
  ]
}

Rules:
- Date should be in YYYY-MM-DD format. If unclear, use null.
- Prices should be numeric (no currency symbols).
- total_amount is the final total on the receipt.
- category_guess should be one of: Food, Transport, Shopping, Entertainment, Bills, Health, Hygiene, Education, Other.
- If an item cannot be read clearly, make a best guess or skip it.
- Return ONLY valid JSON, no markdown formatting."""

    def __init__(self):
        """Initialize the Gemini model with API key configuration."""
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    def _parse_json_response(self, response_text: str) -> dict:
        """
        Parse JSON from AI response, handling markdown code blocks.

        The AI sometimes wraps JSON in ```json ... ``` blocks.
        This method strips those before parsing.
        """
        # Remove markdown code blocks if present
        cleaned = response_text.strip()

        # Handle ```json ... ``` format
        if cleaned.startswith("```"):
            # Remove opening ``` with optional language specifier
            cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned)
            # Remove closing ```
            cleaned = re.sub(r"\n?```$", "", cleaned)

        # Handle ``` without json specifier
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to parse AI response as JSON: {str(e)}",
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

            # Generate content with the image
            response = self.model.generate_content(
                [self.SYSTEM_PROMPT, image_part],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Low temperature for consistent output
                    max_output_tokens=2048,
                ),
            )

            # Check if response was blocked
            if not response.text:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="AI could not process the image. The image may be unreadable or blocked.",
                )

            # Parse the JSON response
            return self._parse_json_response(response.text)

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
