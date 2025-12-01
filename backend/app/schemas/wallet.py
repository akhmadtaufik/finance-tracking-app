from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import Optional


class WalletCreate(BaseModel):
    name: str
    balance: Optional[Decimal] = Decimal("0.00")


class WalletResponse(BaseModel):
    id: int
    user_id: int
    name: str
    balance: Decimal
    created_at: datetime
