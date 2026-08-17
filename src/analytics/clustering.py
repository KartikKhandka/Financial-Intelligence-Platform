import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src import config
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

def load_data():

    companies = pd.read_excel(config.DATA_DIR / "companies.xlsx", header=1)
    if "id" in companies.columns:
        valid_companies = companies["id"].unique()
    else:
        valid_companies = companies["company_id"].unique()

    try:
        cf_intel = pd.read_excel(config.OUTPUT_DIR / "cashflow_intelligence.xlsx")
    except FileNotFoundError:
        cf_intel = pd.DataFrame()

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

    ratios = pd.read_excel(config.SUPPLEMENTARY_DIR / "financial_ratios.xlsx")

    latest_ratios = ratios.sort_values("year").groupby("company_id").tail(1)

    cols_needed = [
        "company_id",
        "return_on_equity_pct",
        "debt_to_equity",
        "operating_profit_margin_pct",
    ]
    latest_ratios = latest_ratios[
        [c for c in cols_needed if c in latest_ratios.columns]
    ]

    df = pd.DataFrame({"company_id": valid_companies})
    df = pd.merge(
        df,
        cf_intel[["company_id", "sector", "fcf_cagr_5yr"]],
        on="company_id",
        how="left",
    )
    df = pd.merge(df, sales_5y, on="company_id", how="left")
    df = pd.merge(df, latest_ratios, on="company_id", how="left")

    return df

def run_clustering():

    df = load_data()
    features = [
        "return_on_equity_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "fcf_cagr_5yr",
        "operating_profit_margin_pct",
    ]

    for f in features:
        if f not in df.columns:
            df[f] = np.nan

    for f in features:
        df[f] = df[f].fillna(pd.to_numeric(df[f], errors="coerce"))  
        df[f] = df.groupby("sector")[f].transform(lambda x: x.fillna(x.median()))

        df[f] = df[f].fillna(df[f].median())
        df[f] = df[f].fillna(0)  

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[features])

    os.makedirs("reports", exist_ok=True)
    inertias = []
    K_range = range(2, 11)
    for k in K_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X_scaled)
        inertias.append(km.inertia_)

    plt.figure(figsize=(8, 5))
    plt.plot(K_range, inertias, "bo-")
    plt.xlabel("Number of clusters (k)")
    plt.ylabel("Inertia")
    plt.title("Elbow Plot for KMeans Clustering")
    plt.grid(True)
    plt.savefig(config.REPORTS_DIR / "elbow_plot.png")
    plt.close()

    kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X_scaled)

    centroids = kmeans.cluster_centers_
    distances = [
        np.linalg.norm(X_scaled[i] - centroids[clusters[i]])
        for i in range(len(X_scaled))
    ]

    df["cluster_id"] = clusters
    df["distance_from_centroid"] = distances

    df["cluster_name"] = "Cluster " + df["cluster_id"].astype(str)

    output_cols = ["company_id", "cluster_id", "cluster_name", "distance_from_centroid"]
    os.makedirs("output", exist_ok=True)
    df[output_cols].to_csv(config.OUTPUT_DIR / "cluster_labels.csv", index=False)

    print("Clustering completed. Elbow plot and labels saved.")

if __name__ == "__main__":
    run_clustering()