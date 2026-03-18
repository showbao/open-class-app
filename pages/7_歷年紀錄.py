import streamlit as st
import json
from utils.auth import require_login
from utils.sheets import (get_sessions_all, get_observations_by_session,
                           get_indicator_name, get_sub_indicators,
                           is_admin, get_all_teachers)
from utils.drive import decode_photo_urls

st.set_page_config(page_title="歷年紀錄", page_icon="📊", layout="wide")
user = require_login()

st.title("📊 歷年公開觀課彙整")
st.divider()

sessions_all = get_sessions_all()

if is_admin(user["email"]):
    teachers_df = get_all_teachers()
    teacher_options = {row["email"]: row["name"] for _, row in teachers_df.iterrows()}
    teacher_options = {"__self__": f"（我自己）{user['name']}"} | teacher_options
    selected_email = st.selectbox(
        "查看教師",
        options=list(teacher_options.keys()),
        format_func=lambda e: teacher_options[e]
    )
    target_email = user["email"] if selected_email == "__self__" else selected_email
    target_name = teacher_options[selected_email]
else:
    target_email = user["email"]
    target_name = user["name"]

st.markdown(f"#### {target_name} 的歷年觀課紀錄")
st.divider()

if sessions_all.empty:
    st.info("目前尚無任何觀課場次")
    st.stop()

my_sessions = sessions_all[sessions_all["teacher_email"] == target_email].copy()

if my_sessions.empty:
    st.info(f"{target_name} 尚無公開觀課紀錄")
    st.stop()

my_sessions["year"] = my_sessions["date"].apply(lambda d: str(d)[:4] if d else "未知")
years = sorted(my_sessions["year"].unique().tolist(), reverse=True)
filter_year = st.selectbox("篩選年度", ["全部"] + [f"{y}年" for y in years])

for year in years:
    if filter_year != "全部" and filter_year != f"{year}年":
        continue

    year_sessions = my_sessions[my_sessions["year"] == year].sort_values("date", ascending=False)
    st.markdown(f"### {year} 年")

    for _, row in year_sessions.iterrows():
        obs_df = get_observations_by_session(row["session_id"])
        obs_count = len(obs_df)
        ind_name = get_indicator_name(row["indicator_id"])
        has_reflection = bool(str(row.get("teacher_reflection", "")).strip())

        with st.expander(
            f"📅 {row['date']}　{row['period']}　{row['subject']}｜{row['unit']}　"
            f"（{obs_count} 位觀課者）{'　✅ 已填省思' if has_reflection else ''}"
        ):
            st.caption(f"觀課指標：{row['indicator_id']}．{ind_name}")
            sub_items = get_sub_indicators(row["indicator_id"])

            if obs_df.empty:
                st.info("本場次尚無觀課紀錄")
            else:
                for _, obs in obs_df.iterrows():
                    st.markdown(f"**👤 {obs['observer_name']}**　（{obs['submitted_at']}）")
                    try:
                        scores = json.loads(obs["indicator_scores"])
                    except:
                        scores = {}
                    if scores:
                        score_cols = st.columns(len(sub_items))
                        for i, sub in enumerate(sub_items):
                            with score_cols[i]:
                                st.metric(sub["sub_id"], scores.get(sub["sub_id"], "-"))
                    st.markdown("*質性記錄：*" + (obs["qualitative_notes"] or "（未填）"))
                    st.markdown("*觀課者省思：*" + (obs["self_reflection"] or "（未填）"))
                    photos = decode_photo_urls(obs["photo_urls"])
                    if photos:
                        img_cols = st.columns(min(len(photos), 4))
                        for i, b64 in enumerate(photos):
                            with img_cols[i % 4]:
                                st.image(b64, use_container_width=True)
                    st.divider()

            if has_reflection:
                st.markdown("**📝 教學省思**")
                st.markdown(row["teacher_reflection"])
                st.markdown("**🔧 未來調整方向**")
                st.markdown(row["teacher_adjustment"])
