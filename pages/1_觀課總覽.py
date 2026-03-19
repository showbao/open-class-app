import streamlit as st
import datetime
from utils.auth import require_login, logout
from utils.sheets import (get_sessions_all, get_sessions_by_teacher,
                           get_observations_all, get_observations_by_session,
                           get_indicator_name, add_session, get_indicators,
                           has_observation, is_admin)

st.set_page_config(page_title="觀課總覽", page_icon="📋", layout="wide")
user = require_login()

SUBJECTS = ["國語","數學","英語","社會","自然","生活","美術","音樂","體育","健康","資訊","綜合","彈性"]
PERIODS  = [f"第{i}節" for i in range(1, 8)]
INDICATOR_COLORS = {"A": "🔵", "B": "🟢", "C": "🟡", "D": "🟠"}

# ── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"### 👤 {user['name']}")
    st.caption(user["email"])
    if is_admin(user["email"]):
        st.info("🔑 主管身份")
    st.divider()
    st.page_link("pages/1_觀課總覽.py",        label="📋 總覽")
    st.page_link("pages/5_我的被觀課紀錄.py",  label="📂 我的被觀課紀錄")
    st.page_link("pages/7_歷年紀錄.py",        label="📊 歷年觀課彙整")
    if is_admin(user["email"]):
        st.page_link("pages/6_主管總覽.py",    label="🔑 主管總覽")
    st.divider()
    if st.button("登出", use_container_width=True):
        logout()

# ── 個人化統計（一次讀取） ────────────────────────────────
sessions_df = get_sessions_all()
obs_df = get_observations_all()
today = datetime.date.today()
my_sessions = sessions_df[sessions_df["teacher_email"] == user["email"]] if not sessions_df.empty else sessions_df

pending_reflection = 0
if not my_sessions.empty and not obs_df.empty:
    for _, row in my_sessions.iterrows():
        has_obs = not obs_df[obs_df["session_id"] == row["session_id"]].empty
        no_ref = not str(row.get("teacher_reflection","")).strip()
        if has_obs and no_ref:
            pending_reflection += 1

total_observers = 0
if not my_sessions.empty and not obs_df.empty:
    total_observers = len(obs_df[obs_df["session_id"].isin(my_sessions["session_id"].tolist())])

st.title("📋 觀課總覽")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("本學期已登記場次", len(my_sessions))
with col2:
    st.metric("待填寫教學省思", pending_reflection,
              delta="需填寫" if pending_reflection > 0 else None,
              delta_color="inverse" if pending_reflection > 0 else "off")
with col3:
    st.metric("被觀課者人次", total_observers)

st.divider()

tab1, tab2, tab3 = st.tabs(["📌 我的觀課列表", "🏫 學校近期觀課", "📁 已結束觀課"])

# ════════════════════════════════════════
# 分頁一：我的觀課列表
# ════════════════════════════════════════
with tab1:
    if st.button("➕ 登記公開觀課", type="primary"):
        st.session_state["show_register"] = not st.session_state.get("show_register", False)

    if st.session_state.get("show_register", False):
        with st.container(border=True):
            st.markdown("### ✏️ 登記公開觀課")
            indicators_df = get_indicators()
            indicator_options = indicators_df.drop_duplicates("indicator_id")[["indicator_id","indicator_name"]].values.tolist()
            indicator_labels = {row[0]: f"{row[0]}．{row[1]}" for row in indicator_options}

            rc1, rc2, rc3 = st.columns(3)
            with rc1:
                r_date = st.date_input("觀課日期", min_value=datetime.date.today(), key="r_date")
            with rc2:
                r_period = st.selectbox("節次", PERIODS, key="r_period")
            with rc3:
                r_subject = st.selectbox("觀課科目", SUBJECTS, key="r_subject")

            r_unit = st.text_input("觀課單元", placeholder="例如：水的三態變化", key="r_unit")

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
            with st.expander(f"📌 {indicator_labels[r_indicator]} 子項目（共 {len(sub_items)} 項）", expanded=True):
                for sub in sub_items:
                    st.markdown(f"- **{sub[0]}**　{sub[1]}")

            bc1, bc2 = st.columns(2)
            with bc1:
                if st.button("✅ 確認送出登記", type="primary", use_container_width=True, key="submit_reg"):
                    if not r_unit.strip():
                        st.error("請填寫觀課單元名稱")
                    else:
                        with st.spinner("儲存中…"):
                            sid = add_session(
                                teacher_email=user["email"],
                                teacher_name=user["name"],
                                date=r_date.strftime("%Y/%m/%d"),
                                period=r_period,
                                subject=r_subject,
                                unit=r_unit.strip(),
                                indicator_id=r_indicator,
                            )
                        st.success(f"✅ 登記成功！場次編號：`{sid}`")
                        st.session_state["show_register"] = False
                        st.rerun()
            with bc2:
                if st.button("取消", use_container_width=True, key="cancel_reg"):
                    st.session_state["show_register"] = False
                    st.rerun()

    st.divider()

    my_s = get_sessions_by_teacher(user["email"])
    if my_s.empty:
        st.info("您尚未登記任何公開觀課場次，請點上方「登記公開觀課」新增。")
    else:
        my_s = my_s.sort_values("date", ascending=False).reset_index(drop=True)
        st.markdown(f"共 **{len(my_s)}** 場")
        for _, row in my_s.iterrows():
            obs_count = len(obs_df[obs_df["session_id"] == row["session_id"]]) if not obs_df.empty else 0
            ind_name = get_indicator_name(row["indicator_id"])
            color = INDICATOR_COLORS.get(row["indicator_id"], "⚪")
            has_ref = bool(str(row.get("teacher_reflection","")).strip())

            with st.container(border=True):
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f"**{row['subject']}｜{row['unit']}**")
                    st.caption(f"📅 {row['date']}　🕐 {row['period']}　{color} {row['indicator_id']}．{ind_name}　｜　👥 {obs_count} 人觀課")
                with c2:
                    if has_ref:
                        st.success("已填省思")
                    else:
                        st.warning("待填省思")

