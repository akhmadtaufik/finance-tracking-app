from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from datetime import date, datetime
from calendar import monthrange
import asyncpg

from ..core.database import get_db_conn
from ..core.security import get_current_user
from ..repositories.analytics_repo import AnalyticsRepository

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/category-breakdown")
async def get_category_breakdown(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    type: Optional[str] = Query("EXPENSE", description="Transaction type: INCOME or EXPENSE"),
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    analytics_repo = AnalyticsRepository(conn)
    
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    trans_type = type.upper() if type else "EXPENSE"
    
    breakdown = await analytics_repo.get_category_breakdown(
        current_user["id"],
        start,
        end,
        trans_type
    )
    
    return [
        {
            "name": item["name"],
            "icon": item["icon"],
            "total": float(item["total"])
        }
        for item in breakdown
    ]


@router.get("/wallet-breakdown")
async def get_wallet_breakdown(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    type: Optional[str] = Query("EXPENSE", description="Transaction type: INCOME or EXPENSE"),
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    analytics_repo = AnalyticsRepository(conn)
    
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    trans_type = type.upper() if type else "EXPENSE"
    
    breakdown = await analytics_repo.get_wallet_breakdown(
        current_user["id"],
        start,
        end,
        trans_type
    )
    
    return [
        {
            "name": item["name"],
            "icon": item["icon"],
            "total": float(item["total"])
        }
        for item in breakdown
    ]


@router.get("/period-summary")
async def get_period_summary(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    analytics_repo = AnalyticsRepository(conn)
    
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    
    summary = await analytics_repo.get_period_summary(
        current_user["id"],
        start,
        end
    )
    
    return {
        "total_income": float(summary["total_income"]),
        "total_expense": float(summary["total_expense"]),
        "transaction_count": summary["transaction_count"],
        "net": float(summary["total_income"] - summary["total_expense"])
    }


@router.get("/daily-totals")
async def get_daily_totals(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    type: Optional[str] = Query("EXPENSE", description="Transaction type: INCOME or EXPENSE"),
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    analytics_repo = AnalyticsRepository(conn)
    
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    trans_type = type.upper() if type else "EXPENSE"
    
    totals = await analytics_repo.get_daily_totals(
        current_user["id"],
        start,
        end,
        trans_type
    )
    
    return [
        {
            "date": item["transaction_date"].isoformat(),
            "total": float(item["total"])
        }
        for item in totals
    ]


@router.get("/trend")
async def get_cash_flow_trend(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    """Get daily income/expense trend for line chart visualization."""
    analytics_repo = AnalyticsRepository(conn)
    
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    
    trend = await analytics_repo.get_cash_flow_trend(
        current_user["id"],
        start,
        end
    )
    
    return [
        {
            "day": item["day"].isoformat(),
            "type": item["type"],
            "total": float(item["total"])
        }
        for item in trend
    ]


@router.get("/comparison")
async def get_monthly_comparison(
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    year: int = Query(..., ge=2000, le=2100, description="Year"),
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    """Compare expenses between selected month and previous month."""
    analytics_repo = AnalyticsRepository(conn)
    
    # Current month range
    current_start = date(year, month, 1)
    current_end = date(year, month, monthrange(year, month)[1])
    
    # Previous month range (handle year rollover)
    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1
    
    prev_start = date(prev_year, prev_month, 1)
    prev_end = date(prev_year, prev_month, monthrange(prev_year, prev_month)[1])
    
    comparison = await analytics_repo.get_monthly_comparison(
        current_user["id"],
        current_start,
        current_end,
        prev_start,
        prev_end
    )
    
    return [
        {
            "category": item["category"],
            "current_total": float(item["current_total"]),
            "prev_total": float(item["prev_total"])
        }
        for item in comparison
    ]
