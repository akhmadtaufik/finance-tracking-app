import re
from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Literal

# XSS Prevention Pattern
XSS_PATTERN = re.compile(r'<script|javascript:|on\w+\s*=', re.IGNORECASE)


class TransactionCreate(BaseModel):
    """Schema for creating a new transaction with strict validation."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "wallet_id": 1,
                "category_id": 5,
                "amount": 150000.00,
                "type": "EXPENSE",
                "transaction_date": "2024-12-01",
                "description": "Makan Siang di Warung Padang"
            }
        }
    )
    
    wallet_id: int = Field(..., gt=0, description="ID of the wallet")
    category_id: int = Field(..., gt=0, description="ID of the category")
    amount: Decimal = Field(..., gt=0, max_digits=15, decimal_places=2, description="Amount (must be positive)")
    type: Literal["INCOME", "EXPENSE"]
    transaction_date: Optional[date] = None
    description: Optional[str] = Field(None, max_length=500)
    
    @field_validator('description')
    @classmethod
    def sanitize_description(cls, v: Optional[str]) -> Optional[str]:
        """Prevent XSS by rejecting script tags."""
        if v and XSS_PATTERN.search(v):
            raise ValueError('HTML/Script tags are not allowed in description')
        return v


class TransactionResponse(BaseModel):
    """Schema for transaction response with category and wallet names."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": 1,
            "user_id": 1,
            "wallet_id": 1,
            "category_id": 5,
            "amount": 150000.00,
            "type": "EXPENSE",
            "transaction_date": "2024-12-01",
            "description": "Makan Siang di Warung Padang",
            "created_at": "2024-12-01T12:30:00",
            "category_name": "Food & Dining",
            "wallet_name": "Bank BCA"
        }
    })
    
    id: int
    user_id: int
    wallet_id: int
    category_id: int
    amount: Decimal
    type: str
    transaction_date: date
    description: Optional[str]
    created_at: datetime
    category_name: Optional[str] = None
    wallet_name: Optional[str] = None
