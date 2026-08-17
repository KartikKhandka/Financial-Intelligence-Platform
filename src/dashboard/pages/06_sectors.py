import pandas as pd
import plotly.express as px
import streamlit as st
from utils.db import (
    get_companies,
    get_connection,
    get_market_caps,
    get_ratios,
    get_sectors,
)
from utils.style import apply_custom_css, get_chart_layout_overrides, render_page_header

st.set_page_config(page_title="Sector Analysis", layout="wide")
apply_custom_css()

render_page_header(
    "SECTOR ANALYSIS",
    "Analyze aggregate sector performance, valuation, and constituent details.",
)

@st.cache_data(ttl=600)
def load_sector_data():

    sectors_df = get_sectors()
    companies = get_companies()

    ratios = get_ratios().sort_values("year").groupby("company_id").tail(1)
    market_caps = get_market_caps().sort_values("year").groupby("company_id").tail(1)

    conn = get_connection()
    pl_df = pd.read_sql_query("SELECT company_id, year, sales FROM profitandloss", conn)
    conn.close()

    pl_df = pl_df.sort_values("year").groupby("company_id").tail(1)

    df = pd.merge(
        companies[["company_id", "company_name"]],
        sectors_df[["company_id", "broad_sector", "sub_sector"]],
        on="company_id",
        how="left",
    )
    df = pd.merge(df, pl_df[["company_id", "sales"]], on="company_id", how="left")
    df = pd.merge(
        df,
        ratios[
            [
                "company_id",
                "return_on_equity_pct",
                "debt_to_equity",
                "free_cash_flow_cr",
            ]
        ],
        on="company_id",
        how="left",
    )
    df = pd.merge(
        df,
        market_caps[["company_id", "market_cap_crore", "pe_ratio"]],
        on="company_id",
        how="left",
    )

    return df

df = load_sector_data()

broad_sectors = sorted(df["broad_sector"].dropna().unique().tolist())
if not broad_sectors:
    st.warning("No sector data available.")
    st.stop()

col_sel1, _ = st.columns([1, 3])
with col_sel1:
    selected_sector = st.selectbox("Sector", broad_sectors)

sector_df = df[df["broad_sector"] == selected_sector]

st.markdown(
    "<hr style='margin: 16px 0; border-color: rgba(255, 255, 255, 0.05);'>",
    unsafe_allow_html=True,
)

col_chart, col_table = st.columns([3, 2])

with col_chart:
    st.markdown(
        f"<h3>VALUATION VS RETURN ({selected_sector})</h3>", unsafe_allow_html=True
    )

    bubble_df = sector_df.dropna(
        subset=["sales", "return_on_equity_pct", "market_cap_crore"]
    )
    bubble_df["market_cap_size"] = bubble_df["market_cap_crore"].apply(
        lambda x: max(x, 1)
    )

    if not bubble_df.empty:
        fig = px.scatter(
            bubble_df,
            x="sales",
            y="return_on_equity_pct",
            size="market_cap_size",
            color="sub_sector",
            hover_name="company_name",
            hover_data={
                "market_cap_size": False,
                "market_cap_crore": True,
                "sales": True,
                "return_on_equity_pct": True,
            },
            labels={
                "sales": "Revenue (Cr)",
                "return_on_equity_pct": "ROE (%)",
                "sub_sector": "Sub-Sector",
                "market_cap_crore": "Market Cap (SIMULATED) (Cr)",
            },
            size_max=40,
            color_discrete_sequence=get_chart_layout_overrides()["colorway"],
        )
        fig.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(color="#9ca3af"),
            ),
            height=450,
            **get_chart_layout_overrides(),
        )
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("Insufficient data for visualization.")

with col_table:
    st.markdown("<h3>SECTOR CONSTITUENTS</h3>", unsafe_allow_html=True)

    disp_df = sector_df[
        [
            "company_name",
            "sub_sector",
            "market_cap_crore",
            "pe_ratio",
            "return_on_equity_pct",
        ]
    ].copy()
    disp_df = disp_df.sort_values("market_cap_crore", ascending=False)

    disp_df.columns = ["Company", "Sub-Sector", "Mcap (SIMULATED) (Cr)", "P/E", "ROE (%)"]

    st.dataframe(
        disp_df.style.format(
            {"Mcap (Cr)": "{:,.0f}", "P/E": "{:.1f}", "ROE (%)": "{:.1f}%"}
        ),
        width="stretch",
        hide_index=True,
        height=450,
    )