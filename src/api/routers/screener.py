import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.database import get_db

router = APIRouter()

@router.get("/")
def screener(
    min_roe: float | None = Query(None),
    max_de: float | None = Query(None),
    min_fcf: float | None = Query(None),
    sector: str | None = Query(None),
    min_rev_cagr_5yr: float | None = Query(None),
    min_pat_cagr_5yr: float | None = Query(None),
    max_pe: float | None = Query(None),
    db: sqlite3.Connection = Depends(get_db),
):

    try:

        pass
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid parameter values")

    query = """
        SELECT 
            c.company_id,
            c.company_name,
            s.broad_sector,
            fr.return_on_equity_pct as roe,
            fr.debt_to_equity as de,
            fr.free_cash_flow_cr as fcf,
            fr.revenue_cagr_5yr,
            fr.pat_cagr_5yr,
            mc.pe_ratio as pe
        FROM companies c
        LEFT JOIN sectors s ON c.company_id = s.company_id
        LEFT JOIN (
            SELECT company_id, return_on_equity_pct, debt_to_equity, free_cash_flow_cr, revenue_cagr_5yr, pat_cagr_5yr, MAX(year)
            FROM financial_ratios
            GROUP BY company_id
        ) fr ON c.company_id = fr.company_id
        LEFT JOIN (
            SELECT company_id, pe_ratio, MAX(year)
            FROM market_cap
            GROUP BY company_id
        ) mc ON c.company_id = mc.company_id
        WHERE 1=1
    """
    params = []

    if min_roe is not None:
        query += " AND fr.return_on_equity_pct >= ?"
        params.append(min_roe)
    if max_de is not None:
        query += " AND fr.debt_to_equity <= ?"
        params.append(max_de)
    if min_fcf is not None:
        query += " AND fr.free_cash_flow_cr >= ?"
        params.append(min_fcf)
    if sector is not None:
        query += " AND s.broad_sector = ?"
        params.append(sector)
    if min_rev_cagr_5yr is not None:
        query += " AND fr.revenue_cagr_5yr >= ?"
        params.append(min_rev_cagr_5yr)
    if min_pat_cagr_5yr is not None:
        query += " AND fr.pat_cagr_5yr >= ?"
        params.append(min_pat_cagr_5yr)
    if max_pe is not None:
        query += " AND mc.pe_ratio <= ?"
        params.append(max_pe)

    query += " ORDER BY fr.return_on_equity_pct DESC"

    try:
        cursor = db.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))