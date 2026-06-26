from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import date
from decimal import Decimal
import asyncpg

from ..core.database import get_db_conn
from ..core.security import get_current_user
from ..schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    TransferRequest,
)
from ..repositories.transaction_repo import TransactionRepository
from ..repositories.wallet_repo import WalletRepository
from ..services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get(
    "",
    response_model=List[TransactionResponse],
    summary="List Transactions",
    description="""
Retrieve all transactions for the authenticated user.

**Filters:**
- `type`: Filter by `INCOME` or `EXPENSE`
- `start_date` / `end_date`: Date range filter (if provided, returns ALL in range)
- `limit`: Maximum results to return (default: 10, max: 100) - ignored if date range provided
- `offset`: Pagination offset for skipping records
    """,
    responses={
        200: {"description": "List of transactions"},
        401: {"description": "Not authenticated"},
        500: {"description": "Internal server error"},
    },
)
async def get_transactions(
    type: Optional[str] = Query(
        default=None, description="Filter by INCOME or EXPENSE"
    ),
    start_date: Optional[date] = Query(
        default=None, description="Start date for range filter"
    ),
    end_date: Optional[date] = Query(
        default=None, description="End date for range filter"
    ),
    limit: int = Query(
        default=10,
        le=100,
        description="Max results (default: 10, ignored if date range)",
    ),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_conn),
):
    trans_repo = TransactionRepository(conn)

    trans_type = None
    if type and type.upper() in ["INCOME", "EXPENSE"]:
        trans_type = type.upper()

    transactions = await trans_repo.get_by_user(
        current_user["id"],
        limit=limit,
        offset=offset,
        trans_type=trans_type,
        start_date=start_date,
        end_date=end_date,
    )
    return transactions


@router.get(
    "/suggestions",
    response_model=List[str],
    summary="Get Description Suggestions",
    description="Retrieve unique descriptions from user's transaction history for autocomplete.",
    responses={
        200: {"description": "List of unique descriptions"},
        401: {"description": "Not authenticated"},
    },
)
async def get_description_suggestions(
    q: Optional[str] = Query(None, description="Search keyword typed by user"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_conn),
):
    trans_repo = TransactionRepository(conn)
    return await trans_repo.get_distinct_descriptions(
        current_user["id"], category_id=category_id, search_term=q
    )


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
        409: {"description": "Duplicate transaction"},
    },
)
async def create_transaction(
    trans_data: TransactionCreate,
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_conn),
):
    service = TransactionService(conn)
    return await service.create_transaction(current_user["id"], trans_data)


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
        401: {"description": "Not authenticated"},
    },
)
async def get_summary(
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_conn),
):
    trans_repo = TransactionRepository(conn)
    wallet_repo = WalletRepository(conn)

    summary = await trans_repo.get_summary(current_user["id"])
    wallets = await wallet_repo.get_by_user(current_user["id"])

    total_balance = sum(w["balance"] for w in wallets)

    return {
        "total_income": summary["total_income"],
        "total_expense": summary["total_expense"],
        "total_balance": total_balance,
        "net": summary["total_income"] - summary["total_expense"],
    }


@router.put(
    "/{transaction_id}",
    response_model=TransactionResponse,
    summary="Update Transaction",
    description="""
Update an existing transaction with safe balance correction.

**Balance Handling:**
- Uses atomic "Revert & Apply" strategy
- Reverts the old transaction's effect on wallet balance
- Applies the new values' effect on wallet balance
- Handles wallet changes correctly (e.g., switching from Cash to Bank)
    """,
    responses={
        200: {"description": "Transaction updated successfully"},
        400: {"description": "Invalid data or insufficient balance"},
        403: {"description": "Category not accessible"},
        404: {"description": "Transaction, wallet, or category not found"},
    },
)
async def update_transaction(
    transaction_id: int,
    trans_data: TransactionUpdate,
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_conn),
):
    service = TransactionService(conn)
    return await service.update_transaction(transaction_id, current_user["id"], trans_data)


@router.delete(
    "/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Transaction",
    description="Delete a transaction and reverse its effect on the wallet balance.",
    responses={
        204: {"description": "Transaction deleted successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "Transaction not found"},
    },
)
async def delete_transaction(
    transaction_id: int,
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_conn),
):
    trans_repo = TransactionRepository(conn)
    deleted = await trans_repo.delete(transaction_id, current_user["id"])

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )


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
        400: {
            "description": "Invalid transfer (same wallet, insufficient balance, or amount <= 0)"
        },
        404: {"description": "Source or destination wallet not found"},
    },
)
async def transfer_funds(
    data: TransferRequest,
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_conn),
):
    service = TransactionService(conn)
    return await service.transfer_funds(current_user["id"], data)


@router.post(
    "/batch",
    response_model=List[TransactionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Batch Create Transactions",
    description="""
Create multiple transactions in a single atomic operation.

**Use Case:** Save scanned receipt items as transactions.

**Important:**
- All transactions are created within a database transaction
- If any transaction fails, none are committed
- Each item is validated the same as single create
    """,
    responses={
        201: {"description": "All transactions created successfully"},
        400: {"description": "Validation error on one or more transactions"},
        404: {"description": "Wallet or category not found"},
    },
)
async def batch_create_transactions(
    transactions_data: List[TransactionCreate],
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_conn),
):
    service = TransactionService(conn)
    return await service.batch_create_transactions(current_user["id"], transactions_data)
