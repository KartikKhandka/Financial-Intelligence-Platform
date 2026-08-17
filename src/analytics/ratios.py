import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import sqlite3
from pathlib import Path

import pandas as pd
from loguru import logger

def calc_net_profit_margin(net_profit, sales):

    return (net_profit / sales * 100) if sales else None

def calc_operating_profit_margin(operating_profit, sales):

    return (operating_profit / sales * 100) if sales else None

def calc_roe(net_profit, equity_capital, reserves):

    equity = equity_capital + reserves
    return (net_profit / equity * 100) if equity > 0 else None

def calc_roce(ebit, equity_capital, reserves, borrowings):

    ce = equity_capital + reserves + borrowings
    return (ebit / ce * 100) if ce > 0 else None

def calc_roa(net_profit, total_assets):

    return (net_profit / total_assets * 100) if total_assets else None

def calc_debt_to_equity(borrowings, equity_capital, reserves):

    equity = equity_capital + reserves
    if equity <= 0:
        return 0.0 if borrowings == 0 else None
    return borrowings / equity

def calc_high_leverage_flag(debt_to_equity, broad_sector):

    if (
        debt_to_equity is not None
        and debt_to_equity > 5
        and broad_sector != "Financials"
    ):
        return 1
    return 0

def calc_icr(ebit, interest):

    return (ebit / interest) if interest else None

def calc_icr_label(icr):

    return "Debt Free" if icr is None else None

def calc_icr_warning_flag(icr):

    return 1 if (icr is not None and icr < 1.5) else 0

def calc_net_debt(borrowings, investments):

    return borrowings - investments

def calc_asset_turnover(sales, total_assets):

    return (sales / total_assets) if total_assets else None

