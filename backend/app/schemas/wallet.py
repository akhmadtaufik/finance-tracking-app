from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from decimal import Decimal
from typing import Optional


class WalletCreate(BaseModel):
    """Schema for creating a new wallet with strict validation."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "name": "Bank BCA",
                "balance": 5000000.00,
                "icon": "bca"
            }
        }
    )
    
    name: str = Field(..., min_length=1, max_length=100, description="Wallet name")
    balance: Decimal = Field(default=Decimal("0.00"), ge=0, max_digits=15, decimal_places=2)
    icon: str = Field(default="wallet", max_length=50)


class WalletResponse(BaseModel):
    """Schema for wallet response."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": 1,
            "user_id": 1,
            "name": "Bank BCA",
            "balance": 5000000.00,
            "icon": "bca",
            "created_at": "2024-12-01T10:30:00"
        }
    })
    
    id: int
    user_id: int
    name: str
    balance: Decimal
    icon: Optional[str] = "wallet"
    created_at: datetime