# ════════════════════════════════════════
# 分頁二：學校近期觀課（未來場次，由近到遠）
# ════════════════════════════════════════
with tab2:
    if sessions_df.empty:
        st.info("目前尚無觀課場次")
    else:
        def parse_date(d):
            try:
                return datetime.datetime.strptime(str(d), "%Y/%m/%d").date()
            except:
                return None

        sessions_df["date_obj"] = sessions_df["date"].apply(parse_date)

        # 只取今天以後的場次，由近到遠
        upcoming = sessions_df[
            sessions_df["date_obj"].apply(lambda d: d is not None and d >= today)
        ].sort_values("date_obj", ascending=True).reset_index(drop=True)

        if upcoming.empty:
            st.info("目前沒有即將到來的觀課場次")
        else:
            st.markdown(f"共 **{len(upcoming)}** 場即將到來的觀課")
            for _, row in upcoming.iterrows():
                obs_count = len(obs_df[obs_df["session_id"] == row["session_id"]]) if not obs_df.empty else 0
                is_own = row["teacher_email"] == user["email"]
                already = False
                if not obs_df.empty:
                    already = not obs_df[
                        (obs_df["session_id"] == row["session_id"]) &
                        (obs_df["observer_email"] == user["email"])
                    ].empty
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
# 分頁三：已結束觀課（近30筆，點擊查看詳情）
# ════════════════════════════════════════
with tab3:
    if sessions_df.empty:
        st.info("目前尚無觀課場次")
    else:
        sessions_df["date_obj2"] = sessions_df["date"].apply(parse_date)
        ended = sessions_df[
            sessions_df["date_obj2"].apply(lambda d: d is not None and d < today)
        ].sort_values("date_obj2", ascending=False).head(30).reset_index(drop=True)

        if ended.empty:
            st.info("尚無已結束的觀課場次")
        else:
            # 如果有選取的場次，顯示詳情
            if "ended_session_id" in st.session_state:
                sel_id = st.session_state["ended_session_id"]
                sel_row = ended[ended["session_id"] == sel_id]
                if not sel_row.empty:
                    sel = sel_row.iloc[0]
                    sel_obs = get_observations_by_session(sel_id)
                    ind_name = get_indicator_name(sel["indicator_id"])

                    if st.button("← 返回列表"):
                        del st.session_state["ended_session_id"]
                        st.rerun()

                    st.markdown(f"### {sel['subject']}｜{sel['unit']}")
                    st.caption(f"📅 {sel['date']}　🕐 {sel['period']}　👤 {sel['teacher_name']}　{sel['indicator_id']}．{ind_name}")
                    st.divider()

                    if sel_obs.empty:
                        st.info("本場次尚無觀課紀錄")
                    else:
                        import json
                        from utils.sheets import get_sub_indicators
                        from utils.drive import decode_photo_urls
                        sub_items = get_sub_indicators(sel["indicator_id"])

                        for _, obs in sel_obs.iterrows():
                            with st.expander(f"👤 {obs['observer_name']}　（{obs['submitted_at']}）"):
                                try:
                                    scores = json.loads(obs["indicator_scores"])
                                except:
                                    scores = {}
                                if scores and sub_items:
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
                                    img_cols = st.columns(min(len(photos), 4))
                                    for i, b64 in enumerate(photos):
                                        with img_cols[i % 4]:
                                            st.image(b64, use_container_width=True)

                    teacher_ref = str(sel.get("teacher_reflection","") or "")
                    teacher_adj = str(sel.get("teacher_adjustment","") or "")
                    if teacher_ref or teacher_adj:
                        st.divider()
                        st.markdown("**📝 被觀課者教學省思**")
                        st.markdown(teacher_ref or "（未填寫）")
                        st.markdown("**🔧 未來調整方向**")
                        st.markdown(teacher_adj or "（未填寫）")
                else:
                    del st.session_state["ended_session_id"]
                    st.rerun()

            else:
                st.markdown(f"最近 **{len(ended)}** 場（已結束）")
                for _, row in ended.iterrows():
                    obs_count = len(obs_df[obs_df["session_id"] == row["session_id"]]) if not obs_df.empty else 0
                    ind_name = get_indicator_name(row["indicator_id"])
                    color = INDICATOR_COLORS.get(row["indicator_id"], "⚪")
                    teacher_done = bool(str(row.get("teacher_reflection","")).strip())
                    obs_done = obs_count > 0

                    with st.container(border=True):
                        c1, c2, c3 = st.columns([5, 1, 1])
                        with c1:
                            st.markdown(f"**{row['subject']}｜{row['unit']}**")
                            st.caption(f"📅 {row['date']}　🕐 {row['period']}　👤 {row['teacher_name']}　{color} {row['indicator_id']}．{ind_name}")
                        with c2:
                            st.write("觀課 " + ("✅" if obs_done else "⬜"))
                        with c3:
                            st.write("省思 " + ("✅" if teacher_done else "⬜"))
                        # 整列點擊
                        if st.button("查看詳情 →", key=f"ended_{row['session_id']}", use_container_width=True):
                            st.session_state["ended_session_id"] = row["session_id"]
                            st.rerun()
