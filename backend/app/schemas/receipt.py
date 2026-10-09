"""
Pydantic schemas for receipt scanning feature.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import List, Optional, Literal
from datetime import date, datetime
from decimal import Decimal


CATEGORY_TYPES = Literal[
    "Food",
    "Transport",
    "Shopping",
    "Entertainment",
    "Bills",
    "Health",
    "Hygiene",
    "Education",
    "Other",
]


class ReceiptItem(BaseModel):
    """Schema for a single item extracted from a receipt."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Indomie Goreng",
                "price": 3500,
                "category_guess": "Food",
            }
        }
    )

    name: str = Field(..., description="Name of the item")
    price: Decimal = Field(..., ge=0, description="Price of the item")
    category_guess: Optional[str] = Field(
        None, description="AI-guessed category for the item"
    )


class ReceiptScanResponse(BaseModel):
    """Schema for the complete receipt scan response."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "date": "2024-12-01",
                "total_amount": 100000,
                "items": [
                    {"name": "Indomie Goreng", "price": 3500, "category_guess": "Food"},
                    {
                        "name": "Sabun Lifebuoy",
                        "price": 5000,
                        "category_guess": "Hygiene",
                    },
                ],
            }
        }
    )

    receipt_date: Optional[date] = Field(
        default_factory=date.today,
        description="Transaction date from receipt",
        serialization_alias="date",
    )
    total_amount: Optional[Decimal] = Field(
        None, ge=0, description="Total amount on receipt"
    )
    items: List[ReceiptItem] = Field(
        default_factory=list, description="List of items extracted"
    )

    @field_validator("receipt_date", mode="before")
    @classmethod
    def parse_and_default_receipt_date(cls, v):
        """
        Parse receipt date from AI or fallback to today's date if empty/unparseable.
        """
        if not v or (isinstance(v, str) and not v.strip()):
            return date.today()
        if isinstance(v, date):
            return v
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, str):
            cleaned = v.strip()
            # Try ISO format (YYYY-MM-DD)
            try:
                return date.fromisoformat(cleaned)
            except ValueError:
                pass
            # Try common Indonesian / receipt date formats
            for fmt in (
                "%d-%m-%Y",
                "%d/%m/%Y",
                "%d-%m-%y",
                "%d/%m/%y",
                "%Y/%m/%d",
                "%d %b %Y",
                "%d %B %Y",
            ):
                try:
                    return datetime.strptime(cleaned, fmt).date()
                except ValueError:
                    pass
            # If all parsing fails, fallback to today's date
            return date.today()
        return date.today()

    @field_validator("total_amount", mode="before")
    @classmethod
    def parse_total_amount(cls, v):
        """Sanitize total amount if returned as string, formatted with commas, or empty."""
        if v is None or v == "":
            return None
        if isinstance(v, (int, float, Decimal)):
            return Decimal(str(v))
        if isinstance(v, str):
            cleaned = v.strip().replace(",", "").replace(".", "") if v.strip().count(".") > 1 else v.strip().replace(",", "")
            try:
                return Decimal(cleaned)
            except Exception:
                return None
        return None


class ReceiptScanError(BaseModel):
    """Schema for structured receipt scanning error responses."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "Foto struk tidak terbaca atau terlalu buram.",
                "code": "AI_IMAGE_UNREADABLE",
                "request_id": "c9bf8f8a-4d2c-4ef7-b52b-7b3c2e17621f",
                "retryable": False,
                "action_hint": "retake_photo",
            }
        }
    )

    detail: str = Field(..., description="Human-readable error message")
    code: str = Field(..., description="Machine-readable error code")
    request_id: Optional[str] = Field(
        None, description="Request correlation ID for log tracing"
    )
    retryable: bool = Field(
        False, description="Whether client should attempt automatic/manual retry"
    )
    action_hint: Optional[str] = Field(
        None, description="Suggested action for client UI (e.g. retake_photo, manual_input)"
    )
