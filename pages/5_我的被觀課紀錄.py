import streamlit as st
import json
from utils.auth import require_login
from utils.sheets import (get_sessions_by_teacher, get_observations_by_session,
                           get_indicator_name, update_teacher_reflection, get_sub_indicators)

st.set_page_config(page_title="我的被觀課紀錄", page_icon="📂", layout="wide")
user = require_login()

st.title("📂 我的被觀課紀錄")
st.caption("點選場次查看觀課者紀錄，並填寫您的教學省思。")
st.divider()

sessions = get_sessions_by_teacher(user["email"])

if sessions.empty:
    st.info("您尚未登記任何公開觀課場次。")
    st.page_link("pages/1_登記觀課.py", label="✏️ 前往登記")
    st.stop()

# 排序：最新在前
sessions = sessions.sort_values("created_at", ascending=False).reset_index(drop=True)

selected_id = st.selectbox(
    "選擇場次",
    options=sessions["session_id"].tolist(),
    format_func=lambda sid: (
        lambda r: f"{r['date']} {r['period']} {r['subject']}｜{r['unit']}"
    )(sessions[sessions["session_id"] == sid].iloc[0])
)

st.divider()

row = sessions[sessions["session_id"] == selected_id].iloc[0]
obs_df = get_observations_by_session(selected_id)
ind_name = get_indicator_name(row["indicator_id"])
sub_items = get_sub_indicators(row["indicator_id"])

with st.container(border=True):
    st.markdown(f"**{row['subject']}｜{row['unit']}**")
    st.caption(f"📅 {row['date']}　🕐 {row['period']}　觀課指標：{row['indicator_id']}．{ind_name}")

if obs_df.empty:
    st.info("本場次尚無觀課者填寫紀錄。")
else:
    st.markdown(f"#### 觀課紀錄（共 {len(obs_df)} 位觀課者）")
    for _, obs in obs_df.iterrows():
        with st.expander(f"👤 {obs['observer_name']}　（{obs['submitted_at']}）"):

            # 量表分數
            try:
                scores = json.loads(obs["indicator_scores"])
            except:
                scores = {}

            if scores:
                st.markdown(f"**{row['indicator_id']}．{ind_name} — 量表結果**")
                score_cols = st.columns(len(sub_items))
                for i, sub in enumerate(sub_items):
                    with score_cols[i]:
                        v = scores.get(sub["sub_id"], "-")
                        st.metric(label=f"{sub['sub_id']}", value=v)

            st.divider()
            st.markdown("**觀課質性記錄**")
            st.markdown(obs["qualitative_notes"] or "（未填寫）")

            st.markdown("**觀課者自我省思**")
            st.markdown(obs["self_reflection"] or "（未填寫）")

            # 照片
            if obs["photo_urls"]:
                st.markdown("**課堂照片**")
                urls = [u.strip() for u in obs["photo_urls"].split(",") if u.strip()]
                img_cols = st.columns(min(len(urls), 4))
                for i, url in enumerate(urls):
                    with img_cols[i % 4]:
                        st.image(url, use_container_width=True)

st.divider()

# ── 被觀課者填寫省思 ──────────────────────────────────────
st.markdown("#### 您的教學省思")
already_reflection = str(row.get("teacher_reflection", "") or "")
already_adjustment = str(row.get("teacher_adjustment", "") or "")

with st.form("reflection_form"):
    reflection = st.text_area(
        "教學省思",
        value=already_reflection,
        placeholder="看完觀課者的紀錄後，您對這堂課有哪些反思？",
        height=120
    )
    adjustment = st.text_area(
        "未來可調整的方向",
        value=already_adjustment,
        placeholder="未來在教學上有哪些可以調整或改進的方向？",
        height=100
    )
    save = st.form_submit_button("💾 儲存省思", use_container_width=True, type="primary")

if save:
    if not reflection.strip() and not adjustment.strip():
        st.error("請至少填寫教學省思或未來調整方向")
    else:
        with st.spinner("儲存中…"):
            update_teacher_reflection(selected_id, reflection.strip(), adjustment.strip())
        st.success("✅ 省思已儲存！")
        st.rerun()
