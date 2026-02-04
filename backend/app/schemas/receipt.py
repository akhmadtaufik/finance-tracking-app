"""
Pydantic schemas for receipt scanning feature.
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Literal
from datetime import date
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
        None, description="Transaction date from receipt", serialization_alias="date"
    )
    total_amount: Optional[Decimal] = Field(
        None, ge=0, description="Total amount on receipt"
    )
    items: List[ReceiptItem] = Field(
        default_factory=list, description="List of items extracted"
    )


class ReceiptScanError(BaseModel):
    """Schema for error responses."""

    detail: str = Field(..., description="Error message")
