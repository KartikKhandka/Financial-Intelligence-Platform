import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import os
import sqlite3

import pandas as pd

def parse_analysis_file():

    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    dataset_path = os.path.join(base_dir, "Dataset", "analysis.xlsx")
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    print("Loading analysis.xlsx...")
    df = pd.read_excel(dataset_path, header=1)

    target_cols = [
        "compounded_sales_growth",
        "compounded_profit_growth",
        "stock_price_cagr",
        "roe",
    ]
    for col in target_cols:
        if col not in df.columns:
            print(f"Warning: Column {col} not found in analysis.xlsx")

    df_melt = df.melt(
        id_vars=["company_id"],
        value_vars=[c for c in target_cols if c in df.columns],
        var_name="metric_type",
        value_name="original_text",
    )

    df_melt = df_melt.dropna(subset=["original_text"]).copy()

    df_melt["original_text"] = df_melt["original_text"].astype(str).str.strip()

    df_melt = df_melt[df_melt["original_text"] != "nan"]

    pattern = r"(\d+)\s*Years?:?\s*([\d.]+)%"
    extracted = df_melt["original_text"].str.extract(pattern)

    df_melt["period_years"] = extracted[0]
    df_melt["value_pct"] = extracted[1]

    failures_mask = df_melt["period_years"].isna()
    failures_df = df_melt[failures_mask][["company_id", "metric_type", "original_text"]]

    success_df = df_melt[~failures_mask].copy()
    success_df["period_years"] = success_df["period_years"].astype(int)
    success_df["value_pct"] = success_df["value_pct"].astype(float)

    failures_path = os.path.join(output_dir, "parse_failures.csv")
    failures_df.to_csv(failures_path, index=False)
    print(f"Saved {len(failures_df)} failures to {failures_path}")

    success_path = os.path.join(output_dir, "analysis_parsed.csv")
    success_df[["company_id", "metric_type", "period_years", "value_pct"]].to_csv(
        success_path, index=False
    )
    print(f"Saved {len(success_df)} parsed metrics to {success_path}")

    return success_df

def cross_validate(parsed_df):

    from src import config
    print("Starting cross-validation against nifty100.db...")
    db_path = config.DB_PATH

    if not os.path.exists(db_path):
        print("Database not found, skipping cross-validation.")
        return

    conn = sqlite3.connect(db_path)

    query = """
    SELECT company_id, 
           revenue_cagr_3yr, revenue_cagr_5yr, revenue_cagr_10yr,
           pat_cagr_3yr, pat_cagr_5yr, pat_cagr_10yr
    FROM financial_ratios 
    WHERE year = (SELECT MAX(year) FROM financial_ratios)
    """
    db_df = pd.read_sql_query(query, conn)
    conn.close()

    db_melt = db_df.melt(
        id_vars=["company_id"], var_name="db_metric_col", value_name="computed_value"
    )

    mapping = {
        ("compounded_sales_growth", 3): "revenue_cagr_3yr",
        ("compounded_sales_growth", 5): "revenue_cagr_5yr",
        ("compounded_sales_growth", 10): "revenue_cagr_10yr",
        ("compounded_profit_growth", 3): "pat_cagr_3yr",
        ("compounded_profit_growth", 5): "pat_cagr_5yr",
        ("compounded_profit_growth", 10): "pat_cagr_10yr",
    }

    def map_to_db_col(row):

        key = (row["metric_type"], row["period_years"])
        return mapping.get(key, None)

    parsed_df["db_metric_col"] = parsed_df.apply(map_to_db_col, axis=1)

    validation_subset = parsed_df.dropna(subset=["db_metric_col"]).copy()

    if validation_subset.empty:
        print("No metrics available for cross-validation.")
        return

    merged = pd.merge(
        validation_subset, db_melt, on=["company_id", "db_metric_col"], how="left"
    )

    merged = merged.dropna(subset=["computed_value"]).copy()
    merged["divergence"] = (merged["value_pct"] - merged["computed_value"]).abs()

    divergences = merged[merged["divergence"] > 5.0].copy()

    output_dir = os.path.join(base_dir, "output")
    div_path = os.path.join(output_dir, "cagr_divergences.csv")
    divergences.to_csv(div_path, index=False)

    print(
        f"Cross-validation complete. Found {len(divergences)} divergences > 5%. Saved to {div_path}"
    )
    if not divergences.empty:
        print(
            divergences[
                [
                    "company_id",
                    "metric_type",
                    "period_years",
                    "value_pct",
                    "computed_value",
                    "divergence",
                ]
            ].head()
        )

if __name__ == "__main__":
    parsed_data = parse_analysis_file()
    cross_validate(parsed_data)