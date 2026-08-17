from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st
from utils.db import get_companies, get_market_caps, get_ratios
from utils.style import (
    apply_custom_css,
    get_chart_layout_overrides,
    render_metric_group,
)

st.set_page_config(page_title="Overview", layout="wide")
apply_custom_css()

header_html = """
<div class="terminal-header" style="margin-bottom: 48px; text-align: center; margin-top: 24px;">
    <div>
        <h1 style="font-size: 64px !important;">FINANCIAL INTELLIGENCE</h1>
        <h1 style="font-size: 64px !important;">PLATFORM.</h1>
        <div style="color: #9ca3af; font-size: 16px; margin: 24px auto 0 auto; max-width: 600px; line-height: 1.6;">
            Welcome to the institutional analytics platform for Nifty 100 constituents. 
            This terminal provides data-dense insights, peer comparisons, fundamental screening, 
            and capital allocation tracking for India's top equities.
        </div>
    </div>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

st.markdown(
    f"""
<div class="terminal-header" style="margin-bottom: 24px; border-top: 1px solid rgba(255, 255, 255, 0.05); padding-top: 32px;">
    <div>
        <h2 style="margin: 0 !important; font-size: 24px !important;">Market Overview</h2>
        <div style="color: #9ca3af; font-size: 12px; margin-top: 4px; letter-spacing: 1px; text-transform: uppercase;">Updated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

ratios = get_ratios()
max_year = int(ratios["year"].max()) if not ratios.empty else 2024
prev_year = max_year - 1

ratios_latest = ratios[ratios["year"] == max_year].set_index("company_id")
ratios_prev = ratios[ratios["year"] == prev_year].set_index("company_id")

mcap = get_market_caps(year=max_year)
companies = get_companies()

total_mcap = mcap["market_cap_crore"].sum() / 100000 if not mcap.empty else 0
median_pe = mcap["pe_ratio"].median() if not mcap.empty else 0
avg_roe = ratios_latest["return_on_equity_pct"].mean() if not ratios_latest.empty else 0

metrics = [
    {
        "label": "NIFTY 100 TOTAL MCAP",
        "value": f"₹{total_mcap:.1f}L Cr",
        "sub": f"FY {max_year} aggregates",
        "sub_class": "neutral",
    },
    {
        "label": "MEDIAN P/E",
        "value": f"{median_pe:.1f}x",
        "sub": "",
        "sub_class": "neutral",
    },
    {
        "label": "AVERAGE ROE",
        "value": f"{avg_roe:.1f}%",
        "sub": "",
        "sub_class": "neutral",
    },
]
render_metric_group(metrics)

st.markdown(
    "<h2>MARKET PERFORMANCE (Aggregated ROE Trend)</h2>", unsafe_allow_html=True
)

if not ratios.empty:
    trend = ratios.groupby("year")["return_on_equity_pct"].mean().reset_index()
    fig = px.area(trend, x="year", y="return_on_equity_pct")
    fig.update_traces(line_color="#8b5cf6", fillcolor="rgba(139, 92, 246, 0.15)")
    fig.update_layout(**get_chart_layout_overrides())
    fig.update_layout(height=250, xaxis_title="", yaxis_title="Average ROE (%)")
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

st.markdown("<h2>MARKET BREADTH (YoY ROE Improvement)</h2>", unsafe_allow_html=True)

advancing = 0
declining = 0
unchanged = 0

for cid in ratios_latest.index:
    if cid in ratios_prev.index:
        curr = ratios_latest.loc[cid, "return_on_equity_pct"]
        prev = ratios_prev.loc[cid, "return_on_equity_pct"]
        if pd.isna(curr) or pd.isna(prev):
            continue
        if curr > prev + 0.5:
            advancing += 1
        elif curr < prev - 0.5:
            declining += 1
        else:
            unchanged += 1

breadth_metrics = [
    {"label": "ADVANCING", "value": str(advancing), "sub_class": "positive"},
    {"label": "DECLINING", "value": str(declining), "sub_class": "negative"},
    {"label": "UNCHANGED", "value": str(unchanged), "sub_class": "neutral"},
]
render_metric_group(breadth_metrics)

col_adv, col_space, col_dec = st.columns([1, 0.1, 1])

if not ratios_latest.empty:
    merged = pd.merge(
        ratios_latest.reset_index(),
        companies[["company_id", "company_name"]],
        on="company_id",
        how="left",
    )

    top_perf = merged.nlargest(10, "pat_cagr_5yr")[["company_name", "pat_cagr_5yr"]]
    top_perf.columns = ["Company", "PAT Growth (5Y)"]

    top_dec = merged.nsmallest(10, "pat_cagr_5yr")[["company_name", "pat_cagr_5yr"]]
    top_dec.columns = ["Company", "PAT Growth (5Y)"]

    with col_adv:
        st.markdown("<h2>TOP PERFORMERS (5Y Growth)</h2>", unsafe_allow_html=True)
        st.dataframe(
            top_perf.style.format({"PAT Growth (5Y)": "{:+.1f}%"}).map(
                lambda x: (
                    "color: #10b981; font-weight: bold; text-shadow: 0 0 10px rgba(16, 185, 129, 0.3);"
                    if isinstance(x, (int, float)) and x > 0
                    else ""
                )
            ),
            width="stretch",
            hide_index=True,
        )

    with col_dec:
        st.markdown("<h2>TOP DECLINERS (5Y Growth)</h2>", unsafe_allow_html=True)
        st.dataframe(
            top_dec.style.format({"PAT Growth (5Y)": "{:+.1f}%"}).map(
                lambda x: (
                    "color: #f43f5e; font-weight: bold; text-shadow: 0 0 10px rgba(244, 63, 94, 0.3);"
                    if isinstance(x, (int, float)) and x < 0
                    else ""
                )
            ),
            width="stretch",
            hide_index=True,
        )