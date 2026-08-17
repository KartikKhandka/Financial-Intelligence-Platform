import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from math import pi

from src.config import DB_PATH, REPORTS_DIR

def generate_all_radar_charts():
    output_dir = REPORTS_DIR / "radar_charts"
    output_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT c.company_id, c.company_name, 
           r.return_on_equity_pct, r.operating_profit_margin_pct, r.revenue_cagr_5yr, r.pat_cagr_5yr, r.interest_coverage, r.asset_turnover,
           m.pe_ratio, m.pb_ratio
    FROM companies c
    JOIN financial_ratios r ON c.company_id = r.company_id
    LEFT JOIN market_cap m ON c.company_id = m.company_id AND r.year = m.year
    WHERE r.year = (SELECT MAX(year) FROM financial_ratios WHERE company_id = c.company_id)
    """
    df = pd.read_sql(query, conn)
    conn.close()
    features = [
        "return_on_equity_pct", "operating_profit_margin_pct", 
        "revenue_cagr_5yr", "pat_cagr_5yr", 
        "interest_coverage", "asset_turnover", 
        "pe_ratio", "pb_ratio"
    ]
    labels = ["ROE", "OPM", "Rev CAGR", "PAT CAGR", "ICR", "Asset T/O", "P/E", "P/B"]
    for col in features:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        df[col] = df[col].clip(lower=0)
    group_avg = df[features].mean()
    for _, row in df.iterrows():
        company_id = row["company_id"]
        company_name = row["company_name"]
        values = row[features].values
        avg_values = group_avg.values
        norm_values = []
        norm_avg = []
        for i, col in enumerate(features):
            max_val = max(df[col].max(), 0.01)
            norm_values.append(values[i] / max_val * 100)
            norm_avg.append(avg_values[i] / max_val * 100)
        angles = [n / float(len(features)) * 2 * pi for n in range(len(features))]
        angles += angles[:1]
        norm_values += norm_values[:1]
        norm_avg += norm_avg[:1]
        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
        plt.xticks(angles[:-1], labels, color='grey', size=10)
        ax.tick_params(axis='y', labelsize=0) 
        ax.plot(angles, norm_values, linewidth=2, linestyle='solid', label=company_name, color='#8b5cf6')
        ax.fill(angles, norm_values, '#8b5cf6', alpha=0.2)
        ax.plot(angles, norm_avg, linewidth=2, linestyle='solid', label='Group Avg', color='#f59e0b')
        ax.fill(angles, norm_avg, '#f59e0b', alpha=0.15)
        plt.title(f"{company_name} - Radar Chart", size=14, y=1.1)
        plt.legend(loc='upper right', bbox_to_anchor=(1.2, 1.1))
        save_path = output_dir / f"{company_id}_radar.png"
        plt.savefig(save_path, bbox_inches='tight')
        plt.close(fig)

    print(f"Successfully generated {len(df)} radar charts in {output_dir}")

if __name__ == "__main__":
    generate_all_radar_charts()