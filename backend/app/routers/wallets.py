from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import asyncpg

from ..core.database import get_db_conn
from ..core.security import get_current_user
from ..schemas.wallet import WalletCreate, WalletResponse
from ..repositories.wallet_repo import WalletRepository

router = APIRouter(prefix="/wallets", tags=["Wallets"])


@router.get("", response_model=List[WalletResponse])
async def get_wallets(
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    wallet_repo = WalletRepository(conn)
    wallets = await wallet_repo.get_by_user(current_user["id"])
    return wallets


@router.post("", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
async def create_wallet(
    wallet_data: WalletCreate,
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    wallet_repo = WalletRepository(conn)
    wallet = await wallet_repo.create(
        current_user["id"],
        wallet_data.name,
        wallet_data.balance,
        wallet_data.icon
    )
    return wallet


@router.get("/{wallet_id}", response_model=WalletResponse)
async def get_wallet(
    wallet_id: int,
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    wallet_repo = WalletRepository(conn)
    wallet = await wallet_repo.get_by_id(wallet_id, current_user["id"])
    
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )
    
    return wallet


@router.delete("/{wallet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wallet(
    wallet_id: int,
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    wallet_repo = WalletRepository(conn)
    wallet = await wallet_repo.get_by_id(wallet_id, current_user["id"])
    
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )
    
    deleted = await wallet_repo.delete(wallet_id, current_user["id"])
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not delete wallet"
        )
