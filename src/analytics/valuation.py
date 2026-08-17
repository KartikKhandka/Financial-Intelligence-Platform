import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import os
import sqlite3
import sys

import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src import config
DB_PATH = str(config.DB_PATH)
OUTPUT_DIR = str(config.OUTPUT_DIR)

def get_connection():

    return sqlite3.connect(os.path.abspath(DB_PATH))

def run_valuation():

    print("Running valuation analytics...")
    conn = get_connection()

    companies = pd.read_sql_query(
        "SELECT company_id, company_name FROM companies", conn
    )
    sectors = pd.read_sql_query("SELECT company_id, broad_sector FROM sectors", conn)
    ratios = pd.read_sql_query(
        "SELECT company_id, year, fcf FROM financial_ratios", conn
    )
    market_caps = pd.read_sql_query(
        "SELECT company_id, year, market_cap_crore, pe_ratio, pb_ratio, ev_ebitda FROM market_cap",
        conn,
    )

    conn.close()

    ratios_latest = ratios.sort_values("year").groupby("company_id").tail(1)
    market_caps_latest = market_caps.sort_values("year").groupby("company_id").tail(1)

    mc_5yr = market_caps.sort_values("year").groupby("company_id").tail(5)
    pe_5yr_median = mc_5yr.groupby("company_id")["pe_ratio"].median().reset_index()
    pe_5yr_median.rename(columns={"pe_ratio": "5yr_median_PE"}, inplace=True)

    df = pd.merge(companies, sectors, on="company_id", how="left")
    df = pd.merge(
        df,
        market_caps_latest[
            ["company_id", "market_cap_crore", "pe_ratio", "pb_ratio", "ev_ebitda"]
        ],
        on="company_id",
        how="left",
    )
    df = pd.merge(df, ratios_latest[["company_id", "fcf"]], on="company_id", how="left")
    df = pd.merge(df, pe_5yr_median, on="company_id", how="left")

    df["FCF_yield_pct"] = (df["fcf"] / df["market_cap_crore"]) * 100

    sector_medians = df.groupby("broad_sector")["pe_ratio"].median().reset_index()
    sector_medians.rename(columns={"pe_ratio": "sector_median_pe"}, inplace=True)

    df = pd.merge(df, sector_medians, on="broad_sector", how="left")

    df["PE_vs_sector_median_pct"] = (
        (df["pe_ratio"] - df["sector_median_pe"]) / df["sector_median_pe"]
    ) * 100

    def flag_valuation(row):

        pe = row.get("pe_ratio")
        sec_med = row.get("sector_median_pe")
        if pd.isna(pe) or pd.isna(sec_med) or sec_med == 0:
            return "Fair"  

        if pe > sec_med * 1.5:
            return "Caution"
        elif pe < sec_med * 0.7:
            return "Discount"
        else:
            return "Fair"

    df["flag"] = df.apply(flag_valuation, axis=1)

    out_cols = [
        "company_id",
        "company_name",
        "broad_sector",
        "pe_ratio",
        "pb_ratio",
        "ev_ebitda",
        "FCF_yield_pct",
        "5yr_median_PE",
        "PE_vs_sector_median_pct",
        "flag",
    ]
    df.rename(
        columns={
            "broad_sector": "sector",
            "pe_ratio": "P/E",
            "pb_ratio": "P/B",
            "ev_ebitda": "EV/EBITDA",
        },
        inplace=True,
    )

    summary_df = df[
        [
            "company_id",
            "company_name",
            "sector",
            "P/E",
            "P/B",
            "EV/EBITDA",
            "FCF_yield_pct",
            "5yr_median_PE",
            "PE_vs_sector_median_pct",
            "flag",
        ]
    ]

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    excel_path = os.path.join(OUTPUT_DIR, "valuation_summary.xlsx")
    summary_df.to_excel(excel_path, index=False)
    print(f"Saved {excel_path}")

    flags_df = summary_df[summary_df["flag"].isin(["Caution", "Discount"])]
    csv_path = os.path.join(OUTPUT_DIR, "valuation_flags.csv")
    flags_df.to_csv(csv_path, index=False)
    print(f"Saved {csv_path}")

    print("Valuation module executed successfully.")

if __name__ == "__main__":
    run_valuation()