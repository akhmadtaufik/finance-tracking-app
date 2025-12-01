import asyncpg
from typing import List
from datetime import date


class AnalyticsRepository:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def get_category_breakdown(
        self,
        user_id: int,
        start_date: date,
        end_date: date,
        trans_type: str = "EXPENSE"
    ) -> List[dict]:
        rows = await self.conn.fetch(
            """
            SELECT c.name, c.icon, SUM(t.amount) as total
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = $1
              AND t.type = $2
              AND t.transaction_date >= $3
              AND t.transaction_date <= $4
              AND c.name != 'Transfer'
            GROUP BY c.id, c.name, c.icon
            HAVING SUM(t.amount) > 0
            ORDER BY total DESC
            """,
            user_id, trans_type, start_date, end_date
        )
        return [dict(row) for row in rows]

    async def get_daily_totals(
        self,
        user_id: int,
        start_date: date,
        end_date: date,
        trans_type: str = "EXPENSE"
    ) -> List[dict]:
        rows = await self.conn.fetch(
            """
            SELECT transaction_date, SUM(amount) as total
            FROM transactions
            WHERE user_id = $1
              AND type = $2
              AND transaction_date >= $3
              AND transaction_date <= $4
            GROUP BY transaction_date
            ORDER BY transaction_date ASC
            """,
            user_id, trans_type, start_date, end_date
        )
        return [dict(row) for row in rows]

    async def get_period_summary(
        self,
        user_id: int,
        start_date: date,
        end_date: date
    ) -> dict:
        row = await self.conn.fetchrow(
            """
            SELECT 
                COALESCE(SUM(CASE WHEN t.type = 'INCOME' AND c.name != 'Transfer' THEN t.amount ELSE 0 END), 0) as total_income,
                COALESCE(SUM(CASE WHEN t.type = 'EXPENSE' AND c.name != 'Transfer' THEN t.amount ELSE 0 END), 0) as total_expense,
                COUNT(*) as transaction_count
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = $1
              AND t.transaction_date >= $2
              AND t.transaction_date <= $3
            """,
            user_id, start_date, end_date
        )
        return dict(row)
