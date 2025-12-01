from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
import asyncpg

from ..core.database import get_db_conn
from ..core.security import get_current_user
from ..schemas.transaction import TransactionCreate, TransactionResponse
from ..repositories.transaction_repo import TransactionRepository
from ..repositories.wallet_repo import WalletRepository
from ..repositories.category_repo import CategoryRepository

router = APIRouter(prefix="/transactions", tags=["Transactions"])


class TransferRequest(BaseModel):
    """Schema for wallet-to-wallet transfer request."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "source_wallet_id": 1,
            "dest_wallet_id": 2,
            "amount": 500000.00,
            "transaction_date": "2024-12-01",
            "description": "Transfer ke dompet darurat"
        }
    })
    
    source_wallet_id: int
    dest_wallet_id: int
    amount: Decimal
    transaction_date: Optional[date] = None
    description: Optional[str] = None


@router.get(
    "",
    response_model=List[TransactionResponse],
    summary="List Transactions",
    description="""
Retrieve all transactions for the authenticated user.

**Filters:**
- `type`: Filter by `INCOME` or `EXPENSE`
- `limit`: Maximum results to return (default: 50, max: 100)
- `offset`: Pagination offset for skipping records
    """,
    responses={
        200: {"description": "List of transactions"},
        401: {"description": "Not authenticated"},
        500: {"description": "Internal server error"}
    }
)
async def get_transactions(
    type: Optional[str] = Query(default=None, description="Filter by INCOME or EXPENSE"),
    limit: int = Query(default=50, le=100, description="Max results (default: 50)"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    trans_repo = TransactionRepository(conn)
    
    trans_type = None
    if type and type.upper() in ["INCOME", "EXPENSE"]:
        trans_type = type.upper()
    
    transactions = await trans_repo.get_by_user(
        current_user["id"],
        limit=limit,
        offset=offset,
        trans_type=trans_type
    )
    return transactions


@router.post(
    "",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Transaction",
    description="Record a new income or expense transaction for the authenticated user.",
    responses={
        201: {"description": "Transaction created successfully"},
        400: {"description": "Category type mismatch with transaction type"},
        403: {"description": "Category not accessible"},
        404: {"description": "Wallet or Category not found"},
        409: {"description": "Duplicate transaction"}
    }
)
async def create_transaction(
    trans_data: TransactionCreate,
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    wallet_repo = WalletRepository(conn)
    category_repo = CategoryRepository(conn)
    trans_repo = TransactionRepository(conn)
    
    # Verify wallet belongs to user
    wallet = await wallet_repo.get_by_id(trans_data.wallet_id, current_user["id"])
    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
    
    # Verify category exists and is accessible to user
    category = await category_repo.get_by_id(trans_data.category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    
    if category["user_id"] is not None and category["user_id"] != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Category not accessible")
    
    # Validate category type matches transaction type
    if category["type"] != trans_data.type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category type ({category['type']}) does not match transaction type ({trans_data.type})"
        )
    
    transaction = await trans_repo.create(
        user_id=current_user["id"],
        wallet_id=trans_data.wallet_id,
        category_id=trans_data.category_id,
        amount=trans_data.amount,
        trans_type=trans_data.type,
        transaction_date=trans_data.transaction_date or date.today(),
        description=trans_data.description
    )
    
    # Add category and wallet names to response
    transaction["category_name"] = category["name"]
    transaction["wallet_name"] = wallet["name"]
    
    return transaction


@router.get(
    "/summary",
    summary="Get Financial Summary",
    description="""
Get a summary of the user's financial status.

**Returns:**
- `total_income`: Sum of all income transactions
- `total_expense`: Sum of all expense transactions  
- `total_balance`: Sum of all wallet balances
- `net`: Income minus Expense
    """,
    responses={
        200: {"description": "Financial summary"},
        401: {"description": "Not authenticated"}
    }
)
async def get_summary(
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    trans_repo = TransactionRepository(conn)
    wallet_repo = WalletRepository(conn)
    
    summary = await trans_repo.get_summary(current_user["id"])
    wallets = await wallet_repo.get_by_user(current_user["id"])
    
    total_balance = sum(w["balance"] for w in wallets)
    
    return {
        "total_income": float(summary["total_income"]),
        "total_expense": float(summary["total_expense"]),
        "total_balance": float(total_balance),
        "net": float(summary["total_income"] - summary["total_expense"])
    }


@router.delete(
    "/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Transaction",
    description="Delete a transaction and reverse its effect on the wallet balance.",
    responses={
        204: {"description": "Transaction deleted successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "Transaction not found"}
    }
)
async def delete_transaction(
    transaction_id: int,
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    trans_repo = TransactionRepository(conn)
    deleted = await trans_repo.delete(transaction_id, current_user["id"])
    
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")


@router.post(
    "/transfer",
    status_code=status.HTTP_201_CREATED,
    summary="Transfer Between Wallets",
    description="""
Transfer funds between two wallets owned by the authenticated user.

**Important Notes:**
- Creates paired EXPENSE (from source) and INCOME (to destination) transactions
- Automatically uses the global 'Transfer' category
- Transfer transactions are **excluded** from expense analytics and reports
- Both wallets must belong to the authenticated user
    """,
    responses={
        201: {"description": "Transfer completed successfully"},
        400: {"description": "Invalid transfer (same wallet, insufficient balance, or amount <= 0)"},
        404: {"description": "Source or destination wallet not found"}
    }
)
async def transfer_funds(
    data: TransferRequest,
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    wallet_repo = WalletRepository(conn)
    trans_repo = TransactionRepository(conn)
    
    # Validate source != destination
    if data.source_wallet_id == data.dest_wallet_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source and destination wallets must be different"
        )
    
    # Validate amount > 0
    if data.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be greater than 0"
        )
    
    # Verify source wallet belongs to user
    source_wallet = await wallet_repo.get_by_id(data.source_wallet_id, current_user["id"])
    if not source_wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source wallet not found"
        )
    
    # Verify destination wallet belongs to user
    dest_wallet = await wallet_repo.get_by_id(data.dest_wallet_id, current_user["id"])
    if not dest_wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Destination wallet not found"
        )
    
    # Check sufficient balance
    if source_wallet["balance"] < data.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance in source wallet"
        )
    
    # Perform transfer
    result = await trans_repo.transfer_funds(
        user_id=current_user["id"],
        source_wallet_id=data.source_wallet_id,
        dest_wallet_id=data.dest_wallet_id,
        amount=data.amount,
        transaction_date=data.transaction_date or date.today(),
        description=data.description
    )
    
    return {
        "message": "Transfer successful",
        "amount": result["amount"],
        "source_wallet": source_wallet["name"],
        "dest_wallet": dest_wallet["name"]
    }
