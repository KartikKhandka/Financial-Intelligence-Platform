import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import sqlite3
from pathlib import Path

import pandas as pd
from loguru import logger

def calculate_cagr(start_val, end_val, n_years):

    if start_val is None or pd.isna(start_val) or end_val is None or pd.isna(end_val):
        return None, "INSUFFICIENT"

    if start_val == 0:
        return None, "ZERO_BASE"
    elif start_val > 0 and end_val > 0:
        cagr = ((end_val / start_val) ** (1 / n_years) - 1) * 100
        return cagr, None
    elif start_val > 0 and end_val < 0:
        return None, "DECLINE_TO_LOSS"
    elif start_val < 0 and end_val > 0:
        return None, "TURNAROUND"
    elif start_val < 0 and end_val < 0:
        return None, "TURNAROUND"
    else:
        if start_val > 0 and end_val == 0:
            return None, "DECLINE_TO_LOSS"  
        elif start_val < 0 and end_val == 0:
            return None, "TURNAROUND"
        return None, "ZERO_BASE"

def compute_cagr_metrics(db_path: str | None = None):
    from src import config
    db_path = Path(db_path) if db_path else config.DB_PATH
    if not db_path.exists():
        logger.error(f"Database not found at {db_path}")
        return

    logger.info("Computing CAGR metrics...")
    with sqlite3.connect(db_path) as conn:
        query = """
            SELECT p.company_id, p.year, p.sales, p.net_profit, p.eps, fr.fcf
            FROM profitandloss p
            LEFT JOIN financial_ratios fr ON p.company_id = fr.company_id AND p.year = fr.year
        """
        pnl_df = pd.read_sql_query(query, conn)

        pnl_df["year"] = pd.to_numeric(pnl_df["year"], errors="coerce")
        pnl_df = pnl_df.dropna(subset=["year"]).sort_values(by=["company_id", "year"])

        updates = []

        for company_id, group in pnl_df.groupby("company_id"):
            year_dict = group.set_index("year").to_dict(orient="index")

            for current_year in year_dict:
                row_updates = {"company_id": company_id, "year": int(current_year)}
                current_data = year_dict[current_year]

                for n in [3, 5, 10]:
                    start_year = current_year - n

                    if start_year in year_dict:
                        start_data = year_dict[start_year]

                        rev_val, rev_flag = calculate_cagr(
                            start_data.get("sales"), current_data.get("sales"), n
                        )
                        row_updates[f"revenue_cagr_{n}yr"] = rev_val
                        row_updates[f"revenue_cagr_{n}yr_flag"] = rev_flag

                        pat_val, pat_flag = calculate_cagr(
                            start_data.get("net_profit"),
                            current_data.get("net_profit"),
                            n,
                        )
                        row_updates[f"pat_cagr_{n}yr"] = pat_val
                        row_updates[f"pat_cagr_{n}yr_flag"] = pat_flag

                        eps_val, eps_flag = calculate_cagr(
                            start_data.get("eps"), current_data.get("eps"), n
                        )
                        row_updates[f"eps_cagr_{n}yr"] = eps_val
                        row_updates[f"eps_cagr_{n}yr_flag"] = eps_flag
                        if n == 5:
                            fcf_val, _ = calculate_cagr(
                                start_data.get("fcf"), current_data.get("fcf"), 5
                            )
                            row_updates["fcf_cagr_5yr"] = fcf_val
                    else:
                        for metric in ["revenue", "pat", "eps"]:
                            row_updates[f"{metric}_cagr_{n}yr"] = None
                            row_updates[f"{metric}_cagr_{n}yr_flag"] = "INSUFFICIENT"

                if "fcf_cagr_5yr" not in row_updates:
                    row_updates["fcf_cagr_5yr"] = None

                updates.append(row_updates)

        logger.info(f"Updating {len(updates)} rows with CAGR metrics...")

        update_sql = """
            UPDATE financial_ratios 
            SET 
                revenue_cagr_3yr = :revenue_cagr_3yr,
                revenue_cagr_5yr = :revenue_cagr_5yr,
                revenue_cagr_10yr = :revenue_cagr_10yr,
                pat_cagr_3yr = :pat_cagr_3yr,
                pat_cagr_5yr = :pat_cagr_5yr,
                pat_cagr_10yr = :pat_cagr_10yr,
                eps_cagr_3yr = :eps_cagr_3yr,
                eps_cagr_5yr = :eps_cagr_5yr,
                eps_cagr_10yr = :eps_cagr_10yr,
                revenue_cagr_3yr_flag = :revenue_cagr_3yr_flag,
                revenue_cagr_5yr_flag = :revenue_cagr_5yr_flag,
                revenue_cagr_10yr_flag = :revenue_cagr_10yr_flag,
                pat_cagr_3yr_flag = :pat_cagr_3yr_flag,
                pat_cagr_5yr_flag = :pat_cagr_5yr_flag,
                pat_cagr_10yr_flag = :pat_cagr_10yr_flag,
                eps_cagr_3yr_flag = :eps_cagr_3yr_flag,
                eps_cagr_5yr_flag = :eps_cagr_5yr_flag,
                eps_cagr_10yr_flag = :eps_cagr_10yr_flag,
                fcf_cagr_5yr = :fcf_cagr_5yr
            WHERE company_id = :company_id AND year = :year
        """

        conn.executemany(update_sql, updates)
        conn.commit()

    logger.info("CAGR metrics computation complete.")

if __name__ == "__main__":
    compute_cagr_metrics()