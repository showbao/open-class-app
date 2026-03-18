import streamlit as st
from utils.auth import require_login, logout, is_admin
from utils.sheets import get_sessions_all, get_observations_by_session, is_admin

st.set_page_config(
    page_title="公開觀課平台",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── 全域樣式 ──────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebarNav"] { font-size: 15px; }
.block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# ── 登入驗證 ──────────────────────────────────────────────
user = require_login()

# ── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"### 👤 {user['name']}")
    st.caption(user["email"])
    if is_admin(user["email"]):
        st.info("🔑 主管身份")
    st.divider()
    if st.button("登出", use_container_width=True):
        logout()

# ── 首頁儀表板 ────────────────────────────────────────────
st.title("📋 公開觀課平台")
st.markdown("歡迎回來，**{}**！".format(user["name"]))
st.divider()

# 統計數字
sessions_df = get_sessions_all()
my_sessions = sessions_df[sessions_df["teacher_email"] == user["email"]] if not sessions_df.empty else sessions_df

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("本學期登記場次", len(my_sessions))

with col2:
    # 計算待填省思（有觀課紀錄但自己尚未填省思）
    pending = 0
    if not my_sessions.empty:
        for _, row in my_sessions.iterrows():
            obs = get_observations_by_session(row["session_id"])
            if not obs.empty and not row["teacher_reflection"]:
                pending += 1
    st.metric("待填寫省思", pending, delta="請盡快補填" if pending > 0 else None,
              delta_color="inverse" if pending > 0 else "off")

with col3:
    total_obs = 0
    if not my_sessions.empty:
        for _, row in my_sessions.iterrows():
            obs = get_observations_by_session(row["session_id"])
            total_obs += len(obs)
    st.metric("觀課者人次", total_obs)

with col4:
    total_sessions = len(sessions_df) if not sessions_df.empty else 0
    st.metric("全校本學期場次", total_sessions)

st.divider()
st.markdown("#### 快速入口")

r1c1, r1c2, r1c3 = st.columns(3)
with r1c1:
    st.page_link("pages/1_登記觀課.py", label="✏️ 登記公開觀課", use_container_width=True)
with r1c2:
    st.page_link("pages/2_我的行事曆.py", label="📅 我的觀課行事曆", use_container_width=True)
with r1c3:
    st.page_link("pages/3_近期場次.py", label="👀 近期觀課場次", use_container_width=True)

r2c1, r2c2, r2c3 = st.columns(3)
with r2c1:
    st.page_link("pages/5_我的被觀課紀錄.py", label="📂 我的被觀課紀錄", use_container_width=True)
with r2c2:
    st.page_link("pages/7_歷年紀錄.py", label="📊 歷年觀課彙整", use_container_width=True)
with r2c3:
    if is_admin(user["email"]):
        st.page_link("pages/6_主管總覽.py", label="🔑 主管總覽", use_container_width=True)
