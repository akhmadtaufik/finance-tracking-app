from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
import asyncpg

from ..core.database import get_db_conn
from ..core.security import get_current_user
from ..schemas.category import CategoryCreate, CategoryResponse
from ..repositories.category_repo import CategoryRepository

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=List[CategoryResponse])
async def get_categories(
    type: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    category_repo = CategoryRepository(conn)
    
    if type and type.upper() in ["INCOME", "EXPENSE"]:
        categories = await category_repo.get_by_type(current_user["id"], type.upper())
    else:
        categories = await category_repo.get_all(current_user["id"])
    
    return categories


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    category_repo = CategoryRepository(conn)
    
    try:
        category = await category_repo.create(
            current_user["id"],
            category_data.name,
            category_data.type,
            category_data.icon or "default"
        )
        return category
    except asyncpg.UniqueViolationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this name and type already exists"
        )


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    category_repo = CategoryRepository(conn)
    
    # Check if category exists and belongs to user (not global)
    category = await category_repo.get_by_id(category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    
    if category["user_id"] is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete global category")
    
    if category["user_id"] != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    deleted = await category_repo.delete(category_id, current_user["id"])
    if not deleted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not delete category")
