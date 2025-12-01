from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from datetime import date
from io import BytesIO, StringIO
import csv
import xlsxwriter
import asyncpg

from ..core.database import get_db_conn
from ..core.security import get_current_user
from ..repositories.report_repo import ReportRepository

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/list")
async def get_report_list(
    start_date: date = Query(...),
    end_date: date = Query(...),
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    repo = ReportRepository(conn)
    data = await repo.get_report_data(current_user["id"], start_date, end_date)
    summary = await repo.get_report_summary(current_user["id"], start_date, end_date)
    
    return {
        "transactions": [
            {
                "transaction_date": str(row["transaction_date"]),
                "wallet_name": row["wallet_name"],
                "category_name": row["category_name"],
                "type": row["type"],
                "description": row["description"] or "",
                "amount": float(row["amount"])
            }
            for row in data
        ],
        "summary": {
            "total_transactions": summary["total_transactions"],
            "total_income": float(summary["total_income"]),
            "total_expense": float(summary["total_expense"])
        }
    }


@router.get("/export/csv")
async def export_csv(
    start_date: date = Query(...),
    end_date: date = Query(...),
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    repo = ReportRepository(conn)
    data = await repo.get_report_data(current_user["id"], start_date, end_date)
    
    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["Date", "Wallet", "Category", "Type", "Description", "Amount"])
    
    for row in data:
        writer.writerow([
            row["transaction_date"].strftime("%d/%m/%Y"),
            row["wallet_name"],
            row["category_name"],
            row["type"],
            row["description"] or "",
            float(row["amount"])
        ])
    
    output.seek(0)
    
    filename = f"transactions_{start_date}_{end_date}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/excel")
async def export_excel(
    start_date: date = Query(...),
    end_date: date = Query(...),
    current_user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    repo = ReportRepository(conn)
    data = await repo.get_report_data(current_user["id"], start_date, end_date)
    summary = await repo.get_report_summary(current_user["id"], start_date, end_date)
    
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet("Transactions")
    
    # Formats
    header_format = workbook.add_format({
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'bg_color': '#D9D9D9',
        'border': 1,
        'border_color': '#000000'
    })
    
    date_format = workbook.add_format({
        'num_format': 'dd/mm/yyyy',
        'align': 'center',
        'border': 1
    })
    
    text_format = workbook.add_format({
        'align': 'left',
        'border': 1
    })
    
    text_center_format = workbook.add_format({
        'align': 'center',
        'border': 1
    })
    
    currency_income_format = workbook.add_format({
        'num_format': '_("Rp"* #,##0_);_("Rp"* (#,##0);_("Rp"* "-"_);_(@_)',
        'align': 'right',
        'border': 1,
        'font_color': '#006400'
    })
    
    currency_expense_format = workbook.add_format({
        'num_format': '_("Rp"* #,##0_);_("Rp"* (#,##0);_("Rp"* "-"_);_(@_)',
        'align': 'right',
        'border': 1,
        'font_color': '#8B0000'
    })
    
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 14,
        'align': 'left'
    })
    
    summary_label_format = workbook.add_format({
        'bold': True,
        'align': 'right'
    })
    
    summary_value_format = workbook.add_format({
        'num_format': '_("Rp"* #,##0_);_("Rp"* (#,##0);_("Rp"* "-"_);_(@_)',
        'bold': True
    })
    
    # Title
    worksheet.write(0, 0, f"Transaction Report: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}", title_format)
    
    # Summary
    worksheet.write(2, 0, "Total Income:", summary_label_format)
    worksheet.write(2, 1, float(summary["total_income"]), summary_value_format)
    worksheet.write(3, 0, "Total Expense:", summary_label_format)
    worksheet.write(3, 1, float(summary["total_expense"]), summary_value_format)
    worksheet.write(4, 0, "Net:", summary_label_format)
    worksheet.write(4, 1, float(summary["total_income"]) - float(summary["total_expense"]), summary_value_format)
    
    # Headers
    headers = ["Date", "Wallet", "Category", "Type", "Description", "Amount"]
    header_row = 6
    
    for col, header in enumerate(headers):
        worksheet.write(header_row, col, header, header_format)
    
    # Data
    for row_num, row in enumerate(data, start=header_row + 1):
        worksheet.write(row_num, 0, row["transaction_date"], date_format)
        worksheet.write(row_num, 1, row["wallet_name"], text_format)
        worksheet.write(row_num, 2, row["category_name"], text_format)
        worksheet.write(row_num, 3, row["type"], text_center_format)
        worksheet.write(row_num, 4, row["description"] or "", text_format)
        
        amount_format = currency_income_format if row["type"] == "INCOME" else currency_expense_format
        worksheet.write(row_num, 5, float(row["amount"]), amount_format)
    
    # Column widths
    worksheet.set_column(0, 0, 12)  # Date
    worksheet.set_column(1, 1, 15)  # Wallet
    worksheet.set_column(2, 2, 15)  # Category
    worksheet.set_column(3, 3, 10)  # Type
    worksheet.set_column(4, 4, 30)  # Description
    worksheet.set_column(5, 5, 18)  # Amount
    
    workbook.close()
    output.seek(0)
    
    filename = f"transactions_{start_date}_{end_date}.xlsx"
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
