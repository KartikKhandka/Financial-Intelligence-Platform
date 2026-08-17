import sqlite3
from pathlib import Path

def optimize_db():
    from src import config
    db_path = config.DB_PATH
    conn = sqlite3.connect(db_path)

    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_pnl_company_year ON profitandloss(company_id, year)",
        "CREATE INDEX IF NOT EXISTS idx_bs_company_year ON balancesheet(company_id, year)",
        "CREATE INDEX IF NOT EXISTS idx_cf_company_year ON cashflow(company_id, year)",
        "CREATE INDEX IF NOT EXISTS idx_fr_company_year ON financial_ratios(company_id, year)",
        "CREATE INDEX IF NOT EXISTS idx_mc_company_year ON market_cap(company_id, year)",
        "CREATE INDEX IF NOT EXISTS idx_docs_company_year ON documents(company_id, year)",
        "CREATE INDEX IF NOT EXISTS idx_sp_company_date ON stock_prices(company_id, date)",
        "CREATE INDEX IF NOT EXISTS idx_sectors_sector ON sectors(broad_sector)",
        "CREATE INDEX IF NOT EXISTS idx_peer_groups_name ON peer_groups(peer_group_name)",
        "CREATE INDEX IF NOT EXISTS idx_peer_perc_group ON peer_percentiles(peer_group_name)"
    ]

    for idx in indexes:
        conn.execute(idx)

    conn.commit()
    conn.close()
    print("Database optimized with indexes.")

if __name__ == "__main__":
    optimize_db()
