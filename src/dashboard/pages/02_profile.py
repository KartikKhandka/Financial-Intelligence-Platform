import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from utils.db import get_companies, get_pl, get_prosandcons, get_ratios, get_sectors
from utils.style import (
    apply_custom_css,
    get_chart_layout_overrides,
    render_con_card,
    render_metric_group,
    render_page_header,
    render_pro_card,
)

st.set_page_config(page_title="Company Profile", layout="wide")
apply_custom_css()

companies_df = get_companies()

if companies_df.empty:
    st.warning("No companies found in database.")
    st.stop()

render_page_header(
    "COMPANY PROFILE",
    "Deep dive into fundamental metrics, financials, and analytical insights.",
)

companies_df["search_label"] = (
    companies_df["company_name"] + " (" + companies_df["company_id"] + ")"
)
search_options = companies_df["search_label"].tolist()

col_search, _ = st.columns([1, 2])
with col_search:
    selected_label = st.selectbox(
        "Search Company", options=[""] + search_options, index=0
    )

if not selected_label:
    st.info("Please select a company to view its profile.")
    st.stop()

ticker = selected_label.split("(")[-1].strip(")")
company_info = companies_df[companies_df["company_id"] == ticker].iloc[0]
sectors_df = get_sectors()
sector_info = sectors_df[sectors_df["company_id"] == ticker]

broad_sector = sector_info.iloc[0]["broad_sector"] if not sector_info.empty else "N/A"
about_text = (
    company_info["about_company"]
    if pd.notnull(company_info["about_company"])
    else "No description available."
)

ratios_df = get_ratios(ticker=ticker).sort_values(by="year", ascending=True)
pl_df = get_pl(ticker)
pros_cons_df = get_prosandcons(ticker)
latest_ratios = ratios_df.iloc[-1] if not ratios_df.empty else pd.Series()

roe = latest_ratios.get("return_on_equity_pct", pd.NA)
mcap = latest_ratios.get(
    "market_cap", "N/A"
)  
fcf = latest_ratios.get("fcf", pd.NA)

header_html = f"""
<div class="company-data-header" style="margin-bottom: 32px; border-bottom: 1px solid rgba(255, 255, 255, 0.05); padding-bottom: 24px;">
    <div>
        <h1 style="font-size: 42px !important; color: #ffffff !important;">{company_info['company_name'].upper()}</h1>
        <div style="color: #9ca3af; font-size: 14px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase;">
            NSE: <span style="color: #ffffff;">{company_info['company_id']}</span> &nbsp;&nbsp;|&nbsp;&nbsp; 
            Sector: <span style="color: #ffffff;">{broad_sector}</span> &nbsp;&nbsp;|&nbsp;&nbsp; 
            Latest FY ROE: <span style="color: #ffffff;">{f"{roe:.1f}%" if pd.notnull(roe) else "N/A"}</span>
        </div>
    </div>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Overview", "Financials", "Analysis"])

with tab1:
    st.markdown("<h2>KEY METRICS</h2>", unsafe_allow_html=True)

    roce = latest_ratios.get("roce", pd.NA)
    npm = latest_ratios.get("net_profit_margin_pct", pd.NA)
    de = latest_ratios.get("debt_to_equity", pd.NA)
    rev_cagr = latest_ratios.get("revenue_cagr_5yr", pd.NA)

    m_group = [
        {"label": "ROE", "value": f"{roe:.1f}%" if pd.notnull(roe) else "N/A"},
        {"label": "ROCE", "value": f"{roce:.1f}%" if pd.notnull(roce) else "N/A"},
        {"label": "NET MARGIN", "value": f"{npm:.1f}%" if pd.notnull(npm) else "N/A"},
        {"label": "D/E RATIO", "value": f"{de:.2f}" if pd.notnull(de) else "N/A"},
        {
            "label": "REV CAGR (5Y)",
            "value": f"{rev_cagr:.1f}%" if pd.notnull(rev_cagr) else "N/A",
        },
        {
            "label": "FREE CASH FLOW",
            "value": f"{fcf:.0f} Cr" if pd.notnull(fcf) else "N/A",
        },
    ]
    render_metric_group(m_group)

    st.markdown("<h2>BUSINESS OVERVIEW</h2>", unsafe_allow_html=True)
    st.markdown(
        f"<div style='color: #d1d5db; font-size: 14px; line-height: 1.8; max-width: 900px; padding: 24px; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px;'>{about_text}</div>",
        unsafe_allow_html=True,
    )

with tab2:
    st.markdown("<h2>REVENUE & PROFITABILITY TREND (10Y)</h2>", unsafe_allow_html=True)
    if not pl_df.empty:
        fig1 = go.Figure()
        fig1.add_trace(
            go.Bar(
                x=pl_df["year"],
                y=pl_df["sales"],
                name="Revenue",
                marker_color="#8b5cf6",
            )
        )
        fig1.add_trace(
            go.Bar(
                x=pl_df["year"],
                y=pl_df["net_profit"],
                name="Net Profit",
                marker_color="#10b981",
            )
        )

        fig1.update_layout(
            **get_chart_layout_overrides(),
            barmode="group",
            showlegend=True,
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )
        st.plotly_chart(fig1, width="stretch", config={"displayModeBar": False})

    st.markdown("<h2>RETURN RATIOS (10Y)</h2>", unsafe_allow_html=True)
    if not ratios_df.empty:
        fig2 = go.Figure()
        fig2.add_trace(
            go.Scatter(
                x=ratios_df["year"],
                y=ratios_df["return_on_equity_pct"],
                name="ROE (%)",
                mode="lines+markers",
                line=dict(color="#8b5cf6", width=3),
                marker=dict(
                    size=8, color="#030712", line=dict(color="#8b5cf6", width=2)
                ),
            )
        )
        fig2.add_trace(
            go.Scatter(
                x=ratios_df["year"],
                y=ratios_df["roce"],
                name="ROCE (%)",
                mode="lines+markers",
                line=dict(color="#8b5cf6", width=3),
                marker=dict(
                    size=8, color="#030712", line=dict(color="#8b5cf6", width=2)
                ),
            )
        )
        fig2.update_layout(
            **get_chart_layout_overrides(),
            showlegend=True,
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )
        st.plotly_chart(fig2, width="stretch", config={"displayModeBar": False})

with tab3:
    st.markdown("<h2>ANALYTICAL SUMMARY</h2>", unsafe_allow_html=True)
    if not pros_cons_df.empty:
        pros_text = pros_cons_df.iloc[0].get("pros", "")
        cons_text = pros_cons_df.iloc[0].get("cons", "")

        col_pro, col_space, col_con = st.columns([1, 0.05, 1])

        with col_pro:
            st.markdown(
                "<div class='analysis-title'>Strengths</div>", unsafe_allow_html=True
            )
            if pd.notnull(pros_text) and pros_text:
                lines = [l.strip() for l in str(pros_text).split("\n") if l.strip()]
                for line in lines:
                    render_pro_card(line)

        with col_con:
            st.markdown(
                "<div class='analysis-title'>Risks & Concerns</div>",
                unsafe_allow_html=True,
            )
            if pd.notnull(cons_text) and cons_text:
                lines = [l.strip() for l in str(cons_text).split("\n") if l.strip()]
                for line in lines:
                    render_con_card(line)
    else:
        st.info("Analysis not available.")