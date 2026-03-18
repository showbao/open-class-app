import streamlit as st
import datetime
from utils.auth import require_login
from utils.sheets import get_sessions_by_teacher, get_indicator_name

st.set_page_config(page_title="我的觀課場次", page_icon="📅", layout="wide")
user = require_login()

st.title("📅 我的觀課場次")
st.divider()

sessions = get_sessions_by_teacher(user["email"])

if sessions.empty:
    st.info("尚未登記任何公開觀課場次，請前往「登記觀課」新增。")
    st.page_link("pages/1_登記觀課.py", label="✏️ 前往登記")
else:
    sessions = sessions.sort_values("date", ascending=False).reset_index(drop=True)

    col1, col2 = st.columns(2)
    with col1:
        subjects = ["全部"] + sorted(sessions["subject"].unique().tolist())
        filter_subject = st.selectbox("篩選科目", subjects)
    with col2:
        indicators = ["全部", "A 課程設計", "B 教學策略", "C 學生學習", "D 班級經營"]
        filter_indicator = st.selectbox("篩選指標", indicators)

    filtered = sessions.copy()
    if filter_subject != "全部":
        filtered = filtered[filtered["subject"] == filter_subject]
    if filter_indicator != "全部":
        filtered = filtered[filtered["indicator_id"] == filter_indicator[0]]

    st.markdown(f"共 **{len(filtered)}** 場")
    st.divider()

    INDICATOR_COLORS = {"A": "🔵", "B": "🟢", "C": "🟡", "D": "🟠"}

    for _, row in filtered.iterrows():
        ind_name = get_indicator_name(row["indicator_id"])
        color = INDICATOR_COLORS.get(row["indicator_id"], "⚪")
        has_reflection = bool(str(row.get("teacher_reflection", "")).strip())

        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"**{row['subject']}｜{row['unit']}**")
                st.caption(
                    f"📅 {row['date']}　🕐 {row['period']}　"
                    f"{color} {row['indicator_id']}．{ind_name}"
                )
            with c2:
                if has_reflection:
                    st.success("已填省思")
                else:
                    st.warning("待填省思")
