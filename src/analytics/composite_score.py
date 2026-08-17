import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import sqlite3
from pathlib import Path

import pandas as pd
from loguru import logger

def winsorize_and_scale(series, invert=False):

    if series.dropna().empty:
        return series

    p10 = series.quantile(0.10)
    p90 = series.quantile(0.90)

    clipped = series.clip(lower=p10, upper=p90)

    if invert:
        clipped = -clipped

    c_min = clipped.min()
    c_max = clipped.max()

    if c_max > c_min:
        scaled = (clipped - c_min) / (c_max - c_min) * 100
    else:
        scaled = pd.Series(50.0, index=series.index)

    return scaled

def compute_composite_scores(db_path: str | None = None):
    from src import config
    db_path = db_path if db_path else str(config.DB_PATH)
    db_path = Path(db_path)
    if not db_path.exists():
        logger.error("DB not found")
        return

    logger.info("Computing sector-relative composite scores...")
    with sqlite3.connect(db_path) as conn:
        query = """
        SELECT 
            fr.company_id, fr.year,
            s.broad_sector,
            fr.return_on_equity_pct as roe,
            fr.roce,
            fr.net_profit_margin_pct as npm,
            fr.fcf_cagr_5yr,
            fr.cfo_quality_score,
            fr.free_cash_flow_cr as fcf,
            fr.revenue_cagr_5yr,
            fr.pat_cagr_5yr,
            fr.debt_to_equity as de,
            fr.interest_coverage as icr
        FROM financial_ratios fr
        LEFT JOIN sectors s ON fr.company_id = s.company_id
        """
        df = pd.read_sql_query(query, conn)

        scaled_dfs = []
        for sector, group in df.groupby("broad_sector"):
            group = group.copy()

            group["roe_score"] = winsorize_and_scale(group["roe"])
            group["roce_score"] = winsorize_and_scale(group["roce"])
            group["npm_score"] = winsorize_and_scale(group["npm"])

            group["fcf_cagr_score"] = winsorize_and_scale(group["fcf_cagr_5yr"])
            group["cfo_pat_score"] = winsorize_and_scale(group["cfo_quality_score"])
            group["fcf_pos_score"] = group["fcf"].apply(
                lambda x: 100.0 if pd.notnull(x) and x > 0 else 0.0
            )

            group["rev_cagr_score"] = winsorize_and_scale(group["revenue_cagr_5yr"])
            group["pat_cagr_score"] = winsorize_and_scale(group["pat_cagr_5yr"])

            group["de_score"] = winsorize_and_scale(group["de"], invert=True)
            group["icr_score"] = winsorize_and_scale(group["icr"])

            score_cols = [
                "roe_score",
                "roce_score",
                "npm_score",
                "fcf_cagr_score",
                "cfo_pat_score",
                "fcf_pos_score",
                "rev_cagr_score",
                "pat_cagr_score",
                "de_score",
                "icr_score",
            ]
            group[score_cols] = group[score_cols].fillna(50.0)

            group["composite"] = (
                (
                    group["roe_score"] * 0.15
                    + group["roce_score"] * 0.10
                    + group["npm_score"] * 0.10
                )  
                + (
                    group["fcf_cagr_score"] * 0.15
                    + group["cfo_pat_score"] * 0.10
                    + group["fcf_pos_score"] * 0.05
                )  
                + (
                    group["rev_cagr_score"] * 0.10 + group["pat_cagr_score"] * 0.10
                )  
                + (group["de_score"] * 0.10 + group["icr_score"] * 0.05)  
            )

            scaled_dfs.append(group)

        final_df = pd.concat(scaled_dfs)

        updates = []
        for _, row in final_df.iterrows():
            updates.append(
                {
                    "composite_quality_score": row["composite"],
                    "company_id": row["company_id"],
                    "year": row["year"],
                }
            )

        logger.info(f"Updating {len(updates)} composite scores in DB...")
        conn.executemany(
            """
            UPDATE financial_ratios
            SET composite_quality_score = :composite_quality_score
            WHERE company_id = :company_id AND year = :year
        """,
            updates,
        )
        conn.commit()

    logger.info("Composite score generation complete.")

if __name__ == "__main__":
    compute_composite_scores()