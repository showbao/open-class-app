import streamlit as st

def inject_global_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600&display=swap');

    /* ── 全域字體與背景 ── */
    html, body, [class*="css"] {
        font-family: 'DM Sans', 'Noto Sans TC', sans-serif !important;
    }
    .stApp {
        background: #F5F7FA;
    }

    /* ── 隱藏 Streamlit 預設元素 ── */
    #MainMenu, footer, header { visibility: hidden; }
    .stDeployButton { display: none; }

    /* ── 頂部間距 ── */
    .block-container {
        padding-top: 1.8rem !important;
        padding-bottom: 2rem !important;
        max-width: 1100px !important;
    }

    /* ── Sidebar 美化 ── */
    section[data-testid="stSidebar"] {
        background: #1E2535 !important;
        border-right: none !important;
    }
    section[data-testid="stSidebar"] * {
        color: #CBD5E1 !important;
    }
    section[data-testid="stSidebar"] .stButton button {
        background: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        color: #E2E8F0 !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
        transition: all 0.2s !important;
    }
    section[data-testid="stSidebar"] .stButton button:hover {
        background: rgba(255,255,255,0.15) !important;
    }
    section[data-testid="stSidebar"] [data-testid="stPageLink"] a {
        border-radius: 10px !important;
        padding: 8px 12px !important;
        margin: 2px 0 !important;
        transition: background 0.15s !important;
        display: block !important;
    }
    section[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
        background: rgba(255,255,255,0.1) !important;
    }
    section[data-testid="stSidebar"] [data-testid="stPageLink-active"] a {
        background: rgba(59,130,246,0.3) !important;
        color: #93C5FD !important;
    }

    /* ── Metric 卡片 ── */
    [data-testid="stMetric"] {
        background: white;
        border-radius: 16px;
        padding: 1.2rem 1.4rem !important;
        border: 1px solid #E8ECF2;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }
    [data-testid="stMetricLabel"] { font-size: 12px !important; color: #7C8BA0 !important; font-weight: 500 !important; text-transform: uppercase; letter-spacing: 0.06em; }
    [data-testid="stMetricValue"] { font-size: 32px !important; font-weight: 700 !important; color: #1A2236 !important; line-height: 1.1 !important; }

    /* ── Primary 按鈕 ── */
    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #2563EB, #1D4ED8) !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        padding: 0.55rem 1.2rem !important;
        color: white !important;
        box-shadow: 0 2px 8px rgba(37,99,235,0.3) !important;
        transition: all 0.2s !important;
    }
    .stButton button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 14px rgba(37,99,235,0.4) !important;
    }

    /* ── Secondary 按鈕 ── */
    .stButton button[kind="secondary"],
    .stButton button:not([kind]) {
        border-radius: 10px !important;
        border: 1px solid #DDE2EA !important;
        font-weight: 500 !important;
        background: white !important;
        color: #374151 !important;
        transition: all 0.15s !important;
    }
    .stButton button:not([kind]):hover {
        border-color: #2563EB !important;
        color: #2563EB !important;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        background: white;
        border-radius: 14px;
        padding: 5px;
        border: 1px solid #E8ECF2;
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        color: #64748B !important;
        padding: 8px 18px !important;
        border: none !important;
        background: transparent !important;
    }
    .stTabs [aria-selected="true"] {
        background: #2563EB !important;
        color: white !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 1.2rem !important;
    }

    /* ── 輸入欄位 ── */
    .stTextInput input, .stSelectbox select, .stDateInput input,
    [data-baseweb="select"] > div {
        border-radius: 10px !important;
        border: 1px solid #DDE2EA !important;
        background: white !important;
        font-size: 14px !important;
        transition: border-color 0.15s !important;
    }
    .stTextInput input:focus, [data-baseweb="select"] > div:focus-within {
        border-color: #2563EB !important;
        box-shadow: 0 0 0 3px rgba(37,99,235,0.1) !important;
    }
    .stTextArea textarea {
        border-radius: 10px !important;
        border: 1px solid #DDE2EA !important;
        background: white !important;
        font-size: 14px !important;
    }

    /* ── Container border ── */
    [data-testid="stVerticalBlockBorderWrapper"] > div {
        border-radius: 16px !important;
        border: 1px solid #E8ECF2 !important;
        background: white !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
        transition: box-shadow 0.2s !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] > div:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.08) !important;
    }

    /* ── Expander ── */
    .stExpander {
        border-radius: 12px !important;
        border: 1px solid #E8ECF2 !important;
        background: white !important;
        overflow: hidden !important;
    }
    .stExpander summary {
        font-weight: 500 !important;
        font-size: 14px !important;
        padding: 12px 16px !important;
    }

    /* ── Success / Warning / Info ── */
    .stSuccess, .stWarning, .stInfo, .stError {
        border-radius: 10px !important;
        font-size: 13px !important;
        border: none !important;
    }

    /* ── Divider ── */
    hr { border-color: #EEF1F7 !important; }

    /* ── Caption ── */
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #7C8BA0 !important;
        font-size: 12px !important;
    }

    /* ── 頁面標題 ── */
    h1 { 
        font-size: 1.6rem !important;
        font-weight: 700 !important;
        color: #1A2236 !important;
        letter-spacing: -0.02em !important;
    }
    h2 { font-weight: 600 !important; color: #1A2236 !important; }
    h3 { font-weight: 600 !important; color: #1A2236 !important; }

    /* ── Radio ── */
    .stRadio label { font-size: 14px !important; }
    .stRadio [data-testid="stWidgetLabel"] { font-weight: 600 !important; }

    /* ── Spinner ── */
    .stSpinner { color: #2563EB !important; }

    /* ── 自訂卡片 HTML ── */
    .ok-card {
        background: white;
        border-radius: 16px;
        border: 1px solid #E8ECF2;
        padding: 1rem 1.25rem;
        margin-bottom: 10px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        transition: box-shadow 0.2s, transform 0.15s;
        cursor: default;
    }
    .ok-card:hover {
        box-shadow: 0 6px 20px rgba(0,0,0,0.09);
        transform: translateY(-1px);
    }
    .ok-card-title {
        font-size: 15px;
        font-weight: 600;
        color: #1A2236;
        margin-bottom: 4px;
    }
    .ok-card-meta {
        font-size: 12px;
        color: #7C8BA0;
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
        align-items: center;
    }
    .ok-badge {
        display: inline-flex;
        align-items: center;
        font-size: 11px;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 20px;
        white-space: nowrap;
    }
    .ok-badge-blue  { background: #EFF6FF; color: #1D4ED8; }
    .ok-badge-green { background: #F0FDF4; color: #15803D; }
    .ok-badge-amber { background: #FFFBEB; color: #B45309; }
    .ok-badge-red   { background: #FEF2F2; color: #DC2626; }
    .ok-badge-gray  { background: #F1F5F9; color: #475569; }

    /* ── 登入頁 ── */
    .ok-login-wrap {
        text-align: center;
        padding: 5rem 1rem;
    }
    .ok-login-icon {
        font-size: 56px;
        margin-bottom: 1rem;
    }
    .ok-login-title {
        font-size: 28px;
        font-weight: 700;
        color: #1A2236;
        margin-bottom: 0.4rem;
    }
    .ok-login-sub {
        font-size: 15px;
        color: #7C8BA0;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)
