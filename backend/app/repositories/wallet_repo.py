import asyncpg
from typing import Optional, List
from decimal import Decimal


class WalletRepository:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def create(self, user_id: int, name: str, balance: Decimal = Decimal("0.00"), icon: str = "wallet") -> dict:
        row = await self.conn.fetchrow(
            """
            INSERT INTO wallets (user_id, name, balance, icon)
            VALUES ($1, $2, $3, $4)
            RETURNING id, user_id, name, balance, icon, created_at
            """,
            user_id, name, balance, icon
        )
        return dict(row)

    async def get_by_user(self, user_id: int) -> List[dict]:
        rows = await self.conn.fetch(
            """
            SELECT id, user_id, name, balance, icon, created_at
            FROM wallets WHERE user_id = $1
            ORDER BY created_at DESC
            """,
            user_id
        )
        return [dict(row) for row in rows]

    async def get_by_id(self, wallet_id: int, user_id: int) -> Optional[dict]:
        row = await self.conn.fetchrow(
            """
            SELECT id, user_id, name, balance, icon, created_at
            FROM wallets WHERE id = $1 AND user_id = $2
            """,
            wallet_id, user_id
        )
        return dict(row) if row else None

    async def update_balance(self, wallet_id: int, amount: Decimal, is_income: bool) -> dict:
        if is_income:
            row = await self.conn.fetchrow(
                """
                UPDATE wallets SET balance = balance + $1
                WHERE id = $2
                RETURNING id, user_id, name, balance, created_at
                """,
                amount, wallet_id
            )
        else:
            row = await self.conn.fetchrow(
                """
                UPDATE wallets SET balance = balance - $1
                WHERE id = $2
                RETURNING id, user_id, name, balance, created_at
                """,
                amount, wallet_id
            )
        return dict(row) if row else None

    async def delete(self, wallet_id: int, user_id: int) -> bool:
        result = await self.conn.execute(
            """
            DELETE FROM wallets
            WHERE id = $1 AND user_id = $2
            """,
            wallet_id, user_id
        )
        return result == "DELETE 1"
