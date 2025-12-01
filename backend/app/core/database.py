import asyncpg
from typing import AsyncGenerator
from .config import settings

pool: asyncpg.Pool = None


async def create_pool():
    global pool
    pool = await asyncpg.create_pool(settings.DATABASE_URL, min_size=5, max_size=20)
    print("Database pool created")


async def close_pool():
    global pool
    if pool:
        await pool.close()
        print("Database pool closed")


async def get_db_conn() -> AsyncGenerator[asyncpg.Connection, None]:
    async with pool.acquire() as conn:
        yield conn
