import streamlit as st
import json
from utils.auth import require_admin
from utils.sheets import (get_sessions_all, get_observations_by_session,
                           get_indicator_name, get_sub_indicators)
from utils.drive import decode_photo_urls

st.set_page_config(page_title="主管總覽", page_icon="🔑", layout="wide")
user = require_admin()

st.title("🔑 主管總覽")
st.caption("全校公開觀課紀錄一覽，可查看每場次填寫完成狀態。")
st.divider()

sessions = get_sessions_all()

if sessions.empty:
    st.info("目前尚無任何觀課場次")
    st.stop()

sessions = sessions.sort_values("date", ascending=False).reset_index(drop=True)

fc1, fc2, fc3 = st.columns(3)
with fc1:
    teachers = ["全部"] + sorted(sessions["teacher_name"].unique().tolist())
    filter_teacher = st.selectbox("篩選教師", teachers)
with fc2:
    subjects = ["全部"] + sorted(sessions["subject"].unique().tolist())
    filter_subject = st.selectbox("篩選科目", subjects)
with fc3:
    filter_indicator = st.selectbox("篩選指標", ["全部", "A 課程設計", "B 教學策略", "C 學生學習", "D 班級經營"])

filtered = sessions.copy()
if filter_teacher != "全部":
    filtered = filtered[filtered["teacher_name"] == filter_teacher]
if filter_subject != "全部":
    filtered = filtered[filtered["subject"] == filter_subject]
if filter_indicator != "全部":
    filtered = filtered[filtered["indicator_id"] == filter_indicator[0]]

st.divider()
st.markdown(f"#### 共 {len(filtered)} 場")

for _, row in filtered.iterrows():
    obs_df = get_observations_by_session(row["session_id"])
    obs_filled = len(obs_df) > 0
    teacher_filled = bool(str(row.get("teacher_reflection", "")).strip())
    obs_icon = "✅" if obs_filled else "⬜"
    teacher_icon = "✅" if teacher_filled else "⬜"
    ind_name = get_indicator_name(row["indicator_id"])

    with st.container(border=True):
        hc1, hc2, hc3, hc4 = st.columns([3, 1, 1, 1])
        with hc1:
            st.markdown(f"**{row['subject']}｜{row['unit']}**")
            st.caption(f"📅 {row['date']}　🕐 {row['period']}　👤 {row['teacher_name']}　｜　{row['indicator_id']}．{ind_name}")
        with hc2:
            st.metric("觀課者填寫", obs_icon)
        with hc3:
            st.metric("被觀課者省思", teacher_icon)
        with hc4:
            if st.button("查看詳情", key=f"detail_{row['session_id']}"):
                st.session_state["admin_session"] = row.to_dict()

if "admin_session" in st.session_state:
    s = st.session_state["admin_session"]
    obs_df = get_observations_by_session(s["session_id"])
    sub_items = get_sub_indicators(s["indicator_id"])
    ind_name = get_indicator_name(s["indicator_id"])

    st.divider()
    st.markdown(f"### 📋 {s['subject']}｜{s['unit']} 完整紀錄")
    st.caption(f"{s['date']} {s['period']} · {s['teacher_name']} · {s['indicator_id']}．{ind_name}")

    if obs_df.empty:
        st.info("本場次尚無觀課者填寫紀錄")
    else:
        for _, obs in obs_df.iterrows():
            with st.expander(f"👤 觀課者：{obs['observer_name']}"):
                try:
                    scores = json.loads(obs["indicator_scores"])
                except:
                    scores = {}
                if scores:
                    score_cols = st.columns(len(sub_items))
                    for i, sub in enumerate(sub_items):
                        with score_cols[i]:
                            st.metric(sub["sub_id"], scores.get(sub["sub_id"], "-"))
                st.markdown("**質性記錄**")
                st.markdown(obs["qualitative_notes"] or "（未填寫）")
                st.markdown("**觀課者省思**")
                st.markdown(obs["self_reflection"] or "（未填寫）")
                photos = decode_photo_urls(obs["photo_urls"])
                if photos:
                    st.markdown("**課堂照片**")
                    img_cols = st.columns(min(len(photos), 4))
                    for i, b64 in enumerate(photos):
                        with img_cols[i % 4]:
                            st.image(b64, use_container_width=True)

    teacher_reflection = str(s.get("teacher_reflection", "") or "")
    teacher_adjustment = str(s.get("teacher_adjustment", "") or "")
    if teacher_reflection or teacher_adjustment:
        st.markdown("---")
        st.markdown("**被觀課者教學省思**")
        st.markdown(teacher_reflection or "（未填寫）")
        st.markdown("**未來調整方向**")
        st.markdown(teacher_adjustment or "（未填寫）")
    else:
        st.warning("被觀課者尚未填寫省思")

    if st.button("關閉詳情"):
        del st.session_state["admin_session"]
        st.rerun()