def compute_ratios(db_path: str | None = None):

    from src import config
    db_path = Path(db_path) if db_path else config.DB_PATH
    if not db_path.exists():
        logger.error(f"Database not found at {db_path}")
        return

    logger.info("Computing financial ratios...")
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM financial_ratios")
        conn.commit()

        conn.execute("""
            INSERT INTO financial_ratios (company_id, year)
            SELECT c.company_id, y.year
            FROM companies c
            CROSS JOIN (SELECT DISTINCT year FROM profitandloss WHERE year >= 2012) y
        """)
        conn.commit()

        pnl_df = pd.read_sql_query("SELECT * FROM profitandloss", conn)
        bs_df = pd.read_sql_query("SELECT * FROM balancesheet", conn)
        sectors_df = pd.read_sql_query("SELECT * FROM sectors", conn)
        fr_df = pd.read_sql_query("SELECT * FROM financial_ratios", conn)

        df = pd.merge(
            pnl_df,
            bs_df,
            on=["company_id", "year"],
            how="inner",
            suffixes=("_pnl", "_bs"),
        )

        df = pd.merge(
            df, sectors_df[["company_id", "broad_sector"]], on="company_id", how="left"
        )

        updates = []
        opm_mismatches = 0

        df["_ebit"] = df["operating_profit"] + df["other_income"].fillna(0)
        df["_ce"] = df["equity_capital"] + df["reserves"] + df["borrowings"]
        df["_roce"] = df.apply(
            lambda row: (row["_ebit"] / row["_ce"] * 100) if row["_ce"] > 0 else None,
            axis=1,
        )

        sector_roce_avg = df.groupby("broad_sector")["_roce"].mean().to_dict()

        for idx, row in df.iterrows():
            company_id = row["company_id"]
            year = row["year"]

            sales = row.get("sales", 0)
            net_profit = row.get("net_profit", 0)
            operating_profit = row.get("operating_profit", 0)
            equity_capital = row.get("equity_capital", 0)
            reserves = row.get("reserves", 0)
            borrowings = row.get("borrowings", 0)
            total_assets = row.get("total_assets", 0)
            other_income = row.get("other_income", 0)
            interest = row.get("interest", 0)
            investments = row.get("investments", 0)
            broad_sector = row.get("broad_sector", "")

            ebit = operating_profit + other_income

            net_profit_margin_pct = calc_net_profit_margin(net_profit, sales)
            operating_profit_margin_pct = calc_operating_profit_margin(
                operating_profit, sales
            )

            if operating_profit_margin_pct is not None and pd.notnull(
                row.get("opm_percentage")
            ):
                raw_opm = float(row["opm_percentage"])
                if abs(operating_profit_margin_pct - raw_opm) > 1.0:
                    logger.warning(
                        f"OPM mismatch for {company_id} in {year}: Calculated {operating_profit_margin_pct:.2f}%, Raw {raw_opm:.2f}%"
                    )
                    opm_mismatches += 1

            return_on_equity_pct = calc_roe(net_profit, equity_capital, reserves)
            roce = calc_roce(ebit, equity_capital, reserves, borrowings)
            roa = calc_roa(net_profit, total_assets)

            debt_to_equity = calc_debt_to_equity(borrowings, equity_capital, reserves)
            high_leverage_flag = calc_high_leverage_flag(debt_to_equity, broad_sector)

            interest_coverage = calc_icr(ebit, interest)
            icr_label = calc_icr_label(interest_coverage)
            icr_warning_flag = calc_icr_warning_flag(interest_coverage)

            net_debt_cr = calc_net_debt(borrowings, investments)
            asset_turnover = calc_asset_turnover(sales, total_assets)

            composite_quality_score = None
            quality_components = [
                v
                for v in [roce, return_on_equity_pct, operating_profit_margin_pct]
                if v is not None
            ]
            if quality_components:
                composite_quality_score = sum(quality_components) / len(
                    quality_components
                )

            updates.append(
                {
                    "net_profit_margin_pct": net_profit_margin_pct,
                    "operating_profit_margin_pct": operating_profit_margin_pct,
                    "return_on_equity_pct": return_on_equity_pct,
                    "debt_to_equity": debt_to_equity,
                    "interest_coverage": interest_coverage,
                    "asset_turnover": asset_turnover,
                    "roce": roce,
                    "roa": roa,
                    "high_leverage_flag": high_leverage_flag,
                    "icr_label": icr_label,
                    "icr_warning_flag": icr_warning_flag,
                    "net_debt_cr": net_debt_cr,
                    "free_cash_flow_cr": row.get("fcf"),
                    "capex_cr": row.get("capex_intensity_pct"),
                    "cash_from_operations_cr": row.get("fcf_conversion_rate_pct"),
                    "earnings_per_share": row.get("eps"),
                    "book_value_per_share": (
                        (equity_capital + reserves) / (net_profit / row["eps"])
                        if row.get("eps") and net_profit
                        else None
                    ),
                    "dividend_payout_ratio_pct": (
                        (row.get("dividend_payout", 0) / row.get("eps", 1) * 100)
                        if row.get("eps")
                        else None
                    ),
                    "total_debt_cr": (
                        (borrowings / total_assets) if total_assets else None
                    ),
                    "composite_quality_score": composite_quality_score,
                    "company_id": company_id,
                    "year": year,
                }
            )

        logger.info(f"Updating {len(updates)} rows in financial_ratios table...")
        if opm_mismatches > 0:
            logger.info(f"Total OPM mismatches > 1%: {opm_mismatches}")

        update_sql = """
            UPDATE financial_ratios 
            SET 
                net_profit_margin_pct = :net_profit_margin_pct,
                operating_profit_margin_pct = :operating_profit_margin_pct,
                return_on_equity_pct = :return_on_equity_pct,
                debt_to_equity = :debt_to_equity,
                interest_coverage = :interest_coverage,
                asset_turnover = :asset_turnover,
                roce = :roce,
                roa = :roa,
                high_leverage_flag = :high_leverage_flag,
                icr_label = :icr_label,
                icr_warning_flag = :icr_warning_flag,
                net_debt_cr = :net_debt_cr,
                free_cash_flow_cr = :free_cash_flow_cr,
                capex_cr = :capex_cr,
                cash_from_operations_cr = :cash_from_operations_cr,
                earnings_per_share = :earnings_per_share,
                book_value_per_share = :book_value_per_share,
                dividend_payout_ratio_pct = :dividend_payout_ratio_pct,
                total_debt_cr = :total_debt_cr,
                composite_quality_score = :composite_quality_score
            WHERE company_id = :company_id AND year = :year
        """

        conn.executemany(update_sql, updates)
        conn.commit()

    logger.info("Financial ratios computation complete.")

if __name__ == "__main__":
    compute_ratios()