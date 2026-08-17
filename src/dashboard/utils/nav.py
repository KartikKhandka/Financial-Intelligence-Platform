import streamlit as st

def render_top_nav():

    st.markdown(
        """
        <style>
            [data-testid="stSidebarNav"] {display: none;}
        </style>
    """,
        unsafe_allow_html=True,
    )

    with st.container():
        st.markdown('<span id="nav-columns"></span>', unsafe_allow_html=True)
        cols = st.columns(8)

        pages = [
            ("app.py", "Home"),
            ("pages/02_profile.py", "Profile"),
            ("pages/03_screener.py", "Screener"),
            ("pages/04_peers.py", "Peers"),
            ("pages/05_trends.py", "Trends"),
            ("pages/06_sectors.py", "Sectors"),
            ("pages/07_capital.py", "Capital"),
            ("pages/08_reports.py", "Reports"),
        ]

        for i, (path, name) in enumerate(pages):
            with cols[i]:
                st.page_link(path, label=name)

    st.markdown("---")