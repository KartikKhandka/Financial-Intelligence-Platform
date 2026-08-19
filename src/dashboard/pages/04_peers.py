import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from utils.db import get_connection, get_market_caps, get_ratios
from utils.style import apply_custom_css, render_page_header

st.set_page_config(page_title="Peer Comparison", layout="wide")
apply_custom_css()

render_page_header(
    "PEER COMPARISON", "Compare fundamental metrics across pre-defined peer groups."
)

@st.cache_data(ttl=600)
def get_peer_group_names():

    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT DISTINCT peer_group_name FROM peer_groups ORDER BY peer_group_name",
        conn,
    )
    conn.close()
    return df["peer_group_name"].tolist()

@st.cache_data(ttl=600)
def get_peer_group_data(group_name):

    conn = get_connection()
    query = """
        SELECT company_id, is_benchmark
        FROM peer_groups
        WHERE peer_group_name = ?
    """
    df = pd.read_sql_query(query, conn, params=[group_name])
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_metrics_for_companies(company_ids):

    if not company_ids:
        return pd.DataFrame()
        
    from utils.db import get_master_dataframe
    df = get_master_dataframe()
    return df[df["company_id"].isin(company_ids)]

groups = get_peer_group_names()
if not groups:
    st.warning("No peer groups found in the database.")
    st.stop()

col_sel1, col_sel2, _ = st.columns([1, 1, 2])
with col_sel1:
    selected_group = st.selectbox("Peer Group", groups)

group_data = get_peer_group_data(selected_group)
company_ids = group_data["company_id"].tolist()
metrics_df = get_metrics_for_companies(company_ids)

full_df = pd.merge(group_data, metrics_df, on="company_id", how="left")

benchmark_row = full_df[full_df["is_benchmark"] == 1]
benchmark_company = (
    benchmark_row["company_name"].iloc[0]
    if not benchmark_row.empty
    else full_df["company_name"].iloc[0]
)

with col_sel2:
    selected_company_name = st.selectbox(
        "Focus Company",
        full_df["company_name"].tolist(),
        index=(
            full_df["company_name"].tolist().index(benchmark_company)
            if benchmark_company in full_df["company_name"].tolist()
            else 0
        ),
    )

st.markdown(
    "<hr style='margin: 16px 0; border-color: rgba(255, 255, 255, 0.05);'>",
    unsafe_allow_html=True,
)

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("<h3>RELATIVE PERFORMANCE</h3>", unsafe_allow_html=True)

    radar_cols = [
        "return_on_equity_pct",
        "operating_profit_margin_pct",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "interest_coverage",
        "asset_turnover",
        "pe_ratio",
        "pb_ratio",
    ]

    radar_labels = [
        "ROE",
        "OPM",
        "Rev CAGR",
        "PAT CAGR",
        "ICR",
        "Asset T/O",
        "P/E",
        "P/B",
    ]

    group_avg = full_df[radar_cols].mean().fillna(0).tolist()

    company_data = (
        full_df[full_df["company_name"] == selected_company_name][radar_cols]
        .iloc[0]
        .fillna(0)
        .tolist()
    )

    norm_company = []
    norm_avg = []

    for i, col in enumerate(radar_cols):
        max_val = max(full_df[col].max(), 0.01)  
        if max_val <= 0:
            max_val = 1

        c_val = max(0, company_data[i]) / max_val * 100
        a_val = max(0, group_avg[i]) / max_val * 100
        norm_company.append(c_val)
        norm_avg.append(a_val)

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=norm_company + [norm_company[0]],
            theta=radar_labels + [radar_labels[0]],
            fill="toself",
            name=selected_company_name,
            line_color="#8b5cf6",
            fillcolor="rgba(139, 92, 246, 0.2)",
            hovertemplate="<b>" + selected_company_name + "</b><br>%{theta}: %{r:.1f}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatterpolar(
            r=norm_avg + [norm_avg[0]],
            theta=radar_labels + [radar_labels[0]],
            fill="toself",
            name="Group Avg",
            line_color="#f59e0b",
            fillcolor="rgba(245, 158, 11, 0.15)",
            hovertemplate="<b>Group Avg</b><br>%{theta}: %{r:.1f}<extra></extra>",
        )
    )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=False, range=[0, 100]),
            angularaxis=dict(
                color="#9ca3af",
                gridcolor="rgba(255,255,255,0.05)",
                linecolor="rgba(255,255,255,0.05)",
            ),
            bgcolor="rgba(0,0,0,0)",
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.1,
            xanchor="center",
            x=0.5,
            font=dict(color="#9ca3af"),
        ),
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(
            bgcolor="#111827",
            font_size=13,
            font_family="Inter",
            bordercolor="rgba(255,255,255,0.1)",
            font_color="#ffffff"
        )
    )

    st.plotly_chart(fig, width="stretch")

with col2:
    st.markdown("<h3>FUNDAMENTAL COMPARISON</h3>", unsafe_allow_html=True)

    display_cols = ["company_name", "is_benchmark"] + radar_cols
    table_df = full_df[display_cols].copy()

    table_df = table_df.rename(
        columns={
            "company_name": "Company",
            "return_on_equity_pct": "ROE (%)",
            "operating_profit_margin_pct": "OPM (%)",
            "revenue_cagr_5yr": "Rev CAGR (%)",
            "pat_cagr_5yr": "PAT CAGR (%)",
            "interest_coverage": "ICR",
            "asset_turnover": "Asset T/O",
            "pe_ratio": "P/E",
            "pb_ratio": "P/B",
        }
    ).round(2)

    def highlight_selected(row):

        if row["Company"] == selected_company_name:
            return [
                "background-color: rgba(139, 92, 246, 0.1); color: #ffffff; font-weight: 700; text-shadow: 0 0 10px rgba(139, 92, 246, 0.5)"
            ] * len(row)
        return [""] * len(row)

    styled_df = table_df.style.apply(highlight_selected, axis=1).format(precision=2)

    st.dataframe(
        styled_df,
        width="stretch",
        hide_index=True,
        column_config={"is_benchmark": None},
    )