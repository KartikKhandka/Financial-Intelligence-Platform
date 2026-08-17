import sqlite3

import pandas as pd
from fastapi import APIRouter, Depends

from src.api.database import get_db

router = APIRouter()

@router.get("/stats")
def get_portfolio_stats(db: sqlite3.Connection = Depends(get_db)):

    query = """
        SELECT 
            fr.return_on_equity_pct as roe,
            fr.debt_to_equity as de,
            fr.operating_profit_margin_pct as opm,
            fr.net_profit_margin_pct as npm,
            fr.roce,
            fr.free_cash_flow_cr as fcf,
            mc.pe_ratio as pe,
            mc.pb_ratio as pb,
            mc.ev_ebitda,
            mc.dividend_yield_pct as div_yield
        FROM companies c
        LEFT JOIN (
            SELECT * FROM financial_ratios 
            WHERE (company_id, year) IN (SELECT company_id, MAX(year) FROM financial_ratios GROUP BY company_id)
        ) fr ON c.company_id = fr.company_id
        LEFT JOIN (
            SELECT * FROM market_cap 
            WHERE (company_id, year) IN (SELECT company_id, MAX(year) FROM market_cap GROUP BY company_id)
        ) mc ON c.company_id = mc.company_id
    """
    df = pd.read_sql_query(query, db)

    percentiles = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    stats_df = df.quantile(percentiles).T
    stats_df.columns = [f"P{int(p*100)}" for p in percentiles]

    stats_df = stats_df.where(pd.notnull(stats_df), None)

    results = {}
    for metric, row in stats_df.iterrows():
        results[metric] = row.to_dict()

    return results