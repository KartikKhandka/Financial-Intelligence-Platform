import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from src.api.database import get_db

router = APIRouter()

@router.get("/{ticker}")
def get_market_cap(ticker: str, db: sqlite3.Connection = Depends(get_db)):

    query = """
        SELECT year, pe_ratio as pe, pb_ratio as pb, ev_ebitda, dividend_yield_pct as dividend_yield
        FROM market_cap
        WHERE company_id = ? AND year BETWEEN 2019 AND 2024
        ORDER BY year ASC
    """
    cursor = db.execute(query, (ticker,))
    results = [dict(row) for row in cursor.fetchall()]

    if not results:

        c = db.execute(
            "SELECT 1 FROM companies WHERE company_id = ?", (ticker,)
        ).fetchone()
        if not c:
            raise HTTPException(status_code=404, detail="Company not found")

    return results