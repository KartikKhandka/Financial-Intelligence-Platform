import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src import config
import io
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

def load_company_data(company_id):

    pl = pd.read_excel(config.DATA_DIR / "profitandloss.xlsx", header=1)
    bs = pd.read_excel(config.DATA_DIR / "balancesheet.xlsx", header=1)
    cf = pd.read_excel(config.DATA_DIR / "cashflow.xlsx", header=1)
    companies = pd.read_excel(config.DATA_DIR / "companies.xlsx", header=1)

    try:
        intel = pd.read_excel(config.OUTPUT_DIR / "cashflow_intelligence.xlsx")
        pros_cons = pd.read_csv(config.OUTPUT_DIR / "pros_cons_generated.csv")
    except Exception:
        intel = pd.DataFrame()
        pros_cons = pd.DataFrame()

    try:
        analysis = pd.read_csv(config.OUTPUT_DIR / "analysis_parsed.csv")
    except:
        analysis = pd.DataFrame()

    try:
        sectors = pd.read_excel(
            config.SUPPLEMENTARY_DIR / "sectors.xlsx",
            names=["idx", "company_id", "sector", "industry", "weight", "cap"],
        )
    except:
        sectors = pd.DataFrame()

    comp_pl = pl[pl["company_id"] == company_id].sort_values("year")
    comp_bs = bs[bs["company_id"] == company_id].sort_values("year")
    comp_cf = cf[cf["company_id"] == company_id].sort_values("year")
    comp_intel = intel[intel["company_id"] == company_id]
    comp_pc = pros_cons[pros_cons["company_id"] == company_id]
    comp_info = companies[companies["id"] == company_id]

    if comp_pl.empty or comp_bs.empty or comp_info.empty:
        return None

    info = comp_info.iloc[0]
    name = info.get("company_name", company_id).strip()

    merged = pd.merge(comp_pl, comp_bs, on="year", how="inner", suffixes=("_pl", "_bs"))
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

    latest_pl = comp_pl.iloc[-1]

    kpis = {
        "Revenue": f"₹{latest_pl['sales']:,.0f} Cr",
        "Net Profit": f"₹{latest_pl['net_profit']:,.0f} Cr",
        "ROE": f"{merged['roe'].iloc[-1]:.1f}%",
        "ROCE": f"{merged['roce'].iloc[-1]:.1f}%",
    }

    cfo_qual = (
        comp_intel["cfo_quality_label"].iloc[0] if not comp_intel.empty else "N/A"
    )
    alloc = (
        comp_intel["capital_allocation"].iloc[0]
        if not comp_intel.empty and "capital_allocation" in comp_intel.columns
        else "N/A"
    )
    kpis["CFO Quality"] = cfo_qual
    kpis["Allocation"] = alloc

    return {
        "company_id": company_id,
        "name": name,
        "pl": merged,  
        "cf": comp_cf,
        "kpis": kpis,
        "pros": comp_pc[comp_pc["type"].str.lower() == "pro"]["text"].tolist(),
        "cons": comp_pc[comp_pc["type"].str.lower() == "con"]["text"].tolist(),
        "badge": alloc,
    }

def create_rev_profit_chart(df):

    plt.figure(figsize=(6, 4))
    df = df.tail(10)  
    x = np.arange(len(df["year"]))
    width = 0.35

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(x - width / 2, df["sales"], width, label="Revenue", color="#1f77b4")
    ax.bar(x + width / 2, df["net_profit"], width, label="Net Profit", color="#ff7f0e")

    ax.set_xticks(x)
    ax.set_xticklabels(df["year"], rotation=45)
    ax.legend()
    ax.set_title("10-Year Revenue & Net Profit (Cr)")

    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png")
    plt.close("all")
    buf.seek(0)
    return buf

def create_roe_roce_chart(df):

    plt.figure(figsize=(6, 4))
    df = df.tail(10)

    fig, ax1 = plt.subplots(figsize=(6, 4))
    ax2 = ax1.twinx()

    ax1.plot(
        df["year"].astype(str), df["roe"], color="blue", marker="o", label="ROE (%)"
    )
    ax2.plot(
        df["year"].astype(str), df["roce"], color="green", marker="s", label="ROCE (%)"
    )

    ax1.set_ylabel("ROE (%)", color="blue")
    ax2.set_ylabel("ROCE (%)", color="green")
    ax1.set_title("ROE and ROCE")

    fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))

    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png")
    plt.close("all")
    buf.seek(0)
    return buf

