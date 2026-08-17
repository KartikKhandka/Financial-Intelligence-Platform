import pandas as pd
import streamlit as st
from utils.db import get_companies, get_connection
from utils.style import apply_custom_css, render_page_header

st.set_page_config(page_title="Annual Reports", layout="wide")
apply_custom_css()

render_page_header(
    "ANNUAL REPORTS",
    "Repository of statutory annual reports and filings for Nifty 100 constituents.",
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

col_sel1, _ = st.columns([1, 2])
with col_sel1:
    selected_company_name = st.selectbox("Company", company_names)
company_id = name_to_id[selected_company_name]

@st.cache_data(ttl=600)
def get_documents(cid):

    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT year, annual_report FROM documents WHERE company_id = ? ORDER BY year DESC",
        conn,
        params=[cid],
    )
    conn.close()
    return df

docs_df = get_documents(company_id)

st.markdown(
    "<hr style='margin: 16px 0; border-color: rgba(255, 255, 255, 0.05);'>",
    unsafe_allow_html=True,
)
st.markdown(
    f"<h3>AVAILABLE REPORTS: {selected_company_name.upper()}</h3>",
    unsafe_allow_html=True,
)

if docs_df.empty:
    st.info("No annual reports found for this company.")
else:

    st.markdown(
        """
    <style>
    .report-table { width: 100%; border-collapse: collapse; text-align: left; }
    .report-table th { padding: 16px; font-weight: 700; color: #9ca3af; font-family: 'Outfit', sans-serif; text-transform: uppercase; font-size: 12px; letter-spacing: 1px; border-bottom: 1px solid rgba(255, 255, 255, 0.05); }
    .report-table td { padding: 16px; font-weight: 500; font-family: 'Inter', sans-serif; border-bottom: 1px solid rgba(255, 255, 255, 0.05); transition: all 0.2s ease; }
    .report-table tr { transition: background-color 0.2s ease; }
    .report-table tr:hover { background-color: rgba(139, 92, 246, 0.05); }
    </style>
    """,
        unsafe_allow_html=True,
    )

    table_html = '<table class="report-table">'
    table_html += "<thead><tr>"
    table_html += "<th>Financial Year</th>"
    table_html += "<th>Document Type</th>"
    table_html += "<th>Status</th>"
    table_html += '<th style="text-align: right;">Action</th>'
    table_html += "</tr></thead><tbody>"

    for i, row in docs_df.iterrows():
        year = row["year"]
        link = row["annual_report"]

        status_html = ""
        action_html = ""

        if pd.isna(link) or not link:
            status_html = "<span style='color: #f43f5e; text-shadow: 0 0 10px rgba(244, 63, 94, 0.3);'>Unavailable</span>"
            action_html = "<span style='color: #4b5563;'>-</span>"
        else:
            status_html = "<span style='color: #10b981; text-shadow: 0 0 10px rgba(16, 185, 129, 0.3);'>Available</span>"
            action_html = f"<a href='{link}' target='_blank' style='color: #8b5cf6; text-decoration: none; font-weight: 600; text-shadow: 0 0 10px rgba(139, 92, 246, 0.4);'>View PDF ↗</a>"

        table_html += "<tr>"
        table_html += f"<td style=\"color: #ffffff; font-weight: 600; font-family: 'Outfit', sans-serif; font-size: 16px;\">FY {year}</td>"
        table_html += '<td style="color: #9ca3af;">Annual Report</td>'
        table_html += f"<td>{status_html}</td>"
        table_html += f'<td style="text-align: right;">{action_html}</td>'
        table_html += "</tr>"

    table_html += "</tbody></table>"
    st.markdown(table_html, unsafe_allow_html=True)