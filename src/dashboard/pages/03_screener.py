import pandas as pd
import streamlit as st
from utils.db import get_companies, get_market_caps, get_ratios, get_sectors
from utils.style import apply_custom_css, render_page_header

st.set_page_config(page_title="Screener", layout="wide")
apply_custom_css()

render_page_header(
    "STOCK SCREENER", "Filter Nifty 100 constituents across 10 fundamental metrics."
)

@st.cache_data(ttl=600)
def load_screener_data():

    from utils.db import get_master_dataframe
    df = get_master_dataframe().copy()

    df["composite_quality_score"] = (
        (df["return_on_equity_pct"].fillna(0) > 15).astype(int)
        + (df["debt_to_equity"].fillna(10) < 0.5).astype(int)
        + (df["fcf_conversion_rate_pct"].fillna(0) > 50).astype(int)
        + (df["interest_coverage"].fillna(0) > 5).astype(int)
        + (df["revenue_cagr_5yr"].fillna(0) > 10).astype(int)
    )
    return df

df = load_screener_data()

if "roe" not in st.session_state:
    st.session_state.update(
        {
            "roe": -50.0,
            "de": 10.0,
            "fcf": -10000.0,
            "rev_cagr": -20.0,
            "pat_cagr": -20.0,
            "opm": -20.0,
            "pe": 200.0,
            "pb": 30.0,
            "div": 0.0,
            "icr": -10.0,
        }
    )

def apply_preset(preset_name):

    presets = {
        "Quality": {
            "roe": 20.0,
            "de": 0.5,
            "icr": 5.0,
            "pe": 200.0,
            "pb": 30.0,
            "fcf": 0.0,
            "rev_cagr": 0.0,
            "pat_cagr": 0.0,
            "opm": 10.0,
            "div": 0.0,
        },
        "Value": {
            "pe": 15.0,
            "pb": 2.0,
            "div": 2.0,
            "roe": 10.0,
            "de": 1.0,
            "fcf": 0.0,
            "rev_cagr": 0.0,
            "pat_cagr": 0.0,
            "opm": 0.0,
            "icr": 2.0,
        },
        "Growth": {
            "rev_cagr": 15.0,
            "pat_cagr": 15.0,
            "roe": 15.0,
            "pe": 200.0,
            "pb": 30.0,
            "de": 2.0,
            "fcf": -500.0,
            "opm": 0.0,
            "div": 0.0,
            "icr": 2.0,
        },
        "Dividend": {
            "div": 3.0,
            "fcf": 100.0,
            "roe": 10.0,
            "pe": 200.0,
            "pb": 30.0,
            "de": 1.5,
            "rev_cagr": 0.0,
            "pat_cagr": 0.0,
            "opm": 0.0,
            "icr": 2.0,
        },
        "Debt-Free": {
            "de": 0.1,
            "icr": 10.0,
            "roe": 10.0,
            "pe": 200.0,
            "pb": 30.0,
            "fcf": 0.0,
            "rev_cagr": 0.0,
            "pat_cagr": 0.0,
            "opm": 0.0,
            "div": 0.0,
        },
        "Turnaround": {
            "pat_cagr": 20.0,
            "roe": -10.0,
            "pe": 200.0,
            "pb": 30.0,
            "de": 5.0,
            "fcf": -1000.0,
            "rev_cagr": 0.0,
            "opm": -10.0,
            "div": 0.0,
            "icr": -1.0,
        },
        "Reset": {
            "roe": -50.0,
            "de": 10.0,
            "fcf": -10000.0,
            "rev_cagr": -20.0,
            "pat_cagr": -20.0,
            "opm": -20.0,
            "pe": 200.0,
            "pb": 30.0,
            "div": 0.0,
            "icr": -10.0,
        },
    }
    if preset_name in presets:
        st.session_state.update(presets[preset_name])

col_filters, col_results = st.columns([1, 4])

