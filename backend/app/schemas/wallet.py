from pydantic import BaseModel, ConfigDict
from datetime import datetime
from decimal import Decimal
from typing import Optional


class WalletCreate(BaseModel):
    """Schema for creating a new wallet."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "Bank BCA",
            "balance": 5000000.00,
            "icon": "bca"
        }
    })
    
    name: str
    balance: Optional[Decimal] = Decimal("0.00")
    icon: Optional[str] = "wallet"


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
