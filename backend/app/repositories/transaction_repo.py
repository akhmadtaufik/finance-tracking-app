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
                COALESCE(SUM(CASE WHEN type = 'INCOME' THEN amount ELSE 0 END), 0) as total_income,
                COALESCE(SUM(CASE WHEN type = 'EXPENSE' THEN amount ELSE 0 END), 0) as total_expense
            FROM transactions
            WHERE user_id = $1
            """,
            user_id
        )
        return dict(row)

    async def delete(self, transaction_id: int, user_id: int) -> bool:
        async with self.conn.transaction():
            # Get transaction details first
            trans = await self.conn.fetchrow(
                "SELECT wallet_id, amount, type FROM transactions WHERE id = $1 AND user_id = $2",
                transaction_id, user_id
            )
            
            if not trans:
                return False
            
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
