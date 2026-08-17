import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import os

import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from src import config

def get_latest_metrics():

    pl = pd.read_excel(config.DATA_DIR / "profitandloss.xlsx", header=1)
    bs = pd.read_excel(config.DATA_DIR / "balancesheet.xlsx", header=1)
    try:
        intel = pd.read_excel(config.OUTPUT_DIR / "cashflow_intelligence.xlsx")
    except Exception:
        intel = pd.DataFrame()

    try:
        sectors = pd.read_excel(
            config.DATA_DIR / "supporting datasets/sectors.xlsx",
            header=1,
            names=["idx", "company_id", "sector", "industry", "weight", "cap"],
        )
    except:
        sectors = pd.DataFrame()

    try:
        analysis_raw = pd.read_csv(config.OUTPUT_DIR / "analysis_parsed.csv")
        sales_5y = analysis_raw[
            (analysis_raw["metric_type"] == "compounded_sales_growth")
            & (analysis_raw["period_years"] == 5)
        ].rename(columns={"value_pct": "cagr_5yr_sales"})[
            ["company_id", "cagr_5yr_sales"]
        ]
        profit_5y = analysis_raw[
            (analysis_raw["metric_type"] == "compounded_profit_growth")
            & (analysis_raw["period_years"] == 5)
        ].rename(columns={"value_pct": "cagr_5yr_profit"})[
            ["company_id", "cagr_5yr_profit"]
        ]
        analysis = pd.merge(sales_5y, profit_5y, on="company_id", how="outer")
    except:
        analysis = pd.DataFrame()

    latest_pl = pl.sort_values("year").groupby("company_id").tail(1)
    latest_bs = bs.sort_values("year").groupby("company_id").tail(1)

    merged = pd.merge(latest_pl, latest_bs, on="company_id", suffixes=("_pl", "_bs"))
    merged["equity"] = merged["equity_capital"] + merged["reserves"]
    merged["capital_employed"] = merged["equity"] + merged["borrowings"]

    merged["roe"] = np.where(
        merged["equity"] > 0, merged["net_profit"] / merged["equity"] * 100, 0
    )
    merged["roce"] = np.where(
        merged["capital_employed"] > 0,
        merged["operating_profit"] / merged["capital_employed"] * 100,
        0,
    )

    df = merged[["company_id", "sales", "net_profit", "roe", "roce"]]

    if not sectors.empty:
        df = pd.merge(
            df, sectors[["company_id", "sector"]], on="company_id", how="left"
        )
    else:
        df["sector"] = "Unknown"

    df = pd.merge(
        df,
        intel[["company_id", "cfo_quality_score", "capital_allocation"]],
        on="company_id",
        how="left",
    )

    if not analysis.empty:
        df = pd.merge(
            df,
            analysis[["company_id", "cagr_5yr_sales", "cagr_5yr_profit"]],
            on="company_id",
            how="left",
        )
    else:
        df["cagr_5yr_sales"] = 0
        df["cagr_5yr_profit"] = 0

    return df

def generate_sector_reports(output_dir: str | None = None):
    from src import config
    output_dir = output_dir if output_dir else str(config.REPORTS_DIR / "sector")
    """Docstring for generate_sector_reports."""
    df = get_latest_metrics()
    os.makedirs(output_dir, exist_ok=True)

    sectors = df["sector"].dropna().unique()

    styles = getSampleStyleSheet()
    header_style = ParagraphStyle(
        "Header", parent=styles["Heading1"], textColor=colors.white, alignment=1
    )

    for sector in sectors:
        sector_df = df[df["sector"] == sector]
        if sector_df.empty:
            continue

        pdf_path = os.path.join(
            output_dir, f"{sector.replace('/', '_').replace(' ', '_')}_report.pdf"
        )
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=landscape(A4),
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30,
        )
        elements = []

        header_text = Paragraph(f"<b>{sector} Sector Summary</b>", header_style)
        header_table = Table([[header_text]], colWidths=[750])
        header_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.navy),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )
        elements.append(header_table)
        elements.append(Spacer(1, 20))

        elements.append(Paragraph("<b>Sector Median KPIs</b>", styles["Heading2"]))
        median_data = [
            ["Median ROE (%)", f"{sector_df['roe'].median():.1f}%"],
            ["Median ROCE (%)", f"{sector_df['roce'].median():.1f}%"],
            ["Median Sales (Cr)", f"₹{sector_df['sales'].median():,.0f}"],
            ["Median Net Profit (Cr)", f"₹{sector_df['net_profit'].median():,.0f}"],
        ]

        median_table = Table(median_data, colWidths=[200, 200])
        median_table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1, colors.black),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ]
            )
        )
        elements.append(median_table)
        elements.append(Spacer(1, 30))

        elements.append(Paragraph("<b>Companies in Sector</b>", styles["Heading2"]))

        table_data = [
            [
                "Company ID",
                "Revenue",
                "Net Profit",
                "ROE (%)",
                "ROCE (%)",
                "Sales CAGR(5Y)",
                "CFO Score",
                "Allocation",
            ]
        ]
        for _, row in sector_df.iterrows():
            cagr = row.get("cagr_5yr_sales", "N/A")
            cagr_str = (
                f"{cagr:.1f}%"
                if pd.notnull(cagr) and isinstance(cagr, (int, float))
                else str(cagr)
            )

            cfo = row.get("cfo_quality_score", "N/A")
            cfo_str = f"{cfo:.1f}" if pd.notnull(cfo) else "N/A"

            table_data.append(
                [
                    Paragraph(str(row["company_id"]), styles["Normal"]),
                    Paragraph(f"₹{row['sales']:,.0f}", styles["Normal"]),
                    Paragraph(f"₹{row['net_profit']:,.0f}", styles["Normal"]),
                    Paragraph(f"{row['roe']:.1f}%", styles["Normal"]),
                    Paragraph(f"{row['roce']:.1f}%", styles["Normal"]),
                    Paragraph(cagr_str, styles["Normal"]),
                    Paragraph(cfo_str, styles["Normal"]),
                    Paragraph(
                        str(row.get("capital_allocation", "N/A")), styles["Normal"]
                    ),
                ]
            )

        comp_table = Table(table_data, colWidths=[100, 100, 100, 70, 70, 90, 70, 150])
        comp_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.navy),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOX", (0, 0), (-1, -1), 1, colors.black),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ]
            )
        )
        elements.append(comp_table)

        doc.build(elements)
        print(f"Generated sector report for {sector}")

if __name__ == "__main__":
    generate_sector_reports()