import os
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from utils.db import get_companies, get_connection
from utils.style import apply_custom_css, render_page_header

st.set_page_config(page_title="Generated Reports", layout="wide")
apply_custom_css()

render_page_header(
    "AI GENERATED REPORTS",
    "Download automated Tearsheets, Sector Reports, and Portfolio Summaries generated during the batch process.",
)

st.markdown(
    "<h3 style='color: #8b5cf6; font-family: Outfit;'>Portfolio Summary</h3>",
    unsafe_allow_html=True,
)
st.markdown(
    "A comprehensive PDF covering all companies with top KPIs and trend arrows."
)
from src import config
portfolio_path = config.REPORTS_DIR / "portfolio" / "portfolio_summary.pdf"
if os.path.exists(portfolio_path):
    with open(portfolio_path, "rb") as f:
        st.download_button(
            label="📄 Download Portfolio Summary",
            data=f.read(),
            file_name="Portfolio_Summary.pdf",
            mime="application/pdf",
        )
else:
    st.info("Portfolio Summary PDF not generated yet.")

st.markdown(
    "<hr style='border-color: rgba(255,255,255,0.1); margin: 30px 0;'>",
    unsafe_allow_html=True,
)

st.markdown(
    "<h3 style='color: #8b5cf6; font-family: Outfit;'>Company Reports & Charts</h3>",
    unsafe_allow_html=True,
)
st.markdown(
    "Detailed 2-page tearsheets and fundamental radar charts comparing the company against the Nifty 100 average."
)

@st.cache_data(ttl=600)
def load_all_companies():

    df = get_companies()
    return (
        df["company_name"].tolist(),
        df.set_index("company_name")["company_id"].to_dict(),
    )

company_names, name_to_id = load_all_companies()

col1, col2 = st.columns([1, 2])
with col1:
    selected_company_name = st.selectbox("Select Company for Reports", company_names)

if selected_company_name:
    company_id = name_to_id[selected_company_name]
    tearsheet_path = config.REPORTS_DIR / "tearsheets" / f"{company_id}_tearsheet.pdf"
    radar_path = config.REPORTS_DIR / "radar_charts" / f"{company_id}_radar.png"

    col_rep1, col_rep2 = st.columns(2)
    with col_rep1:
        if os.path.exists(tearsheet_path):
            with open(tearsheet_path, "rb") as f:
                st.download_button(
                    label=f"📄 Download {company_id} Tearsheet",
                    data=f.read(),
                    file_name=f"{company_id}_Tearsheet.pdf",
                    mime="application/pdf",
                    key=f"btn_ts_{company_id}",
                )
        else:
            st.warning(
                f"Tearsheet not found for {company_id}. It may have been skipped due to insufficient data."
            )
    with col_rep2:
        if os.path.exists(radar_path):
            with open(radar_path, "rb") as f:
                st.download_button(
                    label=f"📊 Download {company_id} Radar Chart",
                    data=f.read(),
                    file_name=f"{company_id}_Radar.png",
                    mime="image/png",
                    key=f"btn_radar_{company_id}",
                )
        else:
            st.info(f"Radar chart not found for {company_id}.")

    st.markdown("<br>", unsafe_allow_html=True)
    col_chart, _ = st.columns([1, 1])
    with col_chart:
        conn = get_connection()
        query = """
        SELECT c.company_id, c.company_name, 
               r.return_on_equity_pct, r.operating_profit_margin_pct, r.revenue_cagr_5yr, r.pat_cagr_5yr, r.interest_coverage, r.asset_turnover,
               m.pe_ratio, m.pb_ratio
        FROM companies c
        JOIN financial_ratios r ON c.company_id = r.company_id
        LEFT JOIN market_cap m ON c.company_id = m.company_id AND r.year = m.year
        WHERE r.year = (SELECT MAX(year) FROM financial_ratios WHERE company_id = c.company_id)
        """
        df_radar = pd.read_sql_query(query, conn)
        conn.close()
        features = [
            "return_on_equity_pct", "operating_profit_margin_pct", 
            "revenue_cagr_5yr", "pat_cagr_5yr", 
            "interest_coverage", "asset_turnover", 
            "pe_ratio", "pb_ratio"
        ]
        labels = ["ROE", "OPM", "Rev CAGR", "PAT CAGR", "ICR", "Asset T/O", "P/E", "P/B"]
        for col in features:
            df_radar[col] = pd.to_numeric(df_radar[col], errors='coerce').fillna(0)
            df_radar[col] = df_radar[col].clip(lower=0)
        group_avg = df_radar[features].mean()
        company_row = df_radar[df_radar["company_id"] == company_id]
        if not company_row.empty:
            values = company_row[features].iloc[0].values
            avg_values = group_avg.values
            norm_values = []
            norm_avg = []
            for i, col in enumerate(features):
                max_val = max(df_radar[col].max(), 0.01)
                norm_values.append(values[i] / max_val * 100)
                norm_avg.append(avg_values[i] / max_val * 100)
            fig = go.Figure()
            fig.add_trace(
                go.Scatterpolar(
                    r=norm_values + [norm_values[0]],
                    theta=labels + [labels[0]],
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
                    theta=labels + [labels[0]],
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
            st.plotly_chart(fig, use_container_width=True)
            st.caption(f"<div style='text-align: center; color: #9ca3af;'>{selected_company_name} Fundamental Radar</div>", unsafe_allow_html=True)

st.markdown(
    "<hr style='border-color: rgba(255,255,255,0.1); margin: 30px 0;'>",
    unsafe_allow_html=True,
)

st.markdown(
    "<h3 style='color: #8b5cf6; font-family: Outfit;'>Sector Reports</h3>",
    unsafe_allow_html=True,
)
st.markdown("Sector-wise analysis with median KPIs and complete company metric lists.")

sector_dir = config.REPORTS_DIR / "sector"
if os.path.exists(sector_dir):
    sector_files = [f for f in os.listdir(sector_dir) if f.endswith("_report.pdf")]
    if sector_files:
        sector_names = [
            f.replace("_report.pdf", "").replace("_", " ") for f in sector_files
        ]
        col3, col4 = st.columns([1, 2])
        with col3:
            selected_sector = st.selectbox("Select Sector", sector_names)

        if selected_sector:

            file_idx = sector_names.index(selected_sector)
            sector_file = sector_files[file_idx]
            sector_path = os.path.join(sector_dir, sector_file)

            with open(sector_path, "rb") as f:
                st.download_button(
                    label=f"📄 Download {selected_sector} Sector Report",
                    data=f.read(),
                    file_name=sector_file,
                    mime="application/pdf",
                    key=f"btn_sec_{selected_sector}",
                )
    else:
        st.info("No sector reports found.")
else:
    st.info("Sector reports directory not found.")