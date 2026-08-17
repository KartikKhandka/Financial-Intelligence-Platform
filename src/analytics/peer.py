import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import sqlite3
from pathlib import Path

import pandas as pd
from loguru import logger

def compute_peer_percentiles(db_path: str | None = None, peer_excel: str | None = None):
    from src import config
    db_path = db_path if db_path else str(config.DB_PATH)
    peer_excel = peer_excel if peer_excel else str(config.DATA_DIR / "peer_groups.xlsx")
    """Docstring for compute_peer_percentiles."""
    db_path = Path(db_path)
    peer_excel = Path(peer_excel)

    if not db_path.exists():
        logger.error("DB not found")
        return

    if not peer_excel.exists():
        logger.error(f"Peer groups excel not found at {peer_excel}")
        return

    logger.info("Computing peer percentiles...")

    from src.etl.normaliser import normalize_ticker
    peers_df = pd.read_excel(peer_excel)
    if "company_id" in peers_df.columns:
        peers_df["company_id"] = peers_df["company_id"].apply(normalize_ticker)

    with sqlite3.connect(db_path) as conn:
        query = """
        SELECT 
            company_id, year,
            return_on_equity_pct as roe,
            roce,
            net_profit_margin_pct as npm,
            debt_to_equity as de,
            free_cash_flow_cr as fcf,
            pat_cagr_5yr,
            revenue_cagr_5yr,
            eps_cagr_5yr,
            interest_coverage as icr,
            asset_turnover
        FROM financial_ratios
        WHERE year = 2024
        """
        data_df = pd.read_sql_query(query, conn)

        df = data_df.merge(peers_df, on="company_id", how="left")

        no_peer = df[df["peer_group_name"].isna()]
        if not no_peer.empty:
            for cid in no_peer["company_id"]:
                logger.info(f"[{cid}] No peer group assigned")

        df = df.dropna(subset=["peer_group_name"])

        metrics = {
            "ROE": "roe",
            "ROCE": "roce",
            "Net Profit Margin": "npm",
            "D/E": "de",
            "FCF": "fcf",
            "PAT CAGR 5yr": "pat_cagr_5yr",
            "Revenue CAGR 5yr": "revenue_cagr_5yr",
            "EPS CAGR 5yr": "eps_cagr_5yr",
            "Interest Coverage": "icr",
            "Asset Turnover": "asset_turnover",
        }

        updates = []

        for peer_group, group in df.groupby("peer_group_name"):
            for nice_name, col_name in metrics.items():
                if col_name in group.columns:
                    ranks = group[col_name].rank(pct=True, na_option="keep")

                    if nice_name == "D/E":
                        ranks = 1.0 - ranks

                    for idx, rank_val in ranks.items():
                        if pd.notna(rank_val):
                            company_id = group.loc[idx, "company_id"]
                            year = group.loc[idx, "year"]
                            val = group.loc[idx, col_name]

                            updates.append(
                                {
                                    "company_id": company_id,
                                    "peer_group_name": peer_group,
                                    "metric": nice_name,
                                    "value": val,
                                    "percentile_rank": rank_val,
                                    "year": int(year),
                                }
                            )

        conn.execute("DELETE FROM peer_percentiles WHERE year = 2024")

        logger.info(f"Inserting {len(updates)} peer percentiles into DB...")
        insert_sql = """
            INSERT INTO peer_percentiles (company_id, peer_group_name, metric, value, percentile_rank, year)
            VALUES (:company_id, :peer_group_name, :metric, :value, :percentile_rank, :year)
        """
        conn.executemany(insert_sql, updates)
        conn.commit()

    logger.info("Peer percentile ranking complete.")

if __name__ == "__main__":
    compute_peer_percentiles()