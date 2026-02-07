from fastapi import APIRouter, Depends, HTTPException, status
import asyncpg

from backend.app.core.database import get_db_conn
from backend.app.core.security import get_current_user, verify_password, hash_password
from backend.app.schemas.user import UserUpdate, UserPasswordUpdate, UserResponse
from backend.app.repositories.user_repo import UserRepository


router = APIRouter(prefix="/users", tags=["Users"])


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    data: UserUpdate,
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_conn),
):
    """Update current user's profile (username)."""
    repo = UserRepository(conn)

    updated_user = await repo.update_username(current_user["id"], data.username)

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return updated_user


@router.put("/password")
async def change_password(
    data: UserPasswordUpdate,
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_conn),
):
    """Change current user's password."""
    repo = UserRepository(conn)

    # Fetch user with password hash
    user = await repo.get_by_id_with_password(current_user["id"])

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Verify current password
    if not verify_password(data.current_password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Hash new password and update
    new_hash = hash_password(data.new_password)
    success = await repo.update_password(current_user["id"], new_hash)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password",
        )

    return {"message": "Password updated successfully"}
