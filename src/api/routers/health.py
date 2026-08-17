import sqlite3

from fastapi import APIRouter, Depends

from src.api.database import get_db

router = APIRouter()

@router.get("/")
def health_check(db: sqlite3.Connection = Depends(get_db)):

    tables = [
        "companies",
        "profitandloss",
        "balancesheet",
        "cashflow",
        "analysis",
        "documents",
        "prosandcons",
        "sectors",
        "stock_prices",
        "financial_ratios",
        "peer_groups",
        "market_cap",
        "peer_percentiles",
    ]

    db_row_counts = {}
    for table in tables:
        try:
            count = db.execute(f"SELECT COUNT(*) as count FROM {table}").fetchone()[
                "count"
            ]
            db_row_counts[table] = count
        except Exception:
            db_row_counts[table] = -1

    return {"status": "ok", "db_row_counts": db_row_counts}