import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from scipy.stats import zscore

def load_all_kpis():

    pl = pd.read_excel(config.DATA_DIR / "profitandloss.xlsx", header=1)
    bs = pd.read_excel(config.DATA_DIR / "balancesheet.xlsx", header=1)
    try:
        cf_intel = pd.read_excel(config.OUTPUT_DIR / "cashflow_intelligence.xlsx")
    except Exception:
        cf_intel = pd.DataFrame()
    ratios = pd.read_excel(config.DATA_DIR / "supporting datasets/financial_ratios.xlsx")

    try:
        analysis_raw = pd.read_csv(config.OUTPUT_DIR / "analysis_parsed.csv")
        sales_5y = analysis_raw[
            (analysis_raw["metric_type"] == "compounded_sales_growth")
            & (analysis_raw["period_years"] == 5)
        ].copy()
        sales_5y = sales_5y.rename(columns={"value_pct": "revenue_cagr_5yr"})[
            ["company_id", "revenue_cagr_5yr"]
        ]
    except:
        sales_5y = pd.DataFrame(columns=["company_id", "revenue_cagr_5yr"])

    latest_pl = pl.sort_values("year").groupby("company_id").tail(1)
    latest_bs = bs.sort_values("year").groupby("company_id").tail(1)
    latest_ratios = ratios.sort_values("year").groupby("company_id").tail(1)

    merged = latest_pl[["company_id", "sales", "net_profit"]]
    merged = pd.merge(
        merged,
        latest_ratios[
            [
                "company_id",
                "operating_profit_margin_pct",
                "return_on_equity_pct",
                "debt_to_equity",
            ]
        ],
        on="company_id",
        how="left",
    )
    merged = pd.merge(merged, sales_5y, on="company_id", how="left")
    merged = pd.merge(
        merged,
        cf_intel[
            [
                "company_id",
                "sector",
                "fcf_cagr_5yr",
                "cfo_quality_score",
                "capex_intensity_pct",
                "fcf_conversion_pct",
            ]
        ],
        on="company_id",
        how="left",
    )

    kpi_cols = [
        "sales",
        "net_profit",
        "operating_profit_margin_pct",
        "return_on_equity_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "fcf_cagr_5yr",
        "cfo_quality_score",
        "capex_intensity_pct",
        "fcf_conversion_pct",
    ]

    for col in kpi_cols:
        merged[col] = pd.to_numeric(merged[col], errors="coerce").fillna(0)

    return merged, kpi_cols

def assign_cluster_names():

    from clustering import load_data

    features = [
        "return_on_equity_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "fcf_cagr_5yr",
        "operating_profit_margin_pct",
    ]

    try:
        labels = pd.read_csv(config.OUTPUT_DIR / "cluster_labels.csv")
    except FileNotFoundError:
        labels = pd.DataFrame()
    df = load_data()

    for f in features:
        df[f] = pd.to_numeric(df[f], errors="coerce").fillna(0)

    df = pd.merge(df, labels[["company_id", "cluster_id"]], on="company_id")

    means = df.groupby("cluster_id")[features].mean()

    cluster_names = {}

    clusters = list(means.index)

    hq = means["return_on_equity_pct"].idxmax()
    cluster_names[hq] = "High-Quality Compounders"
    clusters.remove(hq)

    dist = means.loc[clusters, "debt_to_equity"].idxmax()
    cluster_names[dist] = "Distressed or Turnaround"
    clusters.remove(dist)

    eg = means.loc[clusters, "revenue_cagr_5yr"].idxmax()
    cluster_names[eg] = "Emerging Growth"
    clusters.remove(eg)

    defensive = means.loc[clusters, "operating_profit_margin_pct"].idxmax()
    cluster_names[defensive] = "Defensive Dividend Payers"
    clusters.remove(defensive)

    cluster_names[clusters[0]] = "Value Cyclicals"

    print("Cluster Profiling Means:")
    print(means)
    print("\nAssigned Names:")
    for k, v in cluster_names.items():
        print(f"Cluster {k}: {v}")

    labels["cluster_name"] = labels["cluster_id"].map(cluster_names)
    labels.to_csv(config.OUTPUT_DIR / "cluster_labels.csv", index=False)

def run_profiling():

    assign_cluster_names()

    df, kpi_cols = load_all_kpis()

    corr = df[kpi_cols].corr()
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", center=0)
    plt.title("Pearson Correlation Heatmap of 10 KPIs")
    plt.tight_layout()
    os.makedirs(config.REPORTS_DIR, exist_ok=True)
    plt.savefig(config.REPORTS_DIR / "correlation_heatmap.png")
    plt.close()

    outliers = []

    df_sec = df.dropna(subset=["sector"])

    for sector, group in df_sec.groupby("sector"):
        if len(group) < 3:  
            continue

        zscores = group[kpi_cols].apply(zscore)

        is_outlier = (zscores.abs() > 3).any(axis=1)
        outlier_rows = group[is_outlier]
        if not outlier_rows.empty:
            outlier_rows = outlier_rows.copy()
            outlier_rows["outlier_sector"] = sector
            outliers.append(outlier_rows)

    if outliers:
        outlier_df = pd.concat(outliers, ignore_index=True)
        outlier_df.to_csv(config.OUTPUT_DIR / "outlier_report.csv", index=False)
        print(
            f"  Generated outlier report with {len(outlier_df)} rows at {config.OUTPUT_DIR / 'outlier_report.csv'}"
        )
    else:
        pd.DataFrame(columns=["company_id"]).to_csv(
            config.OUTPUT_DIR / "outlier_report.csv", index=False
        )

    stats = []
    for col in kpi_cols:
        series = df[col].dropna()
        if series.empty:
            continue
        stats.append(
            {
                "KPI": col,
                "Mean": series.mean(),
                "Std": series.std(),
                "P10": series.quantile(0.10),
                "P25": series.quantile(0.25),
                "P50": series.quantile(0.50),
                "P75": series.quantile(0.75),
                "P90": series.quantile(0.90),
            }
        )

    stats_df = pd.DataFrame(stats)
    stats_df.to_csv(config.OUTPUT_DIR / "portfolio_stats.csv", index=False)

    print("Cluster profiling and statistics completed.")

if __name__ == "__main__":
    run_profiling()