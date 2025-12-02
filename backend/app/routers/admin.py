from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta, timezone
import asyncpg

from ..core.database import get_db_conn
from ..core.deps import get_current_active_superuser
from ..schemas.user import UserResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


class CategoryCreate(BaseModel):
    name: str
    type: str  # INCOME or EXPENSE
    icon: Optional[str] = "default"


@router.get("/stats")
async def get_admin_stats(
    current_user: dict = Depends(get_current_active_superuser),
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    # Total users
    total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
    
    # Total transactions
    total_transactions = await conn.fetchval("SELECT COUNT(*) FROM transactions")
    
    # Active users in last 24 hours (users who made transactions)
    yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
    active_users_24h = await conn.fetchval(
        """
        SELECT COUNT(DISTINCT user_id) 
        FROM transactions 
        WHERE created_at >= $1
        """,
        yesterday
    )
    
    # Total income/expense
    totals = await conn.fetchrow(
        """
        SELECT 
            COALESCE(SUM(CASE WHEN type = 'INCOME' THEN amount ELSE 0 END), 0) as total_income,
            COALESCE(SUM(CASE WHEN type = 'EXPENSE' THEN amount ELSE 0 END), 0) as total_expense
        FROM transactions
        """
    )
    
    return {
        "total_users": total_users,
        "total_transactions": total_transactions,
        "active_users_24h": active_users_24h,
        "total_income": float(totals["total_income"]),
        "total_expense": float(totals["total_expense"])
    }


@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    current_user: dict = Depends(get_current_active_superuser),
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    users = await conn.fetch(
        """
        SELECT 
            u.id, u.email, u.username, u.is_superuser, u.is_active, u.created_at
        FROM users u
        ORDER BY u.created_at DESC
        """
    )
    
    return [UserResponse(**dict(user)) for user in users]


@router.patch("/users/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: int,
    current_user: dict = Depends(get_current_active_superuser),
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    # Prevent admin from deactivating themselves
    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own status"
        )
    
    # Check if user exists
    user = await conn.fetchrow(
        "SELECT id, is_active, is_superuser FROM users WHERE id = $1",
        user_id
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent deactivating other superusers
    if user["is_superuser"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change status of another superuser"
        )
    
    new_status = not user["is_active"]
    
    await conn.execute(
        "UPDATE users SET is_active = $1 WHERE id = $2",
        new_status, user_id
    )
    
    return {
        "id": user_id,
        "is_active": new_status,
        "message": f"User {'activated' if new_status else 'deactivated'} successfully"
    }


@router.get("/categories")
async def get_global_categories(
    current_user: dict = Depends(get_current_active_superuser),
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    categories = await conn.fetch(
        """
        SELECT id, name, type, icon, created_at
        FROM categories
        WHERE user_id IS NULL
        ORDER BY type, name
        """
    )
    
    return [
        {
            "id": cat["id"],
            "name": cat["name"],
            "type": cat["type"],
            "icon": cat["icon"],
            "created_at": str(cat["created_at"])
        }
        for cat in categories
    ]


@router.post("/categories", status_code=status.HTTP_201_CREATED)
async def create_global_category(
    category: CategoryCreate,
    current_user: dict = Depends(get_current_active_superuser),
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    if category.type not in ["INCOME", "EXPENSE"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Type must be INCOME or EXPENSE"
        )
    
    # Check if category already exists
    existing = await conn.fetchrow(
        """
        SELECT id FROM categories 
        WHERE user_id IS NULL AND name = $1 AND type = $2
        """,
        category.name, category.type
    )
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Global category with this name and type already exists"
        )
    
    row = await conn.fetchrow(
        """
        INSERT INTO categories (user_id, name, type, icon)
        VALUES (NULL, $1, $2, $3)
        RETURNING id, name, type, icon, created_at
        """,
        category.name, category.type, category.icon
    )
    
    return {
        "id": row["id"],
        "name": row["name"],
        "type": row["type"],
        "icon": row["icon"],
        "created_at": str(row["created_at"])
    }


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_global_category(
    category_id: int,
    current_user: dict = Depends(get_current_active_superuser),
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    # Check if category exists and is global
    category = await conn.fetchrow(
        "SELECT id, user_id FROM categories WHERE id = $1",
        category_id
    )
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    if category["user_id"] is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only delete global categories (user_id must be NULL)"
        )
    
    # Check if category is used in transactions
    usage_count = await conn.fetchval(
        "SELECT COUNT(*) FROM transactions WHERE category_id = $1",
        category_id
    )
    
    if usage_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete category: it is used in {usage_count} transactions"
        )
    
    await conn.execute(
        "DELETE FROM categories WHERE id = $1",
        category_id
    )
