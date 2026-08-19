import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
from utils.style import apply_custom_css

st.set_page_config(
    page_title="Nifty 100 Analytics",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_custom_css()

pages_dict = {
    "pages/01_home.py": "Home",
    "pages/02_profile.py": "Company Profile",
    "pages/03_screener.py": "Screener",
    "pages/04_peers.py": "Peer Comparison",
    "pages/05_trends.py": "Trend Analysis",
    "pages/06_sectors.py": "Sector Analysis",
    "pages/07_capital.py": "Capital Allocation",
    "pages/08_reports.py": "Annual Reports",
    "pages/09_generated.py": "AI Generated Reports",
}

st_pages = [st.Page(path, title=title) for path, title in pages_dict.items()]
pg = st.navigation(st_pages, position="hidden")

bluestock_logo_svg = """<div style='display:flex; justify-content:left; align-items:center; margin-bottom: 16px;'><svg width="45" height="45" viewBox="0 0 200 150" fill="none" xmlns="http://www.w3.org/2000/svg"><g transform="translate(30, 0) skewX(-15)"><rect x="0" y="70" width="35" height="70" rx="12" fill="url(#purple_grad)" /><rect x="50" y="20" width="35" height="120" rx="12" fill="url(#purple_grad)" /><rect x="100" y="40" width="35" height="100" rx="12" fill="url(#purple_grad)" /></g><path d="M10 120 Q90 130 180 45" stroke="#f59e0b" stroke-width="6" fill="none" stroke-linecap="round" /><circle cx="180" cy="45" r="8" fill="#f59e0b" /><defs><linearGradient id="purple_grad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#8b5cf6" /><stop offset="100%" stop-color="#4c1d95" /></linearGradient></defs></svg><div style="font-family: 'Outfit', sans-serif; display: flex; align-items: baseline; margin-left: 10px;"><span style="font-weight: 900; font-size: 24px; letter-spacing: 0.5px; color: #ffffff;">BLUESTOCK<sup style="font-size: 10px; font-weight: 600; margin-left: 2px; color: #9ca3af;">TM</sup></span><span style="font-weight: 700; font-size: 16px; color: #ffffff;">.in</span></div></div>"""
st.markdown(bluestock_logo_svg, unsafe_allow_html=True)

with st.container():
    st.markdown("<div id='nav-columns'></div>", unsafe_allow_html=True)
    cols = st.columns(len(st_pages))
    for col, page_obj in zip(cols, st_pages):
        with col:
            st.page_link(page_obj, label=page_obj.title)
st.markdown(
    "<div style='margin-bottom: 24px; border-bottom: 1px solid rgba(255, 255, 255, 0.05);'></div>",
    unsafe_allow_html=True,
)

pg.run()