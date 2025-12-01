import asyncpg
from typing import Optional


class UserRepository:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def create(self, email: str, username: str, password_hash: str) -> dict:
        row = await self.conn.fetchrow(
            """
            INSERT INTO users (email, username, password_hash)
            VALUES ($1, $2, $3)
            RETURNING id, email, username, created_at
            """,
            email, username, password_hash
        )
        return dict(row)

    async def get_by_email(self, email: str) -> Optional[dict]:
        row = await self.conn.fetchrow(
            "SELECT id, email, username, password_hash, created_at FROM users WHERE email = $1",
            email
        )
        return dict(row) if row else None

    async def get_by_id(self, user_id: int) -> Optional[dict]:
        row = await self.conn.fetchrow(
            "SELECT id, email, username, created_at FROM users WHERE id = $1",
            user_id
        )
        return dict(row) if row else None
