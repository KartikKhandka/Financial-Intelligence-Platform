import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import sqlite3

import pandas as pd

def generate_edge_cases_log():

    from src import config
    conn = sqlite3.connect(config.DB_PATH)

    fr_2024 = pd.read_sql_query(
        "SELECT company_id, roce, return_on_equity_pct FROM financial_ratios WHERE year = 2024",
        conn,
    )

    companies_db = pd.read_sql_query(
        "SELECT company_id, roce_percentage, roe_percentage FROM companies", conn
    )

    sectors = pd.read_sql_query("SELECT company_id, broad_sector FROM sectors", conn)

    conn.close()

    df = fr_2024.merge(companies_db, on="company_id", how="inner").merge(
        sectors, on="company_id", how="left"
    )

    log_entries = []

    for _, row in df.iterrows():
        company = row["company_id"]
        sector = row["broad_sector"]

        if sector == "Financials":
            calc_roce = row["roce"]
            excel_roce = row["roce_percentage"]

            if pd.notnull(calc_roce) and pd.notnull(excel_roce):
                diff = abs(calc_roce - excel_roce)
                if diff > 2.0:
                    log_entries.append(
                        f"[{company}] FINANCIAL_ROCE_MISMATCH: Calculated ROCE ({calc_roce:.2f}%) differs from companies.xlsx ({excel_roce:.2f}%) by {diff:.2f}%. "
                        f"Explanation: Financial institutions have different capital structures where debt is raw material, skewing standard ROCE."
                    )

        calc_roe = row["return_on_equity_pct"]
        excel_roe = row["roe_percentage"]

        if pd.notnull(calc_roe) and pd.notnull(excel_roe):
            diff = abs(calc_roe - excel_roe)
            if diff > 2.0:
                log_entries.append(
                    f"[{company}] ROE_MISMATCH: Calculated ROE ({calc_roe:.2f}%) differs from companies.xlsx ({excel_roe:.2f}%) by {diff:.2f}%. "
                    f"Explanation: Discrepancy may be due to adjustments in comprehensive income or differences in trailing 12M vs annual filings."
                )

    log_path = config.OUTPUT_DIR / "ratio_edge_cases.log"
    with open(log_path, "w") as f:
        f.write("\n".join(log_entries))
    print(f"Generated {log_path} with {len(log_entries)} entries")

if __name__ == "__main__":
    generate_edge_cases_log()