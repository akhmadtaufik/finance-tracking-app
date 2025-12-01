from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal


class CategoryCreate(BaseModel):
    name: str
    type: Literal["INCOME", "EXPENSE"]
    icon: Optional[str] = "default"


class CategoryResponse(BaseModel):
    id: int
    user_id: Optional[int]
    name: str
    type: str
    icon: Optional[str]
    is_global: bool = False
    created_at: datetime