with col_filters:
    st.markdown("<h3>SAVED SCREENS</h3>", unsafe_allow_html=True)

    if "preset_selectbox" not in st.session_state:
        st.session_state.preset_selectbox = "Custom"

    def handle_preset_change():

        if st.session_state.preset_selectbox != "Custom":
            apply_preset(st.session_state.preset_selectbox)

    preset_choice = st.selectbox(
        "Select Screen",
        options=[
            "Custom",
            "Quality",
            "Value",
            "Growth",
            "Dividend",
            "Debt-Free",
            "Turnaround",
        ],
        key="preset_selectbox",
        label_visibility="collapsed",
        on_change=handle_preset_change,
    )

    def reset_filters():

        st.session_state.preset_selectbox = "Custom"
        apply_preset("Reset")

    if st.button("Reset Filters", width="stretch", on_click=reset_filters):
        pass

    st.markdown(
        "<hr style='margin: 16px 0; border-color: rgba(255, 255, 255, 0.05);'>",
        unsafe_allow_html=True,
    )
    st.markdown("<h3>FILTERS</h3>", unsafe_allow_html=True)

    def make_custom():

        st.session_state.preset_selectbox = "Custom"

    min_roe = st.slider(
        "ROE (%) Min", -50.0, 100.0, key="roe", step=1.0, on_change=make_custom
    )
    max_de = st.slider(
        "D/E Ratio Max", 0.0, 10.0, key="de", step=0.1, on_change=make_custom
    )
    min_fcf = st.slider(
        "FCF (Cr) Min", -10000.0, 50000.0, key="fcf", step=100.0, on_change=make_custom
    )
    min_rev_cagr = st.slider(
        "Rev CAGR 5Y (%) Min",
        -20.0,
        50.0,
        key="rev_cagr",
        step=1.0,
        on_change=make_custom,
    )
    min_pat_cagr = st.slider(
        "PAT CAGR 5Y (%) Min",
        -20.0,
        50.0,
        key="pat_cagr",
        step=1.0,
        on_change=make_custom,
    )
    min_opm = st.slider(
        "OPM (%) Min", -20.0, 80.0, key="opm", step=1.0, on_change=make_custom
    )
    max_pe = st.slider(
        "P/E Ratio Max", 0.0, 200.0, key="pe", step=1.0, on_change=make_custom
    )
    max_pb = st.slider(
        "P/B Ratio Max", 0.0, 30.0, key="pb", step=0.5, on_change=make_custom
    )
    min_div = st.slider(
        "Dividend Yield (%) Min", 0.0, 10.0, key="div", step=0.1, on_change=make_custom
    )
    min_icr = st.slider(
        "Interest Coverage Min",
        -10.0,
        100.0,
        key="icr",
        step=1.0,
        on_change=make_custom,
    )

with col_results:
    filtered_df = df[
        (df["return_on_equity_pct"].fillna(-999) >= min_roe)
        & (df["debt_to_equity"].fillna(0) <= max_de)
        & (df["free_cash_flow_cr"].fillna(-99999) >= min_fcf)
        & (df["revenue_cagr_5yr"].fillna(-999) >= min_rev_cagr)
        & (df["pat_cagr_5yr"].fillna(-999) >= min_pat_cagr)
        & (df["operating_profit_margin_pct"].fillna(-999) >= min_opm)
        & (df["pe_ratio"].fillna(9999) <= max_pe)
        & (df["pb_ratio"].fillna(9999) <= max_pb)
        & (df["dividend_yield_pct"].fillna(0) >= min_div)
        & (df["interest_coverage"].fillna(-999) >= min_icr)
    ]

    st.markdown(
        f"<h3>RESULTS ({len(filtered_df)} matches)</h3>", unsafe_allow_html=True
    )

    display_df = filtered_df.rename(
        columns={
            "company_id": "Ticker",
            "company_name": "Company Name",
            "broad_sector": "Sector",
            "composite_quality_score": "Quality Score",
            "return_on_equity_pct": "ROE (%)",
            "debt_to_equity": "D/E",
            "free_cash_flow_cr": "FCF (Cr)",
            "revenue_cagr_5yr": "Rev CAGR 5Y (%)",
            "pat_cagr_5yr": "PAT CAGR 5Y (%)",
            "operating_profit_margin_pct": "OPM (%)",
            "pe_ratio": "P/E",
            "pb_ratio": "P/B",
            "dividend_yield_pct": "Div Yield (%)",
            "interest_coverage": "ICR",
        }
    ).round(2)

    st.dataframe(display_df, width="stretch", hide_index=True, height=700)

    csv = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="screener_results.csv",
        mime="text/csv",
    )