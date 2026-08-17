from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import csv
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from loguru import logger

from .normaliser import normalize_ticker, normalize_year

FILE_MANIFEST = [
    ("companies.xlsx", "companies", 1, False),
    ("profitandloss.xlsx", "profitandloss", 1, False),
    ("balancesheet.xlsx", "balancesheet", 1, False),
    ("cashflow.xlsx", "cashflow", 1, False),
    ("analysis.xlsx", "analysis", 1, False),
    ("documents.xlsx", "documents", 1, False),
    ("prosandcons.xlsx", "prosandcons", 1, False),
    ("financial_ratios.xlsx", "financial_ratios", 0, True),
    ("market_cap.xlsx", "market_cap", 0, True),
    ("peer_groups.xlsx", "peer_groups", 0, True),
    ("sectors.xlsx", "sectors", 0, True),
    ("stock_prices.xlsx", "stock_prices", 0, True),
]

COLUMN_MAPPINGS: dict[str, dict[str, str]] = {
    "companies": {
        "id": "company_id",
        "company_logo": "company_logo",
        "company_name": "company_name",
        "chart_link": "chart_link",
        "about_company": "about_company",
        "website": "website",
        "nse_profile": "nse_profile",
        "bse_profile": "bse_profile",
        "face_value": "face_value",
        "book_value": "book_value",
        "roce_percentage": "roce_percentage",
        "roe_percentage": "roe_percentage",
    },
    "profitandloss": {
        "id": "id",
        "company_id": "company_id",
        "year": "year",
        "sales": "sales",
        "expenses": "expenses",
        "operating_profit": "operating_profit",
        "opm_percentage": "opm_percentage",
        "other_income": "other_income",
        "interest": "interest",
        "depreciation": "depreciation",
        "profit_before_tax": "profit_before_tax",
        "tax_percentage": "tax_percentage",
        "net_profit": "net_profit",
        "eps": "eps",
        "dividend_payout": "dividend_payout",
    },
    "balancesheet": {
        "id": "id",
        "company_id": "company_id",
        "year": "year",
        "equity_capital": "equity_capital",
        "reserves": "reserves",
        "borrowings": "borrowings",
        "other_liabilities": "other_liabilities",
        "total_liabilities": "total_liabilities",
        "fixed_assets": "fixed_assets",
        "cwip": "cwip",
        "investments": "investments",
        "other_asset": "other_asset",
        "total_assets": "total_assets",
    },
    "cashflow": {
        "id": "id",
        "company_id": "company_id",
        "year": "year",
        "operating_activity": "operating_activity",
        "investing_activity": "investing_activity",
        "financing_activity": "financing_activity",
        "net_cash_flow": "net_cash_flow",
    },
    "analysis": {
        "id": "id",
        "company_id": "company_id",
        "compounded_sales_growth": "compounded_sales_growth",
        "compounded_profit_growth": "compounded_profit_growth",
        "stock_price_cagr": "stock_price_cagr",
        "roe": "roe",
    },
    "documents": {
        "id": "id",
        "company_id": "company_id",
        "Year": "year",
        "Annual_Report": "annual_report",
    },
    "prosandcons": {
        "id": "id",
        "company_id": "company_id",
        "pros": "pros",
        "cons": "cons",
    },
    "sectors": {
        "id": "id",
        "company_id": "company_id",
        "broad_sector": "broad_sector",
        "sub_sector": "sub_sector",
        "index_weight_pct": "index_weight_pct",
        "market_cap_category": "market_cap_category",
    },
    "stock_prices": {
        "id": "id",
        "company_id": "company_id",
        "date": "date",
        "open_price": "open_price",
        "high_price": "high_price",
        "low_price": "low_price",
        "close_price": "close_price",
        "volume": "volume",
        "adjusted_close": "adjusted_close",
    },
    "financial_ratios": {
        "id": "id",
        "company_id": "company_id",
        "year": "year",
        "net_profit_margin_pct": "net_profit_margin_pct",
        "operating_profit_margin_pct": "operating_profit_margin_pct",
        "return_on_equity_pct": "return_on_equity_pct",
        "debt_to_equity": "debt_to_equity",
        "interest_coverage": "interest_coverage",
        "asset_turnover": "asset_turnover",
        "free_cash_flow_cr": "free_cash_flow_cr",
        "capex_cr": "capex_cr",
        "earnings_per_share": "earnings_per_share",
        "book_value_per_share": "book_value_per_share",
        "dividend_payout_ratio_pct": "dividend_payout_ratio_pct",
        "total_debt_cr": "total_debt_cr",
        "cash_from_operations_cr": "cash_from_operations_cr",
    },
    "peer_groups": {
        "id": "id",
        "peer_group_name": "peer_group_name",
        "company_id": "company_id",
        "is_benchmark": "is_benchmark",
    },
    "market_cap": {
        "id": "id",
        "company_id": "company_id",
        "year": "year",
        "market_cap_crore": "market_cap_crore",
        "enterprise_value_crore": "enterprise_value_crore",
        "pe_ratio": "pe_ratio",
        "pb_ratio": "pb_ratio",
        "ev_ebitda": "ev_ebitda",
        "dividend_yield_pct": "dividend_yield_pct",
    },
}

