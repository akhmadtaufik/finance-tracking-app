from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    """Schema for user registration."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "email": "john@example.com",
            "username": "johndoe",
            "password": "SecureP@ss123"
        }
    })
    
    email: EmailStr
    username: str
    password: str


class UserResponse(BaseModel):
    """Schema for user response (excludes password)."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": 1,
            "email": "john@example.com",
            "username": "johndoe",
            "is_superuser": False,
            "is_active": True,
            "created_at": "2024-12-01T10:30:00"
        }
    })
    
    id: int
    email: str
    username: str
    is_superuser: bool = False
    is_active: bool = True
    created_at: datetime


class Token(BaseModel):
    """Schema for JWT access token response."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer"
        }
    })
    
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for decoded token data."""
    user_id: Optional[int] = None
