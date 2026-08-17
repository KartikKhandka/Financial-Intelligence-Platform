import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from utils.db import get_companies, get_market_caps, get_pl, get_ratios
from utils.style import apply_custom_css, get_chart_layout_overrides, render_page_header

st.set_page_config(page_title="Trend Analysis", layout="wide")
apply_custom_css()

render_page_header(
    "TREND ANALYSIS", "Historical fundamental & valuation metric trends (10-Year)."
)

@st.cache_data(ttl=600)
def load_all_companies():

    df = get_companies()
    return (
        df["company_name"].tolist(),
        df.set_index("company_name")["company_id"].to_dict(),
    )

company_names, name_to_id = load_all_companies()

if not company_names:
    st.warning("No companies found.")
    st.stop()

col_sel1, col_sel2, _ = st.columns([1, 1, 2])
with col_sel1:
    selected_company_name = st.selectbox("Company", company_names)

company_id = name_to_id[selected_company_name]

pl_df = get_pl(company_id)
ratios_df = get_ratios(company_id)
mc_df = get_market_caps()
mc_df = mc_df[mc_df["company_id"] == company_id]

df = pd.merge(pl_df, ratios_df, on=["company_id", "year"], how="outer")
df = pd.merge(df, mc_df, on=["company_id", "year"], how="outer")
df = df.sort_values("year").dropna(subset=["year"])

metric_options = {
    "Sales": "sales",
    "Net Profit": "net_profit",
    "Operating Profit": "operating_profit",
    "EPS": "eps",
    "ROE (%)": "return_on_equity_pct",
    "P/E Ratio": "pe_ratio",
    "Free Cash Flow": "fcf",
    "Debt to Equity": "debt_to_equity",
}

with col_sel2:
    selected_metrics = st.multiselect(
        "Metrics (Max 3)", list(metric_options.keys()), default=["Sales", "Net Profit"]
    )

st.markdown(
    "<hr style='margin: 16px 0; border-color: rgba(255, 255, 255, 0.05);'>",
    unsafe_allow_html=True,
)

if len(selected_metrics) > 3:
    st.warning("Please select a maximum of 3 metrics.")
    selected_metrics = selected_metrics[:3]

if not selected_metrics:
    st.info("Select at least one metric to view the trend.")
    st.stop()

fig = go.Figure()

colors = get_chart_layout_overrides()["colorway"]

for i, metric_label in enumerate(selected_metrics):
    metric_col = metric_options[metric_label]

    if metric_col not in df.columns:
        continue

    y_vals = df[metric_col].tolist()
    x_vals = df["year"].tolist()

    text_annotations = []
    for j in range(len(y_vals)):
        if j == 0 or pd.isna(y_vals[j - 1]) or pd.isna(y_vals[j]) or y_vals[j - 1] == 0:
            text_annotations.append("")
        else:
            pct_change = ((y_vals[j] - y_vals[j - 1]) / abs(y_vals[j - 1])) * 100
            text_annotations.append(f"{pct_change:+.1f}%")

    fig.add_trace(
        go.Scatter(
            x=x_vals,
            y=y_vals,
            mode="lines+markers+text",
            name=metric_label,
            text=text_annotations,
            textposition="top center",
            textfont=dict(size=10, color=colors[i]),
            line=dict(color=colors[i], width=3),
            marker=dict(size=8, color="#030712", line=dict(color=colors[i], width=2)),
        )
    )

fig.update_layout(
    xaxis_title="",
    yaxis_title="",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        font=dict(color="#9ca3af"),
    ),
    hovermode="x unified",
    height=600,
    **get_chart_layout_overrides(),
)

if len(selected_metrics) > 1:
    max_1 = df[metric_options[selected_metrics[0]]].max()
    if len(selected_metrics) >= 2:
        max_2 = df[metric_options[selected_metrics[1]]].max()
        if max_1 > 0 and max_2 > 0 and (max_1 / max_2 > 10 or max_2 / max_1 > 10):
            fig.data[1].yaxis = "y2"
            fig.update_layout(
                yaxis2=dict(
                    overlaying="y",
                    side="right",
                    showgrid=False,
                    tickfont=dict(color="#9ca3af"),
                )
            )

st.plotly_chart(fig, width="stretch")