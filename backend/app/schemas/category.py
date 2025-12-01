from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Literal


class CategoryCreate(BaseModel):
    """Schema for creating a new category."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "Groceries",
            "type": "EXPENSE",
            "icon": "shopping-cart"
        }
    })
    
    name: str
    type: Literal["INCOME", "EXPENSE"]
    icon: Optional[str] = "default"


class CategoryResponse(BaseModel):
    """Schema for category response."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": 1,
            "user_id": None,
            "name": "Food & Dining",
            "type": "EXPENSE",
            "icon": "utensils",
            "is_global": True,
            "created_at": "2024-12-01T10:30:00"
        }
    })
    
    id: int
    user_id: Optional[int]
    name: str
    type: str
    icon: Optional[str]
    is_global: bool = False
    created_at: datetime
