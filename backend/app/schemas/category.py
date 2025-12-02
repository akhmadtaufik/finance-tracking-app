import re
from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
from typing import Optional, Literal


class CategoryCreate(BaseModel):
    """Schema for creating a new category with strict validation."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "name": "Groceries",
                "type": "EXPENSE",
                "icon": "shopping-cart"
            }
        }
    )
    
    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    type: Literal["INCOME", "EXPENSE"]
    icon: str = Field(default="default", max_length=50)
    
    @field_validator('name')
    @classmethod
    def sanitize_name(cls, value: str) -> str:
        sanitized = re.sub(r'<[^>]+>', '', value)
        return sanitized.strip()


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
