import streamlit as st

# 莫蘭迪色系變數
MORANDI = {
    "bg":       "#F2F0ED",   # 頁面底色
    "surface":  "#FAFAF8",   # 卡片底色
    "border":   "#DDD9D3",   # 邊框
    "primary":  "#7B8FA1",   # 主色（藍灰）
    "primary_dark": "#5C7080",
    "accent":   "#A8937A",   # 暖褐
    "green":    "#849E8F",   # 莫蘭迪綠
    "amber":    "#C4A882",   # 莫蘭迪橙
    "red":      "#B98A8A",   # 莫蘭迪紅
    "text":     "#3D3B38",   # 主文字
    "text_sub": "#857F76",   # 次要文字
    "text_hint":"#AEA89F",   # 提示文字
    "sidebar":  "#2E3440",   # 側邊欄
}

def inject_global_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&family=DM+Sans:wght@400;500;600&display=swap');

    html, body, [class*="css"] {{
        font-family: 'DM Sans', 'Noto Sans TC', sans-serif !important;
    }}
    .stApp {{ background: {MORANDI['bg']}; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    .stDeployButton {{ display: none; }}
    .block-container {{
        padding-top: 1.8rem !important;
        padding-bottom: 2rem !important;
        max-width: 1100px !important;
    }}

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {{
        background: {MORANDI['sidebar']} !important;
        border-right: none !important;
    }}
    section[data-testid="stSidebar"] * {{ color: #CBD5E1 !important; }}
    section[data-testid="stSidebar"] .stButton button {{
        background: rgba(255,255,255,0.07) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        color: #E2E8F0 !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
        transition: all 0.2s !important;
    }}
    section[data-testid="stSidebar"] .stButton button:hover {{
        background: rgba(255,255,255,0.14) !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stPageLink"] a {{
        border-radius: 10px !important;
        padding: 8px 12px !important;
        margin: 2px 0 !important;
        transition: background 0.15s !important;
        display: block !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {{
        background: rgba(255,255,255,0.09) !important;
    }}

    /* ── Metric ── */
    [data-testid="stMetric"] {{
        background: {MORANDI['surface']};
        border-radius: 16px;
        padding: 1.2rem 1.4rem !important;
        border: 1px solid {MORANDI['border']};
    }}
    [data-testid="stMetricLabel"] {{ font-size: 12px !important; color: {MORANDI['text_sub']} !important; font-weight: 500 !important; text-transform: uppercase; letter-spacing: 0.06em; }}
    [data-testid="stMetricValue"] {{ font-size: 30px !important; font-weight: 700 !important; color: {MORANDI['text']} !important; }}

    /* ── Primary 按鈕 ── */
    .stButton button[kind="primary"] {{
        background: {MORANDI['primary']} !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        color: white !important;
        box-shadow: 0 2px 8px rgba(123,143,161,0.25) !important;
        transition: all 0.2s !important;
    }}
    .stButton button[kind="primary"]:hover {{
        background: {MORANDI['primary_dark']} !important;
        transform: translateY(-1px) !important;
    }}

    /* ── Secondary 按鈕 ── */
    .stButton button:not([kind]) {{
        border-radius: 10px !important;
        border: 1px solid {MORANDI['border']} !important;
        font-weight: 500 !important;
        background: {MORANDI['surface']} !important;
        color: {MORANDI['text']} !important;
        transition: all 0.15s !important;
    }}
    .stButton button:not([kind]):hover {{
        border-color: {MORANDI['primary']} !important;
        color: {MORANDI['primary']} !important;
    }}

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-border"] {{ display: none !important; }}
    .stTabs [data-baseweb="tab-list"] {{
        background: {MORANDI['surface']};
        border-radius: 14px;
        padding: 5px;
        border: 1px solid {MORANDI['border']};
        gap: 4px;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 10px !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        color: {MORANDI['text_sub']} !important;
        padding: 8px 18px !important;
        border: none !important;
        background: transparent !important;
    }}
    .stTabs [aria-selected="true"] {{
        background: {MORANDI['primary']} !important;
        color: white !important;
    }}
    .stTabs [data-baseweb="tab-panel"] {{ padding-top: 1.2rem !important; }}

    /* ── 輸入欄位 ── */
    .stTextInput input, [data-baseweb="select"] > div {{
        border-radius: 10px !important;
        border: 1px solid {MORANDI['border']} !important;
        background: {MORANDI['surface']} !important;
        font-size: 14px !important;
    }}
    .stTextArea textarea {{
        border-radius: 10px !important;
        border: 1px solid {MORANDI['border']} !important;
        background: {MORANDI['surface']} !important;
        font-size: 14px !important;
    }}

    /* ── Container border ── */
    [data-testid="stVerticalBlockBorderWrapper"] > div {{
        border-radius: 16px !important;
        border: 1px solid {MORANDI['border']} !important;
        background: {MORANDI['surface']} !important;
    }}

    /* ── Expander ── */
    .stExpander {{
        border-radius: 12px !important;
        border: 1px solid {MORANDI['border']} !important;
        background: {MORANDI['surface']} !important;
        overflow: hidden !important;
    }}

    /* ── Divider ── */
    hr {{ border-color: {MORANDI['border']} !important; }}

    /* ── 標題 ── */
    h1 {{ font-size: 1.55rem !important; font-weight: 700 !important; color: {MORANDI['text']} !important; letter-spacing: -0.01em !important; }}
    h2, h3, h4 {{ font-weight: 600 !important; color: {MORANDI['text']} !important; }}

    /* ── 登入頁 ── */
    .ok-login-wrap {{ text-align: center; padding: 5rem 1rem; }}
    .ok-login-icon {{ font-size: 56px; margin-bottom: 1rem; }}
    .ok-login-title {{ font-size: 28px; font-weight: 700; color: {MORANDI['text']}; margin-bottom: 0.4rem; }}
    .ok-login-sub {{ font-size: 15px; color: {MORANDI['text_sub']}; margin-bottom: 2rem; }}

    /* ── Badge ── */
    .ok-badge {{
        display: inline-flex; align-items: center;
        font-size: 14px; font-weight: 600;
        padding: 4px 12px; border-radius: 20px; white-space: nowrap;
    }}
    .ok-badge-blue  {{ background: #DDE4EC; color: {MORANDI['primary_dark']}; }}
    .ok-badge-green {{ background: #D8E5DC; color: #4A7059; }}
    .ok-badge-amber {{ background: #EAE0D0; color: #8C6A3F; }}
    .ok-badge-red   {{ background: #E8D8D8; color: #8A4F4F; }}
    .ok-badge-gray  {{ background: #E5E1DB; color: {MORANDI['text_sub']}; }}

    /* ── 卡片 Grid ── */
    .ok-card-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 14px;
        margin-bottom: 6px;
    }}
    @media (max-width: 768px) {{
        .ok-card-grid {{ grid-template-columns: 1fr !important; }}
    }}
    .ok-grid-card {{
        background: {MORANDI['surface']};
        border-radius: 16px;
        border: 1px solid {MORANDI['border']};
        padding: 1rem 1.1rem 0.9rem;
        cursor: pointer;
        transition: box-shadow 0.2s, transform 0.15s, border-color 0.2s;
        text-decoration: none;
        display: block;
    }}
    .ok-grid-card:hover {{
        box-shadow: 0 6px 20px rgba(0,0,0,0.08);
        transform: translateY(-2px);
        border-color: {MORANDI['primary']};
    }}
    .ok-card-title {{
        font-size: 15px; font-weight: 700;
        color: {MORANDI['text']}; margin-bottom: 8px;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }}
    .ok-card-row {{
        font-size: 12px; color: {MORANDI['text_sub']};
        margin-bottom: 5px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
    }}
    </style>
    """, unsafe_allow_html=True)
