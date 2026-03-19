import streamlit as st
import datetime
from utils.auth import require_login
from utils.sheets import (get_sessions_all, get_sessions_by_teacher,
                           get_observations_by_session, get_indicator_name,
                           add_session, get_indicators, has_observation)

st.set_page_config(page_title="觀課總覽", page_icon="📋", layout="wide")
user = require_login()

SUBJECTS = ["國語","數學","英語","社會","自然","生活","美術","音樂","體育","健康","資訊","綜合","彈性"]
PERIODS  = [f"第{i}節" for i in range(1, 8)]
INDICATOR_COLORS = {"A": "🔵", "B": "🟢", "C": "🟡", "D": "🟠"}

st.title("📋 觀課總覽")
st.divider()

tab1, tab2, tab3 = st.tabs(["📌 我的觀課列表", "🏫 學校近期觀課", "📁 已結束觀課"])

# ════════════════════════════════════════
# 分頁一：我的觀課列表
# ════════════════════════════════════════
with tab1:
    my_sessions = get_sessions_by_teacher(user["email"])

    # ── 登記觀課按鈕 ──
    if st.button("➕ 登記公開觀課", type="primary"):
        st.session_state["show_register"] = True

    # ── 登記觀課彈跳視窗（用 expander 模擬） ──
    if st.session_state.get("show_register", False):
        with st.container(border=True):
            st.markdown("### ✏️ 登記公開觀課")

            indicators_df = get_indicators()
            indicator_options = indicators_df.drop_duplicates("indicator_id")[["indicator_id","indicator_name"]].values.tolist()
            indicator_labels = {row[0]: f"{row[0]}．{row[1]}" for row in indicator_options}

            r_date = st.date_input("觀課日期", min_value=datetime.date.today(), key="r_date")
            rc1, rc2 = st.columns(2)
            with rc1:
                r_period = st.selectbox("節次", PERIODS, key="r_period")
            with rc2:
                r_subject = st.selectbox("觀課科目", SUBJECTS, key="r_subject")

            r_unit = st.text_input("觀課單元", placeholder="例如：水的三態變化", key="r_unit")

            # 大指標選擇（在 form 外，即時連動）
            st.markdown("**選擇觀課大指標（擇一）**")
            r_indicator = st.radio(
                "觀課大指標",
                options=list(indicator_labels.keys()),
                format_func=lambda x: indicator_labels[x],
                horizontal=True,
                label_visibility="collapsed",
                key="r_indicator"
            )

            # 即時顯示子項目
            sub_items = indicators_df[indicators_df["indicator_id"] == r_indicator][["sub_id","sub_name"]].values.tolist()
            with st.expander(f"📌 {indicator_labels[r_indicator]} — 子項目（共 {len(sub_items)} 項）", expanded=True):
                for sub in sub_items:
                    st.markdown(f"- **{sub[0]}**　{sub[1]}")

            bc1, bc2 = st.columns(2)
            with bc1:
                if st.button("✅ 確認送出登記", type="primary", use_container_width=True, key="submit_register"):
                    if not r_unit.strip():
                        st.error("請填寫觀課單元名稱")
                    else:
                        with st.spinner("儲存中…"):
                            session_id = add_session(
                                teacher_email=user["email"],
                                teacher_name=user["name"],
                                date=r_date.strftime("%Y/%m/%d"),
                                period=r_period,
                                subject=r_subject,
                                unit=r_unit.strip(),
                                indicator_id=r_indicator,
                            )
                        st.success(f"✅ 登記成功！場次編號：`{session_id}`")
                        st.session_state["show_register"] = False
                        st.rerun()
            with bc2:
                if st.button("取消", use_container_width=True, key="cancel_register"):
                    st.session_state["show_register"] = False
                    st.rerun()

    st.divider()

    # ── 我的場次列表 ──
    if my_sessions.empty:
        st.info("您尚未登記任何公開觀課場次，請點上方「登記公開觀課」新增。")
    else:
        my_sessions = my_sessions.sort_values("date", ascending=False).reset_index(drop=True)
        st.markdown(f"共 **{len(my_sessions)}** 場")

        for _, row in my_sessions.iterrows():
            obs_df = get_observations_by_session(row["session_id"])
            obs_count = len(obs_df)
            ind_name = get_indicator_name(row["indicator_id"])
            color = INDICATOR_COLORS.get(row["indicator_id"], "⚪")
            has_reflection = bool(str(row.get("teacher_reflection","")).strip())

            with st.container(border=True):
                c1, c2, c3 = st.columns([4, 1, 1])
                with c1:
                    st.markdown(f"**{row['subject']}｜{row['unit']}**")
                    st.caption(f"📅 {row['date']}　🕐 {row['period']}　{color} {row['indicator_id']}．{ind_name}　｜　👥 {obs_count} 人觀課")
                with c2:
                    if has_reflection:
                        st.success("已填省思")
                    else:
                        st.warning("待填省思")
                with c3:
                    if st.button("查看紀錄", key=f"view_my_{row['session_id']}"):
                        st.session_state["view_session_id"] = row["session_id"]
                        st.switch_page("pages/5_我的被觀課紀錄.py")

