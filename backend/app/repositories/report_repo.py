import asyncpg
from typing import List
from datetime import date


class ReportRepository:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def get_report_data(
        self, user_id: int, start_date: date, end_date: date
    ) -> List[dict]:
        rows = await self.conn.fetch(
            """
            SELECT 
                t.transaction_date,
                w.name AS wallet_name,
                c.name AS category_name,
                t.type,
                t.description,
                t.amount
            FROM transactions t
            JOIN wallets w ON t.wallet_id = w.id
            JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = $1 
              AND t.transaction_date BETWEEN $2 AND $3
            ORDER BY t.transaction_date DESC, t.created_at DESC
            """,
            user_id, start_date, end_date
        )
        return [dict(row) for row in rows]

    async def get_report_summary(
        self, user_id: int, start_date: date, end_date: date
    ) -> dict:
        row = await self.conn.fetchrow(
            """
            SELECT 
                COUNT(*) as total_transactions,
                COALESCE(SUM(CASE WHEN type = 'INCOME' THEN amount ELSE 0 END), 0) as total_income,
                COALESCE(SUM(CASE WHEN type = 'EXPENSE' THEN amount ELSE 0 END), 0) as total_expense
            FROM transactions
            WHERE user_id = $1 
              AND transaction_date BETWEEN $2 AND $3
            """,
            user_id, start_date, end_date
        )
        return dict(row) if row else {"total_transactions": 0, "total_income": 0, "total_expense": 0}