_YEAR_TABLES = {
    "profitandloss",
    "balancesheet",
    "cashflow",
    "financial_ratios",
    "market_cap",
    "documents",
}

_TICKER_TABLES = {
    "profitandloss",
    "balancesheet",
    "cashflow",
    "analysis",
    "documents",
    "prosandcons",
    "sectors",
    "stock_prices",
    "financial_ratios",
    "peer_groups",
    "market_cap",
}

PK_MAPPING = {
    "companies": ["company_id"],
    "profitandloss": ["company_id", "year"],
    "balancesheet": ["company_id", "year"],
    "cashflow": ["company_id", "year"],
    "analysis": ["company_id"],
    "documents": ["company_id", "year"],
    "prosandcons": ["company_id"],
    "sectors": ["company_id"],
    "stock_prices": ["company_id", "date"],
    "financial_ratios": ["company_id", "year"],
    "peer_groups": ["company_id"],
    "market_cap": ["company_id", "year"],
}

class ExcelLoader:

    def __init__(
        self,
        data_dir: str | Path | None = None,
        supplementary_dir: str | Path | None = None,
        output_dir: str | Path | None = None,
    ):
        from src import config
        self.data_dir = Path(data_dir) if data_dir else config.DATA_DIR.parent
        self.supplementary_dir = (
            Path(supplementary_dir)
            if supplementary_dir
            else config.DATA_DIR
        )
        self.output_dir = Path(output_dir) if output_dir else config.OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._audit: list[dict[str, Any]] = []

    def load_file(
        self,
        filepath: str | Path,
        table_name: str,
        header_row: int = 0,
    ) -> pd.DataFrame:

        filepath = Path(filepath)
        logger.info(f"Loading {filepath.name} → {table_name}")

        df = pd.read_excel(filepath, header=header_row, engine="openpyxl")

        df = self._apply_column_mapping(df, table_name)

        df = self.apply_normalisations(df, table_name)

        df = df.dropna(how="all").reset_index(drop=True)

        pk_cols = PK_MAPPING.get(table_name)
        if pk_cols:
            missing_cols = [c for c in pk_cols if c not in df.columns]
            if not missing_cols:
                initial_len = len(df)
                df = df.dropna(subset=pk_cols)
                if len(df) < initial_len:
                    logger.info(
                        f"  Dropped {initial_len - len(df)} rows with NULL PKs from {table_name}"
                    )

                initial_len = len(df)
                df = df.drop_duplicates(subset=pk_cols, keep="first")
                if len(df) < initial_len:
                    logger.info(
                        f"  Dropped {initial_len - len(df)} duplicate rows from {table_name}"
                    )

        df = df.reset_index(drop=True)

        rows_loaded = len(df)
        logger.info(f"  ✓ {table_name}: {rows_loaded} rows loaded")

        self._audit.append(
            {
                "table": table_name,
                "source_file": filepath.name,
                "rows_loaded": rows_loaded,
                "columns": len(df.columns),
                "load_timestamp": datetime.now().isoformat(),
                "status": "OK",
                "rejections": 0,
            }
        )

        return df

    def apply_normalisations(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:

        df = df.copy()

        if table_name in _TICKER_TABLES and "company_id" in df.columns:
            df["company_id"] = df["company_id"].apply(normalize_ticker)

        if table_name == "companies" and "company_id" in df.columns:
            df["company_id"] = df["company_id"].apply(normalize_ticker)

        if table_name in _YEAR_TABLES and "year" in df.columns:
            df["year"] = df["year"].apply(normalize_year)

        return df

    def load_all_files(self) -> dict[str, pd.DataFrame]:

        results: dict[str, pd.DataFrame] = {}

        for filename, table_name, header_row, is_supplementary in FILE_MANIFEST:
            base_dir = self.supplementary_dir if is_supplementary else self.data_dir
            filepath = base_dir / filename

            if not filepath.exists():
                logger.warning(f"  ⚠ File not found: {filepath}")
                self._audit.append(
                    {
                        "table": table_name,
                        "source_file": filename,
                        "rows_loaded": 0,
                        "columns": 0,
                        "load_timestamp": datetime.now().isoformat(),
                        "status": "FILE_NOT_FOUND",
                        "rejections": 0,
                    }
                )
                continue

            try:
                df = self.load_file(filepath, table_name, header_row)
                results[table_name] = df
            except Exception as e:
                logger.error(f"  ✗ Failed to load {filename}: {e}")
                self._audit.append(
                    {
                        "table": table_name,
                        "source_file": filename,
                        "rows_loaded": 0,
                        "columns": 0,
                        "load_timestamp": datetime.now().isoformat(),
                        "status": f"ERROR: {e}",
                        "rejections": 0,
                    }
                )
        if "companies" in results:
            valid_companies = set(results["companies"]["company_id"].dropna().unique())
            for table_name, df in results.items():
                if table_name != "companies" and "company_id" in df.columns:
                    original_len = len(df)
                    filtered_df = df[df["company_id"].isin(valid_companies)].copy()
                    if len(filtered_df) < original_len:
                        logger.info(
                            f"  Dropped {original_len - len(filtered_df)} orphan rows from {table_name}"
                        )

                        for entry in self._audit:
                            if entry["table"] == table_name and entry["status"] == "OK":
                                entry["rejections"] += original_len - len(filtered_df)
                                entry["rows_loaded"] = len(filtered_df)

                    results[table_name] = filtered_df

        self.write_audit()

        return results

    def write_audit(self) -> Path:

        audit_path = self.output_dir / "load_audit.csv"
        if not self._audit:
            logger.info("No audit entries to write.")
            return audit_path

        fieldnames = [
            "table",
            "source_file",
            "rows_loaded",
            "columns",
            "load_timestamp",
            "status",
            "rejections",
        ]

        with open(audit_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self._audit)

        logger.info(f"📋 Audit log written to {audit_path}")
        return audit_path

    def get_column_mapping(self, table_name: str) -> dict[str, str]:

        return COLUMN_MAPPINGS.get(table_name, {})

    def init_db(
        self,
        db_path: str | Path | None = None,
        schema_path: str | Path = "data/schema.sql",
    ) -> None:

        from src import config
        db_path = Path(db_path) if db_path else config.DB_PATH
        schema_path = Path(schema_path)

        db_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initializing database at {db_path}")

        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")

            if schema_path.exists():
                with open(schema_path, "r", encoding="utf-8") as f:
                    schema_sql = f.read()
                conn.executescript(schema_sql)
                logger.info("  ✓ Schema executed successfully")
            else:
                logger.warning(f"  ⚠ Schema file not found: {schema_path}")

    def insert_into_db(
        self, data: dict[str, pd.DataFrame], db_path: str | Path | None = None
    ) -> None:

        from src import config
        db_path = Path(db_path) if db_path else config.DB_PATH
        logger.info(f"Inserting data into database at {db_path}...")

        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")

            for table_name, df in data.items():
                logger.info(f"  Inserting {len(df):>6,} rows into {table_name}...")
                try:
                    df.to_sql(table_name, conn, if_exists="append", index=False)
                except Exception as e:
                    logger.error(f"  ✗ Failed to insert into {table_name}: {e}")
                    raise

            cursor = conn.execute("PRAGMA foreign_key_check;")
            fk_violations = cursor.fetchall()

            if fk_violations:
                logger.error(
                    f"  ✗ FK check failed: {len(fk_violations)} violations found."
                )
                for v in fk_violations[:10]:
                    logger.error(
                        f"    Table: {v[0]}, RowID: {v[1]}, Target: {v[2]}, FK Index: {v[3]}"
                    )
            else:
                logger.info("  ✓ FK check passed (0 violations)")

    def _apply_column_mapping(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:

        mapping = self.get_column_mapping(table_name)
        if not mapping:
            return df

        rename_dict = {}
        for src_col, tgt_col in mapping.items():
            if src_col in df.columns and src_col != tgt_col:
                rename_dict[src_col] = tgt_col

        if rename_dict:
            df = df.rename(columns=rename_dict)

        return df

if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    data_dir = os.environ.get("DATA_DIR", "Dataset")
    supplementary_dir = os.environ.get("SUPPLEMENTARY_DIR", None)
    output_dir = os.environ.get("OUTPUT_DIR", "output")

    loader = ExcelLoader(
        data_dir=data_dir,
        supplementary_dir=supplementary_dir,
        output_dir=output_dir,
    )

    logger.info("Financial Intelligence Platform — Data Loader")

    loader.init_db()

    all_data = loader.load_all_files()
    loader.insert_into_db(all_data)

    logger.info("\n── Summary ──")
    for table, df in all_data.items():
        logger.info(f"  {table:25s} → {len(df):>6,} rows × {len(df.columns)} cols")

    total = sum(len(df) for df in all_data.values())
    logger.info(f"\n  Total: {total:,} rows across {len(all_data)} tables")
    logger.info(" Load complete ")