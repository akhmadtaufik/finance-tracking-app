import asyncpg
from typing import Optional, List


class CategoryRepository:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def get_all(self, user_id: int) -> List[dict]:
        rows = await self.conn.fetch(
            """
            SELECT id, user_id, name, type, icon, created_at,
                   CASE WHEN user_id IS NULL THEN true ELSE false END as is_global
            FROM categories
            WHERE user_id IS NULL OR user_id = $1
            ORDER BY type, name
            """,
            user_id
        )
        return [dict(row) for row in rows]

    async def get_by_type(self, user_id: int, category_type: str) -> List[dict]:
        rows = await self.conn.fetch(
            """
            SELECT id, user_id, name, type, icon, created_at,
                   CASE WHEN user_id IS NULL THEN true ELSE false END as is_global
            FROM categories
            WHERE (user_id IS NULL OR user_id = $1) AND type = $2
            ORDER BY name
            """,
            user_id, category_type
        )
        return [dict(row) for row in rows]

    async def create(self, user_id: int, name: str, category_type: str, icon: str = "default") -> dict:
        row = await self.conn.fetchrow(
            """
            INSERT INTO categories (user_id, name, type, icon)
            VALUES ($1, $2, $3, $4)
            RETURNING id, user_id, name, type, icon, created_at,
                      CASE WHEN user_id IS NULL THEN true ELSE false END as is_global
            """,
            user_id, name, category_type, icon
        )
        return dict(row)

    async def get_by_id(self, category_id: int) -> Optional[dict]:
        row = await self.conn.fetchrow(
            """
            SELECT id, user_id, name, type, icon, created_at
            FROM categories WHERE id = $1
            """,
            category_id
        )
        return dict(row) if row else None

    async def delete(self, category_id: int, user_id: int) -> bool:
        result = await self.conn.execute(
            """
            DELETE FROM categories
            WHERE id = $1 AND user_id = $2
            """,
            category_id, user_id
        )
        return result == "DELETE 1"
