import streamlit as st
import datetime
import pandas as pd
from utils.auth import require_login
from utils.sheets import get_sessions_all, get_observations_by_session, get_indicator_name, has_observation

st.set_page_config(page_title="近期場次", page_icon="👀", layout="wide")
user = require_login()

st.title("👀 近期公開觀課場次")
st.caption("列出前後 30 天內的所有公開觀課場次，點選場次可進入填寫觀課紀錄。")
st.divider()

sessions = get_sessions_all()

if sessions.empty:
    st.info("目前尚無觀課場次")
else:
    today = datetime.date.today()
    delta = datetime.timedelta(days=30)

    def parse_date(d):
        try:
            return datetime.datetime.strptime(str(d), "%Y/%m/%d").date()
        except:
            return None

    sessions["date_obj"] = sessions["date"].apply(parse_date)
    recent = sessions[
        sessions["date_obj"].apply(lambda d: d is not None and (today - delta) <= d <= (today + delta))
    ].sort_values("date_obj").reset_index(drop=True)

    if recent.empty:
        st.info("近期（前後30天）無觀課場次")
    else:
        for _, row in recent.iterrows():
            obs_df = get_observations_by_session(row["session_id"])
            obs_count = len(obs_df)
            already = has_observation(row["session_id"], user["email"])
            is_own = row["teacher_email"] == user["email"]

            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"**{row['subject']}｜{row['unit']}**")
                    st.caption(f"📅 {row['date']}　🕐 {row['period']}　👤 {row['teacher_name']}")
                    ind_name = get_indicator_name(row["indicator_id"])
                    st.caption(f"觀課指標：{row['indicator_id']}．{ind_name}　｜　已有 {obs_count} 人觀課")
                with c2:
                    if is_own:
                        st.info("自己的課")
                    elif already:
                        st.success("已填寫")
                        if st.button("查看紀錄", key=f"view_{row['session_id']}"):
                            st.session_state["selected_session"] = row.to_dict()
                            st.switch_page("pages/4_填寫觀課紀錄.py")
                    else:
                        if st.button("填寫觀課紀錄 →", key=f"obs_{row['session_id']}", type="primary"):
                            st.session_state["selected_session"] = row.to_dict()
                            st.switch_page("pages/4_填寫觀課紀錄.py")
