from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import csv
from pathlib import Path
from typing import Any

import pandas as pd
from loguru import logger

class SchemaValidator:
    def __init__(self, output_dir: str | None = None):
        from src import config
        self.output_dir = Path(output_dir) if output_dir else config.OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.failures: list[dict[str, Any]] = []

    def validate(self, all_data: dict[str, pd.DataFrame]) -> bool:

        self.failures = []
        logger.info("Running Schema Validation (16 DQ Rules)...")

        self._check_pk(all_data, "DQ-01", "companies", ["company_id"])

        pk_year_tables = [
            "profitandloss",
            "balancesheet",
            "cashflow",
            "financial_ratios",
            "market_cap",
            "documents",
        ]
        for table in pk_year_tables:
            self._check_pk(all_data, "DQ-02", table, ["company_id", "year"])

        self._check_pk(all_data, "DQ-03", "stock_prices", ["company_id", "date"])

        pk_company_tables = ["analysis", "sectors", "prosandcons"]
        for table in pk_company_tables:
            self._check_pk(all_data, "DQ-04", table, ["company_id"])

        fk_mapping = {
            "DQ-05": "profitandloss",
            "DQ-06": "balancesheet",
            "DQ-07": "cashflow",
            "DQ-08": "stock_prices",
            "DQ-09": "sectors",
            "DQ-10": "analysis",
            "DQ-11": "financial_ratios",
            "DQ-12": "market_cap",
            "DQ-13": "documents",
        }

        for rule_id, table in fk_mapping.items():
            self._check_fk(all_data, rule_id, table)

        self._check_fk(all_data, "DQ-13", "prosandcons")

        self._check_opm(all_data, "DQ-14")
        self._check_balance(all_data, "DQ-15")
        self._check_sales(all_data, "DQ-16")

        self._write_failures()

        critical_failures = sum(1 for f in self.failures if f["severity"] == "CRITICAL")
        if critical_failures > 0:
            logger.error(
                f"Validation failed with {critical_failures} CRITICAL failures."
            )
            return False

        logger.info(
            f"Validation passed with {len(self.failures)} WARNING(S) and {critical_failures} CRITICAL failures."
        )
        return True

    def _add_failure(
        self, rule_id: str, table: str, severity: str, desc: str, count: int
    ):
        if count > 0:
            self.failures.append(
                {
                    "rule_id": rule_id,
                    "table": table,
                    "severity": severity,
                    "description": desc,
                    "failed_records_count": int(count),
                }
            )

    def _check_pk(
        self,
        all_data: dict[str, pd.DataFrame],
        rule_id: str,
        table: str,
        cols: list[str],
    ):
        if table not in all_data:
            return
        df = all_data[table]

        missing_cols = [c for c in cols if c not in df.columns]
        if missing_cols:
            self._add_failure(
                rule_id,
                table,
                "CRITICAL",
                f"Missing columns for PK check: {missing_cols}",
                1,
            )
            return

        null_count = df[cols].isnull().any(axis=1).sum()
        if null_count > 0:
            self._add_failure(
                rule_id, table, "CRITICAL", f"PK {cols} contains NULLs", null_count
            )

        dup_count = df.duplicated(subset=cols).sum()
        if dup_count > 0:
            self._add_failure(
                rule_id, table, "CRITICAL", f"PK {cols} contains duplicates", dup_count
            )

    def _check_fk(self, all_data: dict[str, pd.DataFrame], rule_id: str, table: str):
        if table not in all_data or "companies" not in all_data:
            return
        df = all_data[table]
        companies_df = all_data["companies"]

        if "company_id" not in df.columns or "company_id" not in companies_df.columns:
            return

        valid_ids = set(companies_df["company_id"].dropna())
        invalid_count = (~df["company_id"].isin(valid_ids)).sum()

        if invalid_count > 0:
            self._add_failure(
                rule_id,
                table,
                "CRITICAL",
                "Orphaned records (invalid company_id)",
                invalid_count,
            )

    def _check_opm(self, all_data: dict[str, pd.DataFrame], rule_id: str):
        table = "profitandloss"
        if table not in all_data:
            return
        df = all_data[table].copy()

        if not all(
            c in df.columns for c in ["sales", "operating_profit", "opm_percentage"]
        ):
            return

        for col in ["sales", "operating_profit", "opm_percentage"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        mask = df["sales"] > 0
        df_valid = df[mask].dropna(
            subset=["sales", "operating_profit", "opm_percentage"]
        )

        calc_opm = (df_valid["operating_profit"] / df_valid["sales"]) * 100
        diff = (df_valid["opm_percentage"] - calc_opm).abs()

        failed_count = (diff > 1.5).sum()  
        if failed_count > 0:
            self._add_failure(
                rule_id,
                table,
                "WARNING",
                "OPM percentage mismatch (>1.5% diff)",
                failed_count,
            )

    def _check_balance(self, all_data: dict[str, pd.DataFrame], rule_id: str):
        table = "balancesheet"
        if table not in all_data:
            return
        df = all_data[table].copy()

        if not all(c in df.columns for c in ["total_liabilities", "total_assets"]):
            return

        df["total_liabilities"] = pd.to_numeric(
            df["total_liabilities"], errors="coerce"
        )
        df["total_assets"] = pd.to_numeric(df["total_assets"], errors="coerce")
        df_valid = df.dropna(subset=["total_liabilities", "total_assets"])

        diff = (df_valid["total_liabilities"] - df_valid["total_assets"]).abs()
        failed_count = (diff > 2.0).sum()
        if failed_count > 0:
            self._add_failure(
                rule_id,
                table,
                "WARNING",
                "Total liabilities != Total assets",
                failed_count,
            )

    def _check_sales(self, all_data: dict[str, pd.DataFrame], rule_id: str):
        table = "profitandloss"
        if table not in all_data:
            return
        df = all_data[table]

        if "sales" not in df.columns:
            return

        sales = pd.to_numeric(df["sales"], errors="coerce")
        failed_count = (sales < 0).sum()
        if failed_count > 0:
            self._add_failure(rule_id, table, "WARNING", "Sales < 0", failed_count)

    def _write_failures(self):
        out_path = self.output_dir / "validation_failures.csv"

        fieldnames = [
            "rule_id",
            "table",
            "severity",
            "description",
            "failed_records_count",
        ]
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.failures)

        logger.info(f"📋 Validation failures written to {out_path}")

if __name__ == "__main__":
    from src.etl.loader import ExcelLoader

    loader = ExcelLoader()
    data = loader.load_all_files()
    validator = SchemaValidator()
    validator.validate(data)