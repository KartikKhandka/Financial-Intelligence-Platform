import sqlite3
from pathlib import Path

import pandas as pd
import yaml
from loguru import logger

class ScreenerEngine:
    def __init__(
        self, db_path: str | None = None, config_path: str | None = None
    ):
        from src import config
        self.db_path = Path(db_path) if db_path else config.DB_PATH
        self.config_path = Path(config_path) if config_path else Path("config/screener_config.yaml")

        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found at {self.db_path}")

        self.presets = self._load_config()

    def _load_config(self):
        if not self.config_path.exists():
            logger.warning(
                f"Config not found at {self.config_path}. Using empty presets."
            )
            return {}
        with open(self.config_path, "r") as f:
            data = yaml.safe_load(f)
            return data.get("presets", {})

    def get_raw_data(self, target_year=2024):

        query = """
        SELECT
            fr.company_id,
            c.company_name,
            s.broad_sector,
            fr.return_on_equity_pct,
            fr.debt_to_equity,
            fr.free_cash_flow_cr,
            fr.revenue_cagr_5yr,
            fr.revenue_cagr_3yr,
            fr.pat_cagr_5yr,
            fr.operating_profit_margin_pct,
            fr.interest_coverage,
            fr.icr_label,
            fr.eps_cagr_5yr,
            fr.asset_turnover,
            fr.dividend_payout_ratio_pct,
            fr.composite_quality_score,
            mc.pe_ratio,
            mc.pb_ratio,
            mc.dividend_yield_pct,
            mc.market_cap_crore,
            pnl.net_profit,
            pnl.sales
        FROM financial_ratios fr
        JOIN companies c ON fr.company_id = c.company_id
        LEFT JOIN sectors s ON fr.company_id = s.company_id
        LEFT JOIN market_cap mc ON fr.company_id = mc.company_id AND mc.year = fr.year
        LEFT JOIN profitandloss pnl ON fr.company_id = pnl.company_id AND pnl.year = fr.year
        WHERE fr.year = ?
        """
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(query, conn, params=(target_year,))

            prev_year_query = "SELECT company_id, debt_to_equity as prev_de FROM financial_ratios WHERE year = ?"
            prev_df = pd.read_sql_query(
                prev_year_query, conn, params=(target_year - 1,)
            )

        df = df.merge(prev_df, on="company_id", how="left")
        return df

    def run_screener(self, preset_name, custom_filters=None, target_year=2024):

        filters = {}
        if preset_name:
            if preset_name not in self.presets:
                logger.error(f"Preset '{preset_name}' not found.")
                return None
            filters = self.presets[preset_name]

        if custom_filters:
            filters.update(custom_filters)

        df = self.get_raw_data(target_year)

        mask = pd.Series([True] * len(df))

        if "roe_min" in filters:
            mask &= df["return_on_equity_pct"] >= filters["roe_min"]

        if "de_max" in filters:
            de_cond = (df["debt_to_equity"] <= filters["de_max"]) | (
                df["broad_sector"] == "Financials"
            )
            mask &= de_cond

        if "fcf_min" in filters:
            mask &= df["free_cash_flow_cr"] >= filters["fcf_min"]

        if "revenue_cagr_5yr_min" in filters:
            mask &= df["revenue_cagr_5yr"] >= filters["revenue_cagr_5yr_min"]

        if "pat_cagr_5yr_min" in filters:
            mask &= df["pat_cagr_5yr"] >= filters["pat_cagr_5yr_min"]

        if "opm_min" in filters:
            mask &= df["operating_profit_margin_pct"] >= filters["opm_min"]

        if "pe_max" in filters:
            mask &= (df["pe_ratio"] <= filters["pe_max"]) & (df["pe_ratio"] > 0)

        if "pb_max" in filters:
            mask &= df["pb_ratio"] <= filters["pb_max"]

        if "dividend_yield_min" in filters:
            mask &= df["dividend_yield_pct"] >= filters["dividend_yield_min"]

        if "icr_min" in filters:
            icr_cond = (df["interest_coverage"] >= filters["icr_min"]) | (
                df["icr_label"] == "Debt Free"
            )
            mask &= icr_cond

        if "market_cap_min" in filters:
            mask &= df["market_cap_crore"] >= filters["market_cap_min"]

        if "net_profit_min" in filters:
            mask &= df["net_profit"] >= filters["net_profit_min"]

        if "eps_cagr_min" in filters:
            mask &= df["eps_cagr_5yr"] >= filters["eps_cagr_min"]

        if "asset_turnover_min" in filters:
            mask &= df["asset_turnover"] >= filters["asset_turnover_min"]

        if "sales_min" in filters:
            mask &= df["sales"] >= filters["sales_min"]

        if "dividend_payout_max" in filters:
            mask &= df["dividend_payout_ratio_pct"] <= filters["dividend_payout_max"]

        if "revenue_cagr_3yr_min" in filters:
            mask &= df["revenue_cagr_3yr"] >= filters["revenue_cagr_3yr_min"]

        if filters.get("de_declining_yoy"):
            mask &= df["debt_to_equity"] < df["prev_de"]

        filtered_df = df[mask].copy()

        filtered_df = filtered_df.drop(columns=["prev_de"])

        if "composite_quality_score" in filtered_df.columns:
            filtered_df = filtered_df.sort_values(
                by="composite_quality_score", ascending=False
            )

        return filtered_df