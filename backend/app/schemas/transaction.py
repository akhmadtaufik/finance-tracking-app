from pydantic import BaseModel, ConfigDict
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Literal


class TransactionCreate(BaseModel):
    """Schema for creating a new transaction."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "wallet_id": 1,
            "category_id": 5,
            "amount": 150000.00,
            "type": "EXPENSE",
            "transaction_date": "2024-12-01",
            "description": "Makan Siang di Warung Padang"
        }
    })
    
    wallet_id: int
    category_id: int
    amount: Decimal
    type: Literal["INCOME", "EXPENSE"]
    transaction_date: Optional[date] = None
    description: Optional[str] = None


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
