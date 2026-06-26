import asyncpg
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import date

from ..schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransferRequest,
)
from ..repositories.transaction_repo import TransactionRepository
from ..repositories.wallet_repo import WalletRepository
from ..repositories.category_repo import CategoryRepository


class TransactionService:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn
        self.wallet_repo = WalletRepository(conn)
        self.category_repo = CategoryRepository(conn)
        self.trans_repo = TransactionRepository(conn)

    async def create_transaction(
        self, current_user_id: int, trans_data: TransactionCreate
    ) -> dict:
        # Verify wallet belongs to user
        wallet = await self.wallet_repo.get_by_id(trans_data.wallet_id, current_user_id)
        if not wallet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found"
            )

        # Verify category exists and is accessible to user
        category = await self.category_repo.get_by_id(trans_data.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
            )

        if category["user_id"] is not None and category["user_id"] != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Category not accessible"
            )

        # Validate category type matches transaction type
        if category["type"] != trans_data.type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category type ({category['type']}) does not match transaction type ({trans_data.type})",
            )

        try:
            transaction = await self.trans_repo.create(
                user_id=current_user_id,
                wallet_id=trans_data.wallet_id,
                category_id=trans_data.category_id,
                amount=trans_data.amount,
                trans_type=trans_data.type,
                transaction_date=trans_data.transaction_date or date.today(),
                description=trans_data.description,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
            ) from exc

        # Add category and wallet names to response
        transaction["category_name"] = category["name"]
        transaction["wallet_name"] = wallet["name"]

        return transaction

    async def update_transaction(
        self, transaction_id: int, current_user_id: int, trans_data: TransactionUpdate
    ) -> dict:
        # Validate wallet if provided
        if trans_data.wallet_id is not None:
            wallet = await self.wallet_repo.get_by_id(
                trans_data.wallet_id, current_user_id
            )
            if not wallet:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found"
                )

        # Validate category if provided
        if trans_data.category_id is not None:
            category = await self.category_repo.get_by_id(trans_data.category_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
                )
            if (
                category["user_id"] is not None
                and category["user_id"] != current_user_id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Category not accessible",
                )
            # Validate category type matches transaction type if both provided
            if trans_data.type is not None and category["type"] != trans_data.type:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Category type ({category['type']}) does not match transaction type ({trans_data.type})",
                )

        try:
            transaction = await self.trans_repo.update(
                transaction_id=transaction_id,
                user_id=current_user_id,
                wallet_id=trans_data.wallet_id,
                category_id=trans_data.category_id,
                amount=trans_data.amount,
                trans_type=trans_data.type,
                transaction_date=trans_data.transaction_date,
                description=trans_data.description,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
            ) from exc

        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
            )

        # Fetch category and wallet names for response
        cat = await self.category_repo.get_by_id(transaction["category_id"])
        wal = await self.wallet_repo.get_by_id(
            transaction["wallet_id"], current_user_id
        )
        transaction["category_name"] = cat["name"] if cat else None
        transaction["wallet_name"] = wal["name"] if wal else None

        return transaction

    async def transfer_funds(
        self, current_user_id: int, data: TransferRequest
    ) -> dict:
        # Validate source != destination
        if data.source_wallet_id == data.dest_wallet_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source and destination wallets must be different",
            )

        # Validate amount > 0
        if data.amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Amount must be greater than 0",
            )

        # Verify source wallet belongs to user
        source_wallet = await self.wallet_repo.get_by_id(
            data.source_wallet_id, current_user_id
        )
        if not source_wallet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Source wallet not found"
            )

        # Verify destination wallet belongs to user
        dest_wallet = await self.wallet_repo.get_by_id(
            data.dest_wallet_id, current_user_id
        )
        if not dest_wallet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Destination wallet not found",
            )

        # Check sufficient balance
        if source_wallet["balance"] < data.amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient balance in source wallet",
            )

        # Perform transfer
        try:
            result = await self.trans_repo.transfer_funds(
                user_id=current_user_id,
                source_wallet_id=data.source_wallet_id,
                dest_wallet_id=data.dest_wallet_id,
                amount=data.amount,
                transaction_date=data.transaction_date or date.today(),
                description=data.description,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
            ) from exc

        return {
            "message": "Transfer successful",
            "amount": result["amount"],
            "source_wallet": source_wallet["name"],
            "dest_wallet": dest_wallet["name"],
        }

    async def batch_create_transactions(
        self, current_user_id: int, transactions_data: List[TransactionCreate]
    ) -> List[dict]:
        if not transactions_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transaction list cannot be empty",
            )

        # Pre-fetch all wallets for this user to avoid N+1 queries
        all_wallets = await self.wallet_repo.get_by_user(current_user_id)
        wallets_map = {w["id"]: w for w in all_wallets}

        # Pre-fetch all available categories (both global and user-specific)
        all_categories = await self.category_repo.get_all(current_user_id)
        categories_map = {c["id"]: c for c in all_categories}

        created_transactions = []

        # Use a single database transaction for atomicity
        async with self.conn.transaction():
            for idx, trans_data in enumerate(transactions_data):
                # Verify wallet belongs to user using cached map
                wallet = wallets_map.get(trans_data.wallet_id)
                if not wallet:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Item {idx + 1}: Wallet not found",
                    )

                # Verify category exists and is accessible using cached map
                category = categories_map.get(trans_data.category_id)
                if not category:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Item {idx + 1}: Category not found",
                    )

                if (
                    category["user_id"] is not None
                    and category["user_id"] != current_user_id
                ):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Item {idx + 1}: Category not accessible",
                    )

                # Validate category type matches transaction type
                if category["type"] != trans_data.type:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            f"Item {idx + 1}: Category type ({category['type']}) "
                            f"does not match transaction type ({trans_data.type})"
                        ),
                    )

                try:
                    transaction = await self.trans_repo.create(
                        user_id=current_user_id,
                        wallet_id=trans_data.wallet_id,
                        category_id=trans_data.category_id,
                        amount=trans_data.amount,
                        trans_type=trans_data.type,
                        transaction_date=trans_data.transaction_date or date.today(),
                        description=trans_data.description,
                    )
                except ValueError as exc:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Item {idx + 1}: {str(exc)}",
                    ) from exc

                # Add category and wallet names
                transaction["category_name"] = category["name"]
                transaction["wallet_name"] = wallet["name"]
                created_transactions.append(transaction)

        return created_transactions