# ════════════════════════════════════════
# 分頁二：學校近期觀課（前後30天）
# ════════════════════════════════════════
with tab2:
    sessions_all = get_sessions_all()
    today = datetime.date.today()
    delta = datetime.timedelta(days=30)

    if sessions_all.empty:
        st.info("目前尚無觀課場次")
    else:
        def parse_date(d):
            try:
                return datetime.datetime.strptime(str(d), "%Y/%m/%d").date()
            except:
                return None

        sessions_all["date_obj"] = sessions_all["date"].apply(parse_date)
        recent = sessions_all[
            sessions_all["date_obj"].apply(
                lambda d: d is not None and (today - delta) <= d <= (today + delta)
            )
        ].sort_values("date_obj").reset_index(drop=True)

        if recent.empty:
            st.info("近期（前後30天）無觀課場次")
        else:
            st.markdown(f"共 **{len(recent)}** 場")
            for _, row in recent.iterrows():
                obs_df = get_observations_by_session(row["session_id"])
                obs_count = len(obs_df)
                is_own = row["teacher_email"] == user["email"]
                already = has_observation(row["session_id"], user["email"])
                ind_name = get_indicator_name(row["indicator_id"])
                color = INDICATOR_COLORS.get(row["indicator_id"], "⚪")

                with st.container(border=True):
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.markdown(f"**{row['subject']}｜{row['unit']}**")
                        st.caption(f"📅 {row['date']}　🕐 {row['period']}　👤 {row['teacher_name']}　{color} {row['indicator_id']}．{ind_name}　｜　👥 {obs_count} 人")
                    with c2:
                        if is_own:
                            st.info("自己的課")
                        elif already:
                            st.success("已填寫")
                        else:
                            if st.button("填寫觀課紀錄 →", key=f"obs_{row['session_id']}", type="primary"):
                                st.session_state["selected_session"] = row.to_dict()
                                st.switch_page("pages/4_填寫觀課紀錄.py")

# ════════════════════════════════════════
# 分頁三：已結束觀課（近30筆）
# ════════════════════════════════════════
with tab3:
    sessions_all2 = get_sessions_all()
    today2 = datetime.date.today()

    if sessions_all2.empty:
        st.info("目前尚無觀課場次")
    else:
        sessions_all2["date_obj"] = sessions_all2["date"].apply(
            lambda d: datetime.datetime.strptime(str(d), "%Y/%m/%d").date() if d else None
        )
        ended = sessions_all2[
            sessions_all2["date_obj"].apply(lambda d: d is not None and d < today2)
        ].sort_values("date_obj", ascending=False).head(30).reset_index(drop=True)

        if ended.empty:
            st.info("尚無已結束的觀課場次")
        else:
            st.markdown(f"最近 **{len(ended)}** 場（已結束）")
            for _, row in ended.iterrows():
                obs_df = get_observations_by_session(row["session_id"])
                obs_count = len(obs_df)
                ind_name = get_indicator_name(row["indicator_id"])
                color = INDICATOR_COLORS.get(row["indicator_id"], "⚪")
                teacher_done = bool(str(row.get("teacher_reflection","")).strip())
                obs_done = obs_count > 0

                with st.container(border=True):
                    c1, c2, c3 = st.columns([4, 1, 1])
                    with c1:
                        st.markdown(f"**{row['subject']}｜{row['unit']}**")
                        st.caption(f"📅 {row['date']}　🕐 {row['period']}　👤 {row['teacher_name']}　{color} {row['indicator_id']}．{ind_name}")
                    with c2:
                        st.write("觀課者：" + ("✅" if obs_done else "⬜"))
                    with c3:
                        st.write("省思：" + ("✅" if teacher_done else "⬜"))
