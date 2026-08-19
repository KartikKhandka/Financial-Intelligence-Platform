import streamlit as st
import base64

def apply_custom_css():
    svg_logo = """<svg viewBox="0 0 200 150" fill="none" xmlns="http://www.w3.org/2000/svg"><g transform="translate(30, 0) skewX(-15)"><rect x="0" y="70" width="35" height="70" rx="12" fill="url(#purple_grad)" /><rect x="50" y="20" width="35" height="120" rx="12" fill="url(#purple_grad)" /><rect x="100" y="40" width="35" height="100" rx="12" fill="url(#purple_grad)" /></g><path d="M10 120 Q90 130 180 45" stroke="#f59e0b" stroke-width="6" fill="none" stroke-linecap="round" /><circle cx="180" cy="45" r="8" fill="#f59e0b" /><defs><linearGradient id="purple_grad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#8b5cf6" /><stop offset="100%" stop-color="#4c1d95" /></linearGradient></defs></svg>"""
    img_base64 = base64.b64encode(svg_logo.encode('utf-8')).decode('utf-8')
    watermark_html = f"""
    <div style="
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 500px;
        height: 500px;
        background-image: url('data:image/svg+xml;base64,{img_base64}');
        background-size: contain;
        background-repeat: no-repeat;
        background-position: center;
        opacity: 0.1;
        pointer-events: none;
        z-index: 0;
    "></div>
    """
    st.markdown(watermark_html, unsafe_allow_html=True)

    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Outfit:wght@500;700;800;900&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif !important;
            background-color: #131124 !important;
            color: #9ca3af !important;
            font-size: 14px !important;
        }

        [data-testid="stSidebar"], [data-testid="collapsedControl"] {
            display: none !important;
        }

        .stApp {
            background-color: #131124 !important;
            background-image: radial-gradient(circle at 50% 0%, rgba(139, 92, 246, 0.15) 0%, rgba(19, 17, 36, 0) 50%) !important;
            background-attachment: fixed;
        }

        footer {visibility: hidden;}

        .block-container, 
        [data-testid="stAppViewBlockContainer"], 
        [data-testid="stMainBlockContainer"] {
            padding-top: 1.5rem !important;
            padding-bottom: 0rem !important;
            margin-top: 0rem !important;
        }

        section[data-testid="stSidebar"] {
            background-color: #1A1831 !important;
            border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
            width: 260px !important;
        }

        [data-testid="stSidebarNav"] span, [data-testid="stPageLink"] p {
            font-family: 'Outfit', sans-serif !important;
            font-size: 11px !important;
            font-weight: 700 !important;
            color: #9ca3af !important;
            text-transform: uppercase;
            letter-spacing: 1px;
            transition: all 0.3s ease;
            margin: 0 !important;
            text-align: center;
            white-space: nowrap;
        }

        div[data-testid="stVerticalBlock"]:has(#nav-columns) div[data-testid="stHorizontalBlock"] {
            gap: 24px !important;
            justify-content: center !important;
        }
        div[data-testid="stVerticalBlock"]:has(#nav-columns) div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            width: max-content !important;
            flex: 0 0 auto !important;
            min-width: 0 !important;
        }
        div[data-testid="stElementContainer"]:has([data-testid="stPageLink"]), 
        div[data-testid="stElementContainer"]:has([data-testid="stPageLink"]) * {
            overflow: visible !important;
        }

        [data-testid="stSidebarNav"] span:hover, [data-testid="stPageLink"]:hover p {
            color: #8b5cf6 !important;
            text-shadow: 0 0 10px rgba(139, 92, 246, 0.5);
        }

        [data-testid="stPageLink"] {
            display: flex;
            justify-content: center;
            align-items: center;
            background: transparent !important;
            border: none !important;
            padding: 0 !important;
            text-decoration: none !important;
            width: 100%;
        }
        [data-testid="stPageLink"]:hover {
            background: transparent !important;
        }
        [data-testid="stPageLink"] a {
            padding: 8px 16px !important;
            border-radius: 8px !important;
            background: transparent !important;
            transition: all 0.3s ease !important;
        }
        [data-testid="stPageLink"] a:hover {
            background: rgba(139, 92, 246, 0.1) !important;
        }
        [data-testid="stPageLink"] svg {
            display: none !important;
        }

        @keyframes text-gradient-shift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        h1 {
            font-family: 'Outfit', sans-serif !important;
            font-weight: 900 !important;
            font-size: 48px !important;
            letter-spacing: -1px !important;
            margin-bottom: 0.5rem !important;
            text-transform: uppercase;
            border: none !important;
            padding: 0 !important;
            line-height: 1.1 !important;
            color: #ffffff !important;
        }

        .terminal-header h1 {
            background: linear-gradient(90deg, #8b5cf6 0%, #8b5cf6 25%, #ffffff 40%, #f59e0b 55%, #8b5cf6 70%, #8b5cf6 100%);
            background-size: 300% auto;
            color: transparent !important;
            -webkit-background-clip: text !important;
            background-clip: text !important;
            animation: text-gradient-shift 12s ease-in-out infinite;
        }

        h2 {
            font-family: 'Outfit', sans-serif !important;
            font-weight: 800 !important;
            font-size: 28px !important;
            color: #ffffff !important;
            margin-top: 1.5rem !important;
            margin-bottom: 1rem !important;
            text-transform: uppercase;
            letter-spacing: -0.5px;
        }

        h3 {
            font-family: 'Outfit', sans-serif !important;
            font-weight: 700 !important;
            font-size: 16px !important;
            color: #8b5cf6 !important;
            text-transform: uppercase;
            letter-spacing: 2px !important;
        }

        .metric-group {
            display: flex;
            align-items: stretch;
            margin-bottom: 32px;
            flex-wrap: wrap;
            gap: 24px;
        }

        .metric-item {
            flex: 1;
            min-width: 200px;
            background: rgba(255, 255, 255, 0.02);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            padding: 24px;
            display: flex;
            flex-direction: column;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }

        .metric-item::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 2px;
            background: linear-gradient(90deg, transparent, rgba(139, 92, 246, 0.5), transparent);
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        .metric-item:hover {
            background: rgba(255, 255, 255, 0.04);
            border-color: rgba(139, 92, 246, 0.4);
            box-shadow: 0 10px 30px -10px rgba(139, 92, 246, 0.2);
            transform: translateY(-2px);
        }

        .metric-item:hover::before {
            opacity: 1;
        }

        .metric-label {
            color: #9ca3af;
            font-family: 'Inter', sans-serif;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }

        .metric-val {
            color: #ffffff;
            font-family: 'Outfit', sans-serif;
            font-size: 36px;
            font-weight: 800;
            line-height: 1.1;
        }

        .metric-sub {
            font-size: 13px;
            margin-top: 8px;
            font-weight: 500;
        }

        .positive { color: #10b981; text-shadow: 0 0 10px rgba(16, 185, 129, 0.3); }
        .negative { color: #f43f5e; text-shadow: 0 0 10px rgba(244, 63, 94, 0.3); }
        .neutral { color: #9ca3af; }

        .analysis-section {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 24px;
            transition: all 0.3s ease;
        }
        .analysis-section:hover {
            border-color: rgba(255, 255, 255, 0.1);
        }
        .analysis-title {
            color: #ffffff;
            font-family: 'Outfit', sans-serif;
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 16px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .pro-item, .con-item {
            color: #d1d5db;
            font-size: 14px;
            margin-bottom: 10px;
            display: flex;
            align-items: flex-start;
        }
        .pro-item::before { content: "✦"; color: #8b5cf6; margin-right: 12px; font-weight: bold; text-shadow: 0 0 8px rgba(139, 92, 246, 0.5); }
        .con-item::before { content: "✦"; color: #f43f5e; margin-right: 12px; font-weight: bold; text-shadow: 0 0 8px rgba(244, 63, 94, 0.5); }

        .stDataFrame {
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-radius: 12px !important;
            overflow: hidden !important;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 32px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        .stTabs [data-baseweb="tab"] {
            font-family: 'Outfit', sans-serif !important;
            font-weight: 600;
            font-size: 14px;
            color: #9ca3af;
            border-bottom: 2px solid transparent !important;
            padding-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .stTabs [aria-selected="true"] {
            color: #8b5cf6 !important;
            border-bottom: 2px solid #8b5cf6 !important;
            text-shadow: 0 0 10px rgba(139, 92, 246, 0.4);
        }

        .stSelectbox div[data-baseweb="select"] > div {
            background-color: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 8px !important;
            color: #ffffff !important;
        }

        .stButton button {
            background: linear-gradient(135deg, #8b5cf6, #6d28d9) !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 30px !important;
            padding: 12px 24px !important;
            font-family: 'Outfit', sans-serif !important;
            font-weight: 700 !important;
            letter-spacing: 1px !important;
            text-transform: uppercase !important;
            box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3) !important;
            transition: all 0.3s ease !important;
        }

        .stButton button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 25px rgba(139, 92, 246, 0.5) !important;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )

def render_page_header(title, subtitle):

    html = f"""
    <div class="terminal-header" style="margin-bottom: 32px; border-bottom: 1px solid rgba(255, 255, 255, 0.05); padding-bottom: 24px;">
        <div>
            <h1 style="font-size: 42px !important; color: #8b5cf6 !important;">{title}</h1>
            <div style="color: #9ca3af; font-size: 14px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase;">{subtitle}</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_metric_group(metrics):

    html = '<div class="metric-group">'
    for m in metrics:
        sub_html = (
            f'<div class="metric-sub {m.get("sub_class", "neutral")}">{m.get("sub", "")}</div>'
            if m.get("sub")
            else ""
        )
        html += f'<div class="metric-item"><div class="metric-label">{m["label"]}</div><div class="metric-val">{m["value"]}</div>{sub_html}</div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

def render_pro_card(text):

    html = f"""<div class="pro-item">{text}</div>"""
    st.markdown(html, unsafe_allow_html=True)

def render_con_card(text):

    html = f"""<div class="con-item">{text}</div>"""
    st.markdown(html, unsafe_allow_html=True)

def get_chart_layout_overrides():

    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#9ca3af", size=12),
        margin=dict(l=40, r=20, t=40, b=30),
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.05)",
            gridwidth=1,
            zeroline=False,
            title_font=dict(size=12),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.05)",
            gridwidth=1,
            zeroline=False,
            title_font=dict(size=12),
        ),
        hoverlabel=dict(
            bgcolor="rgba(26, 24, 49, 0.95)",
            bordercolor="rgba(139, 92, 246, 0.5)",
            font_size=12,
            font_family="Inter",
        ),
        colorway=[
            "#8b5cf6",
            "#f59e0b",
            "#10b981",
            "#f43f5e",
            "#3b82f6",
            "#ec4899",
            "#06b6d4",
        ],
    )