import asyncpg
from typing import Optional, List
from decimal import Decimal
from datetime import date


class TransactionRepository:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def create(
        self,
        user_id: int,
        wallet_id: int,
        category_id: int,
        amount: Decimal,
        trans_type: str,
        transaction_date: date,
        description: Optional[str] = None
    ) -> dict:
        async with self.conn.transaction():
            wallet = await self.conn.fetchrow(
                """
                SELECT id, balance
                FROM wallets
                WHERE id = $1 AND user_id = $2
                FOR UPDATE
                """,
                wallet_id, user_id
            )
            if not wallet:
                raise ValueError("Wallet not found")
            if trans_type == "EXPENSE" and wallet["balance"] < amount:
                raise ValueError("Insufficient balance in wallet")
            
            # Insert transaction
            row = await self.conn.fetchrow(
                """
                INSERT INTO transactions (user_id, wallet_id, category_id, amount, type, transaction_date, description)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id, user_id, wallet_id, category_id, amount, type, transaction_date, description, created_at
                """,
                user_id, wallet_id, category_id, amount, trans_type, transaction_date, description
            )
            
            # Update wallet balance
            if trans_type == "INCOME":
                await self.conn.execute(
                    "UPDATE wallets SET balance = balance + $1 WHERE id = $2",
                    amount, wallet_id
                )
            else:
                await self.conn.execute(
                    "UPDATE wallets SET balance = balance - $1 WHERE id = $2",
                    amount, wallet_id
                )
            
            return dict(row)

    async def get_by_user(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        trans_type: Optional[str] = None
    ) -> List[dict]:
        if trans_type:
            rows = await self.conn.fetch(
                """
                SELECT t.id, t.user_id, t.wallet_id, t.category_id, t.amount, t.type,
                       t.transaction_date, t.description, t.created_at,
                       c.name as category_name, w.name as wallet_name
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                JOIN wallets w ON t.wallet_id = w.id
                WHERE t.user_id = $1 AND t.type = $2
                ORDER BY t.transaction_date DESC, t.created_at DESC
                LIMIT $3 OFFSET $4
                """,
                user_id, trans_type, limit, offset
            )
        else:
            rows = await self.conn.fetch(
                """
                SELECT t.id, t.user_id, t.wallet_id, t.category_id, t.amount, t.type,
                       t.transaction_date, t.description, t.created_at,
                       c.name as category_name, w.name as wallet_name
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                JOIN wallets w ON t.wallet_id = w.id
                WHERE t.user_id = $1
                ORDER BY t.transaction_date DESC, t.created_at DESC
                LIMIT $2 OFFSET $3
                """,
                user_id, limit, offset
            )
        return [dict(row) for row in rows]

    async def get_summary(self, user_id: int) -> dict:
        row = await self.conn.fetchrow(
            """
            SELECT 
                COALESCE(SUM(CASE WHEN t.type = 'INCOME' AND LOWER(c.name) <> 'transfer' THEN t.amount ELSE 0 END), 0) as total_income,
                COALESCE(SUM(CASE WHEN t.type = 'EXPENSE' AND LOWER(c.name) <> 'transfer' THEN t.amount ELSE 0 END), 0) as total_expense
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = $1
            """,
            user_id
        )
        return dict(row)

    async def transfer_funds(
        self,
        user_id: int,
        source_wallet_id: int,
        dest_wallet_id: int,
        amount: Decimal,
        transaction_date: date,
        description: Optional[str] = None
    ) -> dict:
        async with self.conn.transaction():
            source_wallet = await self.conn.fetchrow(
                """
                SELECT id, balance
                FROM wallets
                WHERE id = $1 AND user_id = $2
                FOR UPDATE
                """,
                source_wallet_id, user_id
            )
            if not source_wallet:
                raise ValueError("Source wallet not found")
            
            dest_wallet = await self.conn.fetchrow(
                """
                SELECT id
                FROM wallets
                WHERE id = $1 AND user_id = $2
                FOR UPDATE
                """,
                dest_wallet_id, user_id
            )
            if not dest_wallet:
                raise ValueError("Destination wallet not found")
            
            if source_wallet["balance"] < amount:
                raise ValueError("Insufficient balance in source wallet")
            
            # Get or create "Transfer" category (global)
            category = await self.conn.fetchrow(
                """
                SELECT id FROM categories 
                WHERE name = 'Transfer' AND (user_id = $1 OR user_id IS NULL)
                ORDER BY user_id NULLS LAST
                LIMIT 1
                """,
                user_id
            )
            
            if not category:
                category = await self.conn.fetchrow(
                    """
                    INSERT INTO categories (user_id, name, type, icon)
                    VALUES (NULL, 'Transfer', 'EXPENSE', 'repeat')
                    ON CONFLICT (user_id, name, type) DO UPDATE SET icon = 'repeat'
                    RETURNING id
                    """
                )
            
            category_id = category['id']
            transfer_desc = description or "Transfer between wallets"
            
            # Deduct from source wallet
            await self.conn.execute(
                "UPDATE wallets SET balance = balance - $1 WHERE id = $2 AND user_id = $3",
                amount, source_wallet_id, user_id
            )
            
            # Add to destination wallet
            await self.conn.execute(
                "UPDATE wallets SET balance = balance + $1 WHERE id = $2 AND user_id = $3",
                amount, dest_wallet_id, user_id
            )
            
            # Insert EXPENSE record (from source)
            out_record = await self.conn.fetchrow(
                """
                INSERT INTO transactions (user_id, wallet_id, category_id, amount, type, transaction_date, description)
                VALUES ($1, $2, $3, $4, 'EXPENSE', $5, $6)
                RETURNING id, user_id, wallet_id, category_id, amount, type, transaction_date, description, created_at
                """,
                user_id, source_wallet_id, category_id, amount, transaction_date, f"[OUT] {transfer_desc}"
            )
            
            # Insert INCOME record (to destination)
            in_record = await self.conn.fetchrow(
                """
                INSERT INTO transactions (user_id, wallet_id, category_id, amount, type, transaction_date, description)
                VALUES ($1, $2, $3, $4, 'INCOME', $5, $6)
                RETURNING id, user_id, wallet_id, category_id, amount, type, transaction_date, description, created_at
                """,
                user_id, dest_wallet_id, category_id, amount, transaction_date, f"[IN] {transfer_desc}"
            )
            
            return {
                "out_transaction": dict(out_record),
                "in_transaction": dict(in_record),
                "amount": float(amount)
            }

    async def delete(self, transaction_id: int, user_id: int) -> bool:
        async with self.conn.transaction():
            # Get transaction details first
            trans = await self.conn.fetchrow(
                "SELECT wallet_id, amount, type FROM transactions WHERE id = $1 AND user_id = $2",
                transaction_id, user_id
            )
            
            if not trans:
                return False
            
            await self.conn.fetchrow(
                "SELECT id FROM wallets WHERE id = $1 AND user_id = $2 FOR UPDATE",
                trans['wallet_id'], user_id
            )
            
            # Reverse the balance change
            if trans['type'] == "INCOME":
                await self.conn.execute(
                    "UPDATE wallets SET balance = balance - $1 WHERE id = $2",
                    trans['amount'], trans['wallet_id']
                )
            else:
                await self.conn.execute(
                    "UPDATE wallets SET balance = balance + $1 WHERE id = $2",
                    trans['amount'], trans['wallet_id']
                )
            
            # Delete the transaction
            result = await self.conn.execute(
                "DELETE FROM transactions WHERE id = $1 AND user_id = $2",
                transaction_id, user_id
            )
            
            return result == "DELETE 1"