def create_bs_stacked_chart(df):

    df = df.tail(10)
    fig, ax = plt.subplots(figsize=(6, 4))

    years = df["year"].astype(str)
    equity = df["equity"]
    borrow = df["borrowings"]
    other_liab = df["other_liabilities"]

    ax.bar(years, equity, label="Equity", color="#2ca02c")
    ax.bar(years, borrow, bottom=equity, label="Borrowings", color="#d62728")
    ax.bar(
        years,
        other_liab,
        bottom=equity + borrow,
        label="Other Liabilities",
        color="#7f7f7f",
    )

    ax.legend()
    ax.set_title("Balance Sheet Composition (Cr)")
    plt.xticks(rotation=45)

    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png")
    plt.close("all")
    buf.seek(0)
    return buf

def create_cf_waterfall(cf_df):

    if cf_df.empty:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.text(0.5, 0.5, "No CF Data", ha="center", va="center")
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        plt.close("all")
        buf.seek(0)
        return buf

    latest = cf_df.iloc[-1]
    labels = ["CFO", "CFI", "CFF", "Net"]
    vals = [
        latest["operating_activity"],
        latest["investing_activity"],
        latest["financing_activity"],
        latest["net_cash_flow"],
    ]

    fig, ax = plt.subplots(figsize=(6, 4))

    starts = [0, vals[0], vals[0] + vals[1], 0]
    colors = ["green" if v > 0 else "red" for v in vals]
    colors[-1] = "blue"  

    for i in range(len(vals)):
        ax.bar(labels[i], vals[i], bottom=starts[i], color=colors[i])

    ax.set_title(f'Cash Flow Waterfall ({latest["year"]})')

    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png")
    plt.close("all")
    buf.seek(0)
    return buf

def generate_tearsheet(company_id: str, output_dir: str | None = None):
    output_dir = output_dir if output_dir else str(config.REPORTS_DIR / "tearsheets")
    """Docstring for generate_tearsheet."""
    data = load_company_data(company_id)
    if not data:
        return False

    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, f"{company_id}_tearsheet.pdf")

    doc = SimpleDocTemplate(
        pdf_path,
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
    header_text = Paragraph(
        f"<b>{data['name']} ({data['company_id']})</b>", header_style
    )
    header_table = Table([[header_text]], colWidths=[530])
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

    kpis = list(data["kpis"].items())
    kpi_data = []
    for i in range(0, 6, 3):
        row = []
        for j in range(3):
            if i + j < len(kpis):
                k, v = kpis[i + j]
                row.append(Paragraph(f"<b>{k}</b><br/>{v}", styles["Normal"]))
            else:
                row.append("")
        kpi_data.append(row)

    kpi_table = Table(kpi_data, colWidths=[176, 176, 176])
    kpi_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, colors.grey),
                ("INNERGRID", (0, 0), (-1, -1), 1, colors.lightgrey),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    elements.append(kpi_table)
    elements.append(Spacer(1, 20))

    rev_buf = create_rev_profit_chart(data["pl"])
    roe_buf = create_roe_roce_chart(data["pl"])

    img1 = Image(rev_buf, width=250, height=200)
    img2 = Image(roe_buf, width=250, height=200)

    chart_table = Table([[img1, img2]], colWidths=[265, 265])
    chart_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    elements.append(chart_table)

    elements.append(PageBreak())

    bs_buf = create_bs_stacked_chart(data["pl"])
    cf_buf = create_cf_waterfall(data["cf"])

    img3 = Image(bs_buf, width=250, height=200)
    img4 = Image(cf_buf, width=250, height=200)

    chart_table2 = Table([[img3, img4]], colWidths=[265, 265])
    chart_table2.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    elements.append(chart_table2)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("<b>Pros</b>", styles["Heading3"]))
    for p in data["pros"]:

        bullet = Paragraph(f"<font color='green'>•</font> {p}", styles["Normal"])
        elements.append(bullet)

    elements.append(Spacer(1, 10))

    elements.append(Paragraph("<b>Cons</b>", styles["Heading3"]))
    for c in data["cons"]:

        bullet = Paragraph(f"<font color='red'>•</font> {c}", styles["Normal"])
        elements.append(bullet)

    elements.append(Spacer(1, 20))

    badge_style = ParagraphStyle(
        "Badge",
        parent=styles["Normal"],
        backColor=colors.lightblue,
        textColor=colors.black,
        alignment=1,
        fontSize=12,
        spaceBefore=10,
        spaceAfter=10,
    )
    elements.append(
        Paragraph(f"<b>Capital Allocation Pattern: {data['badge']}</b>", badge_style)
    )

    doc.build(elements)
    return True

if __name__ == "__main__":
    for comp in ["TCS", "HDFCBANK", "RELIANCE", "SUNPHARMA", "TATASTEEL"]:
        print(f"Generating for {comp}...")
        generate_tearsheet(comp)