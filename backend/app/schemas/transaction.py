from pydantic import BaseModel
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Literal


class TransactionCreate(BaseModel):
    wallet_id: int
    category_id: int
    amount: Decimal
    type: Literal["INCOME", "EXPENSE"]
    transaction_date: Optional[date] = None
    description: Optional[str] = None


class TransactionResponse(BaseModel):
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
