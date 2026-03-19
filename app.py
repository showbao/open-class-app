import streamlit as st
from utils.auth import require_login, logout
from utils.sheets import (get_sessions_all, get_sessions_by_teacher,
                           get_observations_by_session, is_admin, has_observation)
import datetime

st.set_page_config(
    page_title="公開觀課平台",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

user = require_login()

with st.sidebar:
    st.markdown(f"### 👤 {user['name']}")
    st.caption(user["email"])
    if is_admin(user["email"]):
        st.info("🔑 主管身份")
    st.divider()
    if st.button("登出", use_container_width=True):
        logout()

st.title("📋 公開觀課平台")
st.markdown(f"歡迎回來，**{user['name']}**！")
st.divider()

# ── 個人化統計 ────────────────────────────────────────────
sessions_all = get_sessions_all()
my_sessions = sessions_all[sessions_all["teacher_email"] == user["email"]] if not sessions_all.empty else sessions_all

# 待填省思：有觀課紀錄但尚未填省思
pending_reflection = 0
if not my_sessions.empty:
    for _, row in my_sessions.iterrows():
        obs = get_observations_by_session(row["session_id"])
        if not obs.empty and not str(row.get("teacher_reflection","")).strip():
            pending_reflection += 1

# 觀課者人次：自己被觀課的總人次
total_observers = 0
if not my_sessions.empty:
    for _, row in my_sessions.iterrows():
        obs = get_observations_by_session(row["session_id"])
        total_observers += len(obs)

# 自己尚未填寫觀課紀錄的場次（身為觀課者）
pending_obs = 0
if not sessions_all.empty:
    today = datetime.date.today()
    delta = datetime.timedelta(days=30)
    for _, row in sessions_all.iterrows():
        if row["teacher_email"] == user["email"]:
            continue
        try:
            d = datetime.datetime.strptime(str(row["date"]), "%Y/%m/%d").date()
        except:
            continue
        if d <= today and not has_observation(row["session_id"], user["email"]):
            # 只算已結束的場次
            if d < today:
                pending_obs += 1

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("本學期已登記場次", len(my_sessions))
with col2:
    st.metric("待填寫教學省思", pending_reflection,
              delta="需填寫" if pending_reflection > 0 else None,
              delta_color="inverse" if pending_reflection > 0 else "off")
with col3:
    st.metric("被觀課者人次", total_observers)
with col4:
    st.metric("待補填觀課紀錄", pending_obs,
              delta="需補填" if pending_obs > 0 else None,
              delta_color="inverse" if pending_obs > 0 else "off")

st.divider()
st.markdown("#### 快速入口")

r1c1, r1c2, r1c3 = st.columns(3)
with r1c1:
    st.page_link("pages/1_觀課總覽.py", label="📋 觀課總覽", use_container_width=True)
with r1c2:
    st.page_link("pages/5_我的被觀課紀錄.py", label="📂 我的被觀課紀錄", use_container_width=True)
with r1c3:
    st.page_link("pages/7_歷年紀錄.py", label="📊 歷年觀課彙整", use_container_width=True)

if is_admin(user["email"]):
    st.page_link("pages/6_主管總覽.py", label="🔑 主管總覽", use_container_width=True)
