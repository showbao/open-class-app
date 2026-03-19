import streamlit as st
from utils.auth import require_login, logout
from utils.sheets import is_admin

st.set_page_config(
    page_title="公開觀課平台",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

user = require_login()

with st.sidebar:
    st.markdown(f"### 👤 {user['name']}")
    st.caption(user["email"])
    if is_admin(user["email"]):
        st.info("🔑 主管身份")
    st.divider()
    if st.button("登出", use_container_width=True):
        logout()

# 登入後直接跳到觀課總覽
st.switch_page("pages/1_觀課總覽.py")
