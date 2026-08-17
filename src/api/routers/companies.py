import sqlite3
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from src.api.database import get_db

router = APIRouter()

@router.get("/", response_model=list[dict])
def get_companies(
    sector: str | None = None,
    market_cap_category: str | None = None,
    search: str | None = None,
    db: sqlite3.Connection = Depends(get_db),
):

    query = """
        SELECT 
            c.company_id as id, 
            c.company_name, 
            s.broad_sector, 
            s.sub_sector, 
            c.roe_percentage as roe_pct, 
            c.roce_percentage as roce_pct
        FROM companies c
        LEFT JOIN sectors s ON c.company_id = s.company_id
        WHERE 1=1
    """
    params = []

    if sector:
        query += " AND s.broad_sector = ?"
        params.append(sector)
    if market_cap_category:
        query += " AND s.market_cap_category = ?"
        params.append(market_cap_category)
    if search:
        query += " AND (c.company_name LIKE ? OR c.company_id LIKE ?)"
        params.append(f"%{search}%")
        params.append(f"%{search}%")

    cursor = db.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]

@router.get("/{ticker}")
def get_company_profile(ticker: str, db: sqlite3.Connection = Depends(get_db)):

    query = """
        SELECT c.*, s.broad_sector, s.sub_sector, s.market_cap_category
        FROM companies c
        LEFT JOIN sectors s ON c.company_id = s.company_id
        WHERE c.company_id = ?
    """
    cursor = db.execute(query, (ticker,))
    company = cursor.fetchone()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    company_dict = dict(company)

    ratios_query = """
        SELECT * FROM financial_ratios 
        WHERE company_id = ? 
        ORDER BY year DESC LIMIT 1
    """
    ratios = db.execute(ratios_query, (ticker,)).fetchone()
    if ratios:
        company_dict.update(
            {
                f"latest_{k}": v
                for k, v in dict(ratios).items()
                if k not in ["id", "company_id", "year"]
            }
        )

    mc_query = """
        SELECT * FROM market_cap 
        WHERE company_id = ? 
        ORDER BY year DESC LIMIT 1
    """
    mc = db.execute(mc_query, (ticker,)).fetchone()
    if mc:
        company_dict.update(
            {
                f"latest_{k}": v
                for k, v in dict(mc).items()
                if k not in ["id", "company_id", "year"]
            }
        )

    return company_dict

@router.get("/{ticker}/pl")
def get_company_pl(
    ticker: str,
    from_year: str | None = None,
    to_year: str | None = None,
    db: sqlite3.Connection = Depends(get_db),
):

    query = "SELECT * FROM profitandloss WHERE company_id = ?"
    params = [ticker]

    if from_year:
        query += " AND year >= ?"
        params.append(int(from_year[:4]))
    if to_year:
        query += " AND year <= ?"
        params.append(int(to_year[:4]))

    query += " ORDER BY year ASC"
    cursor = db.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]

@router.get("/{ticker}/bs")
def get_company_bs(
    ticker: str,
    from_year: str | None = None,
    to_year: str | None = None,
    db: sqlite3.Connection = Depends(get_db),
):

    query = "SELECT * FROM balancesheet WHERE company_id = ?"
    params = [ticker]

    if from_year:
        query += " AND year >= ?"
        params.append(int(from_year[:4]))
    if to_year:
        query += " AND year <= ?"
        params.append(int(to_year[:4]))

    query += " ORDER BY year ASC"
    cursor = db.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]

@router.get("/{ticker}/cashflow")
def get_company_cashflow(
    ticker: str,
    from_year: str | None = None,
    to_year: str | None = None,
    db: sqlite3.Connection = Depends(get_db),
):

    query = "SELECT * FROM cashflow WHERE company_id = ?"
    params = [ticker]

    if from_year:
        query += " AND year >= ?"
        params.append(int(from_year[:4]))
    if to_year:
        query += " AND year <= ?"
        params.append(int(to_year[:4]))

    query += " ORDER BY year ASC"
    cursor = db.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]

@router.get("/{ticker}/ratios")
def get_company_ratios(
    ticker: str, year: int | None = None, db: sqlite3.Connection = Depends(get_db)
):

    query = "SELECT * FROM financial_ratios WHERE company_id = ?"
    params = [ticker]

    if year:
        query += " AND year = ?"
        params.append(year)

    query += " ORDER BY year ASC"
    cursor = db.execute(query, params)

    results = [dict(row) for row in cursor.fetchall()]
    if year and len(results) == 1:
        return results[0]
    return results

@router.get("/{ticker}/tearsheet")
def get_company_tearsheet(ticker: str):

    from src.config import REPORTS_DIR
    pdf_path = REPORTS_DIR / "tearsheets" / f"{ticker}_tearsheet.pdf"

    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Tearsheet not found")

    return FileResponse(
        path=pdf_path, media_type="application/pdf", filename=f"{ticker}_tearsheet.pdf"
    )

@router.get("/{ticker}/peers/compare")
def get_company_peers_compare(ticker: str, db: sqlite3.Connection = Depends(get_db)):

    pg_query = "SELECT peer_group_name FROM peer_groups WHERE company_id = ?"
    pg_row = db.execute(pg_query, (ticker,)).fetchone()

    if not pg_row:
        raise HTTPException(status_code=404, detail="Peer group not found for company")

    peer_group = pg_row["peer_group_name"]

    comp_query = "SELECT metric, value, percentile_rank FROM peer_percentiles WHERE company_id = ? AND peer_group_name = ?"
    comp_data = {
        row["metric"]: dict(row)
        for row in db.execute(comp_query, (ticker, peer_group)).fetchall()
    }

    bm_query = """
        SELECT pp.metric, pp.value, pp.percentile_rank 
        FROM peer_percentiles pp
        JOIN peer_groups pg ON pp.company_id = pg.company_id
        WHERE pg.peer_group_name = ? AND pg.is_benchmark = 1 AND pp.peer_group_name = ?
    """
    bm_data = {
        row["metric"]: dict(row)
        for row in db.execute(bm_query, (peer_group, peer_group)).fetchall()
    }

    avg_query = """
        SELECT metric, AVG(value) as avg_value 
        FROM peer_percentiles 
        WHERE peer_group_name = ?
        GROUP BY metric
    """
    avg_data = {
        row["metric"]: row["avg_value"]
        for row in db.execute(avg_query, (peer_group,)).fetchall()
    }

    metrics = [
        "roe",
        "roce",
        "debt_to_equity",
        "fcf_conversion_rate_pct",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "operating_profit_margin_pct",
        "pe_ratio",
    ]

    radar_data = []
    for m in metrics:
        radar_data.append(
            {
                "metric": m,
                "company_value": comp_data.get(m, {}).get("value"),
                "company_percentile": comp_data.get(m, {}).get("percentile_rank"),
                "benchmark_value": bm_data.get(m, {}).get("value"),
                "benchmark_percentile": bm_data.get(m, {}).get("percentile_rank"),
                "group_average": avg_data.get(m),
            }
        )

    return {
        "company_id": ticker,
        "peer_group_name": peer_group,
        "radar_data": radar_data,
    }