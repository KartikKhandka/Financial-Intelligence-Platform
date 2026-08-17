import pandas as pd
import plotly.express as px
import streamlit as st
from utils.db import get_companies, get_market_caps, get_ratios, get_sectors, get_master_dataframe
from utils.style import apply_custom_css, get_chart_layout_overrides, render_page_header

st.set_page_config(page_title="Capital Allocation", layout="wide")
apply_custom_css()

render_page_header(
    "CAPITAL ALLOCATION MAP",
    "Nifty 100 constituents grouped by dynamically derived capital allocation patterns.",
)

df = get_master_dataframe()

def categorize_pattern(row):

    dy = row.get("dividend_yield_pct", 0)
    dy = dy if pd.notna(dy) else 0
    fcf = row.get("free_cash_flow_cr", 0)
    fcf = fcf if pd.notna(fcf) else 0
    fcf_conv = row.get("fcf_conversion_rate_pct", 0)
    fcf_conv = fcf_conv if pd.notna(fcf_conv) else 0
    capex_int = row.get("capex_intensity_pct", 0)
    capex_int = capex_int if pd.notna(capex_int) else 0
    de = row.get("debt_to_equity", 0)
    de = de if pd.notna(de) else 0
    icr = row.get("interest_coverage", 100)
    icr = icr if pd.notna(icr) else 100
    rev_cagr = row.get("revenue_cagr_5yr", 0)
    rev_cagr = rev_cagr if pd.notna(rev_cagr) else 0

    if dy > 3.0:
        return "High Dividend"
    elif fcf > 1000 and fcf_conv > 80:
        return "Cash Cow"
    elif capex_int > 15:
        return "Capex Heavy"
    elif de > 2.0 and icr < 3:
        return "Debt Burdened"
    elif de < 0.2 and fcf > 500:
        return "Debt Free/Repayer"
    elif rev_cagr > 15 and dy < 1.0:
        return "High Growth"
    elif fcf_conv > 50 and dy > 1.0 and capex_int < 10:
        return "Balanced"
    else:
        return "Standard"

df["Allocation Pattern"] = df.apply(categorize_pattern, axis=1)

df["market_cap_size"] = df["market_cap_crore"].fillna(100).apply(lambda x: max(x, 100))
df["market_cap_crore"] = df["market_cap_crore"].fillna(0).round(2)

category_colors = {
    "(?)": "#374151",
    "Nifty 100": "rgba(0,0,0,0)",
    "Standard": "#4c1d95",      
    "High Dividend": "#065f46", 
    "Cash Cow": "#92400e",      
    "Capex Heavy": "#9f1239",   
    "Debt Burdened": "#7f1d1d", 
    "Debt Free/Repayer": "#1e3a8a", 
    "High Growth": "#164e63",   
    "Balanced": "#701a75"       
}

fig = px.treemap(
    df,
    path=[px.Constant("Nifty 100"), "Allocation Pattern", "company_name"],
    values="market_cap_size",
    color="Allocation Pattern",
    color_discrete_map=category_colors,
    hover_data={
        "market_cap_size": False,
        "market_cap_crore": True,
        "broad_sector": True,
    }
)

fig.update_traces(
    textinfo="label",
    textfont=dict(color="#ffffff", family="Inter", size=13),
    hovertemplate="<b>%{label}</b><br>Market Cap (SIMULATED): \u20b9%{customdata[0]:,.0f} Cr<br>Sector: %{customdata[1]}<extra></extra>",
    marker=dict(line=dict(color="#131124", width=1.5)),
    pathbar=dict(textfont=dict(color="#9ca3af", family="Outfit", size=14)),
    root_color="#131124"
)

layout_opts = get_chart_layout_overrides()
layout_opts["margin"] = dict(t=30, l=10, r=10, b=10)
fig.update_layout(height=600, **layout_opts)
st.plotly_chart(fig, width="stretch")

st.markdown(
    "<hr style='margin: 16px 0; border-color: rgba(255, 255, 255, 0.05);'>",
    unsafe_allow_html=True,
)

col1, col2 = st.columns([1, 3])
with col1:
    st.markdown("<h3>FILTER BY PATTERN</h3>", unsafe_allow_html=True)
    selected_pattern = st.selectbox(
        "Pattern",
        sorted(df["Allocation Pattern"].unique()),
        label_visibility="collapsed",
    )

with col2:
    st.markdown("<h3>CONSTITUENTS</h3>", unsafe_allow_html=True)
    pattern_df = df[df["Allocation Pattern"] == selected_pattern][
        [
            "company_name",
            "broad_sector",
            "market_cap_crore",
            "free_cash_flow_cr",
            "dividend_yield_pct",
            "capex_intensity_pct",
        ]
    ]
    pattern_df.columns = [
        "Company Name",
        "Sector",
        "Mcap (SIMULATED) (Cr)",
        "FCF (Cr)",
        "Div Yield (%)",
        "Capex Int (%)",
    ]

    pattern_df = pattern_df.fillna(0)

    st.dataframe(
        pattern_df.style.format(
            {
                "Mcap (SIMULATED) (Cr)": "{:,.0f}",
                "FCF (Cr)": "{:,.0f}",
                "Div Yield (%)": "{:.2f}%",
                "Capex Int (%)": "{:.1f}%",
            }
        ),
        width="stretch",
        hide_index=True,
    )