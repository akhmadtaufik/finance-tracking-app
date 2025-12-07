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
              AND LOWER(c.name) <> 'transfer'
            GROUP BY c.id, c.name, c.icon
            HAVING SUM(t.amount) > 0
            ORDER BY total DESC
            """,
            user_id, trans_type, start_date, end_date
        )
        return [dict(row) for row in rows]

    async def get_wallet_breakdown(
        self,
        user_id: int,
        start_date: date,
        end_date: date,
        trans_type: str = "EXPENSE"
    ) -> List[dict]:
        rows = await self.conn.fetch(
            """
            SELECT w.name, w.icon, SUM(t.amount) as total
            FROM transactions t
            JOIN wallets w ON t.wallet_id = w.id
            JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = $1
              AND t.type = $2
              AND t.transaction_date >= $3
              AND t.transaction_date <= $4
              AND LOWER(c.name) <> 'transfer'
            GROUP BY w.id, w.name, w.icon
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
                COALESCE(SUM(CASE WHEN t.type = 'INCOME' AND LOWER(c.name) <> 'transfer' THEN t.amount ELSE 0 END), 0) as total_income,
                COALESCE(SUM(CASE WHEN t.type = 'EXPENSE' AND LOWER(c.name) <> 'transfer' THEN t.amount ELSE 0 END), 0) as total_expense,
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

    async def get_cash_flow_trend(
        self,
        user_id: int,
        start_date: date,
        end_date: date
    ) -> List[dict]:
        """Fetch daily totals for Income and Expense, excluding Transfer category."""
        rows = await self.conn.fetch(
            """
            SELECT 
                t.transaction_date::DATE as day, 
                t.type, 
                SUM(t.amount) as total
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = $1
              AND t.transaction_date >= $2
              AND t.transaction_date <= $3
              AND LOWER(c.name) <> 'transfer'
            GROUP BY day, t.type
            ORDER BY day ASC
            """,
            user_id, start_date, end_date
        )
        return [dict(row) for row in rows]

    async def get_monthly_comparison(
        self,
        user_id: int,
        current_start: date,
        current_end: date,
        prev_start: date,
        prev_end: date
    ) -> List[dict]:
        """Compare expenses between two months using FILTER clause."""
        rows = await self.conn.fetch(
            """
            SELECT 
                c.name as category,
                COALESCE(SUM(t.amount) FILTER (
                    WHERE t.transaction_date >= $2 AND t.transaction_date <= $3
                ), 0) as current_total,
                COALESCE(SUM(t.amount) FILTER (
                    WHERE t.transaction_date >= $4 AND t.transaction_date <= $5
                ), 0) as prev_total
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = $1
              AND t.type = 'EXPENSE'
              AND LOWER(c.name) <> 'transfer'
              AND (
                  (t.transaction_date >= $2 AND t.transaction_date <= $3) OR
                  (t.transaction_date >= $4 AND t.transaction_date <= $5)
              )
            GROUP BY c.name
            HAVING 
                SUM(t.amount) FILTER (WHERE t.transaction_date >= $2 AND t.transaction_date <= $3) > 0 OR
                SUM(t.amount) FILTER (WHERE t.transaction_date >= $4 AND t.transaction_date <= $5) > 0
            ORDER BY current_total DESC
            """,
            user_id, current_start, current_end, prev_start, prev_end
        )
        return [dict(row) for row in rows]
