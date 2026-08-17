import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src import config
import os

import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

def get_trend_arrow(val_latest, val_prev):

    if pd.isna(val_latest) or pd.isna(val_prev) or val_prev == 0:
        return "<font color='grey'>→</font>"

    change = (val_latest - val_prev) / abs(val_prev)
    if change > 0.02:
        return "<font color='green'>↑</font>"
    elif change < -0.02:
        return "<font color='red'>↓</font>"
    else:
        return "<font color='grey'>→</font>"

def generate_portfolio_summary(output_file: str | None = None):
    output_file = output_file if output_file else str(config.REPORTS_DIR / "portfolio" / "portfolio_summary.pdf")
    """Docstring for generate_portfolio_summary."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    pl = pd.read_excel(config.DATA_DIR / "profitandloss.xlsx", header=1)
    bs = pd.read_excel(config.DATA_DIR / "balancesheet.xlsx", header=1)
    cf = pd.read_excel(config.DATA_DIR / "cashflow.xlsx", header=1)

    try:
        sectors = pd.read_excel(
            config.SUPPLEMENTARY_DIR / "sectors.xlsx",
            header=1,
            names=["idx", "company_id", "sector", "industry", "weight", "cap"],
        )
    except:
        sectors = pd.DataFrame()

    companies = pd.read_excel(config.DATA_DIR / "companies.xlsx", header=1)

    merged = pd.merge(pl, bs, on=["company_id", "year"], suffixes=("_pl", "_bs"))
    merged = pd.merge(
        merged,
        cf[["company_id", "year", "operating_activity", "net_cash_flow"]],
        on=["company_id", "year"],
        how="left",
    )

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

    company_ids = sorted(merged["company_id"].unique())

    doc = SimpleDocTemplate(
        output_file,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
    )
    elements = []
    styles = getSampleStyleSheet()
    header_style = ParagraphStyle(
        "Header", parent=styles["Heading1"], textColor=colors.white, alignment=1
    )

    for cid in company_ids:
        comp_df = merged[merged["company_id"] == cid].sort_values("year")
        if len(comp_df) < 2:
            continue

        latest = comp_df.iloc[-1]
        prev = comp_df.iloc[-2]

        info = companies[companies["id"] == cid]
        name = info.iloc[0]["company_name"] if not info.empty else cid

        sec_info = sectors[sectors["company_id"] == cid]
        sector = sec_info.iloc[0]["sector"] if not sec_info.empty else "Unknown"

        header_text = Paragraph(f"<b>{name} ({cid}) - {sector}</b>", header_style)
        header_table = Table([[header_text]], colWidths=[530])
        header_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.darkblue),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )
        elements.append(header_table)
        elements.append(Spacer(1, 40))

        kpis = [
            ("Revenue (Cr)", latest["sales"], prev["sales"]),
            ("Net Profit (Cr)", latest["net_profit"], prev["net_profit"]),
            ("ROE (%)", latest["roe"], prev["roe"]),
            ("ROCE (%)", latest["roce"], prev["roce"]),
            (
                "Operating CF (Cr)",
                latest["operating_activity"],
                prev["operating_activity"],
            ),
            ("Net Cash Flow (Cr)", latest["net_cash_flow"], prev["net_cash_flow"]),
        ]

        kpi_data = []
        for i in range(0, 6, 2):
            row = []
            for j in range(2):
                if i + j < len(kpis):
                    k_name, l_val, p_val = kpis[i + j]
                    arrow = get_trend_arrow(l_val, p_val)
                    val_str = f"₹{l_val:,.0f}" if "Cr" in k_name else f"{l_val:.1f}%"
                    row.append(
                        Paragraph(
                            f"<b>{k_name}</b><br/>{val_str} {arrow}", styles["Heading2"]
                        )
                    )
                else:
                    row.append("")
            kpi_data.append(row)

        kpi_table = Table(kpi_data, colWidths=[265, 265])
        kpi_table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1, colors.grey),
                    ("INNERGRID", (0, 0), (-1, -1), 1, colors.lightgrey),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 20),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 20),
                ]
            )
        )

        elements.append(kpi_table)
        elements.append(PageBreak())

    doc.build(elements)
    print(f"Generated portfolio summary with {len(company_ids)} companies.")

if __name__ == "__main__":
    generate_portfolio_summary()