import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from src.api.database import get_db

router = APIRouter()

@router.get("/")
def get_sectors(db: sqlite3.Connection = Depends(get_db)):

    query = """
        SELECT 
            s.broad_sector as sector_name,
            COUNT(DISTINCT c.company_id) as company_count,
            -- SQLite doesn't have MEDIAN built-in, so we might need a workaround or average
            -- But for the API, if median is strictly required we can calculate it in Python.
            AVG(fr.return_on_equity_pct) as avg_roe,
            AVG(mc.pe_ratio) as avg_pe,
            AVG(fr.debt_to_equity) as avg_de
        FROM sectors s
        JOIN companies c ON s.company_id = c.company_id
        LEFT JOIN (
            SELECT company_id, return_on_equity_pct, debt_to_equity, MAX(year)
            FROM financial_ratios GROUP BY company_id
        ) fr ON c.company_id = fr.company_id
        LEFT JOIN (
            SELECT company_id, pe_ratio, MAX(year)
            FROM market_cap GROUP BY company_id
        ) mc ON c.company_id = mc.company_id
        GROUP BY s.broad_sector
    """
    cursor = db.execute(query)
    sectors_data = [dict(row) for row in cursor.fetchall()]

    raw_query = """
        SELECT s.broad_sector, fr.return_on_equity_pct as roe, mc.pe_ratio as pe, fr.debt_to_equity as de
        FROM sectors s
        LEFT JOIN (SELECT company_id, return_on_equity_pct, debt_to_equity, MAX(year) FROM financial_ratios GROUP BY company_id) fr ON s.company_id = fr.company_id
        LEFT JOIN (SELECT company_id, pe_ratio, MAX(year) FROM market_cap GROUP BY company_id) mc ON s.company_id = mc.company_id
    """
    raw_data = [dict(row) for row in db.execute(raw_query).fetchall()]

    import statistics

    grouped_data = {}
    for row in raw_data:
        sector = row["broad_sector"]
        if sector not in grouped_data:
            grouped_data[sector] = {"roe": [], "pe": [], "de": []}
        if row["roe"] is not None:
            grouped_data[sector]["roe"].append(row["roe"])
        if row["pe"] is not None:
            grouped_data[sector]["pe"].append(row["pe"])
        if row["de"] is not None:
            grouped_data[sector]["de"].append(row["de"])

    final_sectors = []
    for sector, counts in grouped_data.items():
        if not sector:
            continue
        final_sectors.append(
            {
                "sector_name": sector,
                "company_count": len(counts["roe"])
                + len(
                    [
                        r
                        for r in raw_data
                        if r["broad_sector"] == sector and r["roe"] is None
                    ]
                ),  
                "median_roe": (
                    statistics.median(counts["roe"]) if counts["roe"] else None
                ),
                "median_pe": statistics.median(counts["pe"]) if counts["pe"] else None,
                "median_de": statistics.median(counts["de"]) if counts["de"] else None,
            }
        )

    counts_query = "SELECT broad_sector, COUNT(DISTINCT company_id) as count FROM sectors GROUP BY broad_sector"
    counts_map = {
        row["broad_sector"]: row["count"]
        for row in db.execute(counts_query).fetchall()
        if row["broad_sector"]
    }

    for s in final_sectors:
        s["company_count"] = counts_map.get(s["sector_name"], 0)

    return final_sectors

@router.get("/{sector}/companies")
def get_companies_in_sector(sector: str, db: sqlite3.Connection = Depends(get_db)):

    query = """
        SELECT c.*, s.broad_sector, s.sub_sector
        FROM companies c
        JOIN sectors s ON c.company_id = s.company_id
        WHERE s.broad_sector = ?
    """
    cursor = db.execute(query, (sector,))
    companies = [dict(row) for row in cursor.fetchall()]

    if not companies:
        raise HTTPException(status_code=404, detail="Sector not found")

    for company in companies:
        ticker = company["company_id"]
        fr = db.execute(
            "SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year DESC LIMIT 1",
            (ticker,),
        ).fetchone()
        if fr:
            company.update(
                {
                    f"latest_{k}": v
                    for k, v in dict(fr).items()
                    if k not in ["id", "company_id", "year"]
                }
            )
    return companies