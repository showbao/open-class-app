import streamlit as st
import datetime
import json
from utils.auth import require_login, logout
from utils.style import inject_global_css
from utils.sheets import (get_sessions_all, get_sessions_by_teacher,
                           get_observations_all, get_observations_by_session,
                           get_indicator_name, add_session, get_indicators,
                           has_observation, is_admin, get_sub_indicators)
from utils.drive import decode_photo_urls

st.set_page_config(page_title="觀課總覽", page_icon="📋", layout="wide")
inject_global_css()
user = require_login()

SUBJECTS = ["國語","數學","英語","社會","自然","生活","美術","音樂","體育","健康","資訊","綜合","彈性"]
PERIODS  = [f"第{i}節" for i in range(1, 8)]
IND_BADGE = {"A": "ok-badge-blue", "B": "ok-badge-green", "C": "ok-badge-amber", "D": "ok-badge-gray"}
IND_DOT   = {"A": "#2563EB", "B": "#10B981", "C": "#F59E0B", "D": "#6B7280"}

# ── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
        <div style="padding:1rem 0.5rem 0.5rem;">
            <div style="width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,#667eea,#764ba2);
                display:flex;align-items:center;justify-content:center;
                font-size:16px;font-weight:700;color:white;margin-bottom:10px;">
                {user['name'][0]}
            </div>
            <div style="font-size:14px;font-weight:600;color:#E2E8F0;">{user['name']}</div>
            <div style="font-size:11px;color:#94A3B8;margin-top:2px;">{user['email']}</div>
        </div>
    """, unsafe_allow_html=True)
    if is_admin(user["email"]):
        st.markdown('<div style="margin:0 0.5rem;"><span class="ok-badge ok-badge-blue">🔑 主管身份</span></div>', unsafe_allow_html=True)
    st.markdown("<hr style='border-color:rgba(255,255,255,0.1);margin:12px 0;'>", unsafe_allow_html=True)
    st.page_link("pages/1_觀課總覽.py",        label="📋 總覽")
    st.page_link("pages/5_我的被觀課紀錄.py",  label="📂 我的被觀課紀錄")
    st.page_link("pages/7_歷年紀錄.py",        label="📊 歷年觀課彙整")
    if is_admin(user["email"]):
        st.page_link("pages/6_主管總覽.py",    label="🔑 主管總覽")
    st.divider()
    if st.button("登出", use_container_width=True):
        logout()

# ── 一次讀取資料 ──────────────────────────────────────────
sessions_df = get_sessions_all()
obs_df      = get_observations_all()
today       = datetime.date.today()

my_sessions = sessions_df[sessions_df["teacher_email"] == user["email"]] if not sessions_df.empty else sessions_df

pending_reflection = 0
if not my_sessions.empty and not obs_df.empty:
    for _, row in my_sessions.iterrows():
        has_obs = not obs_df[obs_df["session_id"] == row["session_id"]].empty
        no_ref  = not str(row.get("teacher_reflection","")).strip()
        if has_obs and no_ref:
            pending_reflection += 1

total_observers = 0
if not my_sessions.empty and not obs_df.empty:
    total_observers = len(obs_df[obs_df["session_id"].isin(my_sessions["session_id"].tolist())])

# ── 頁首 ─────────────────────────────────────────────────
st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.5rem;">
    <div>
        <h1 style="margin:0;">📋 觀課總覽</h1>
        <p style="color:#7C8BA0;font-size:14px;margin:4px 0 0;">歡迎回來，{user['name']}！</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ── 統計卡 ────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("本學期已登記場次", len(my_sessions))
with col2:
    st.metric("待填寫教學省思", pending_reflection,
              delta="需填寫" if pending_reflection > 0 else None,
              delta_color="inverse" if pending_reflection > 0 else "off")
with col3:
    st.metric("被觀課者人次", total_observers)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

def parse_date(d):
    try:
        return datetime.datetime.strptime(str(d), "%Y/%m/%d").date()
    except:
        return None

tab1, tab2, tab3 = st.tabs(["📌 我的觀課列表", "🏫 學校近期觀課", "📁 已結束觀課"])

# ════════════════════════════════════════
# 分頁一：我的觀課列表
# ════════════════════════════════════════
with tab1:
    if st.button("➕ 登記公開觀課", type="primary"):
        st.session_state["show_register"] = not st.session_state.get("show_register", False)

    if st.session_state.get("show_register", False):
        with st.container(border=True):
            st.markdown("#### ✏️ 登記公開觀課")
            indicators_df = get_indicators()
            indicator_options = indicators_df.drop_duplicates("indicator_id")[["indicator_id","indicator_name"]].values.tolist()
            indicator_labels = {r[0]: f"{r[0]}．{r[1]}" for r in indicator_options}

            rc1, rc2, rc3 = st.columns(3)
            with rc1:
                r_date = st.date_input("觀課日期", min_value=datetime.date.today(), key="r_date")
            with rc2:
                r_period = st.selectbox("節次", PERIODS, key="r_period")
            with rc3:
                r_subject = st.selectbox("觀課科目", SUBJECTS, key="r_subject")

            r_unit = st.text_input("觀課單元", placeholder="例如：水的三態變化", key="r_unit")
            st.markdown("**選擇觀課大指標（擇一）**")
            r_indicator = st.radio("指標", options=list(indicator_labels.keys()),
                format_func=lambda x: indicator_labels[x], horizontal=True,
                label_visibility="collapsed", key="r_indicator")

            sub_items = indicators_df[indicators_df["indicator_id"] == r_indicator][["sub_id","sub_name"]].values.tolist()
            with st.expander(f"📌 {indicator_labels[r_indicator]} 子項目（共 {len(sub_items)} 項）", expanded=True):
                cols_sub = st.columns(2)
                for i, sub in enumerate(sub_items):
                    with cols_sub[i % 2]:
                        st.markdown(f'<span class="ok-badge ok-badge-blue">{sub[0]}</span> {sub[1]}', unsafe_allow_html=True)

            bc1, bc2 = st.columns(2)
            with bc1:
                if st.button("✅ 確認送出登記", type="primary", use_container_width=True, key="submit_reg"):
                    if not r_unit.strip():
                        st.error("請填寫觀課單元名稱")
                    else:
                        with st.spinner("儲存中…"):
                            sid = add_session(
                                teacher_email=user["email"], teacher_name=user["name"],
                                date=r_date.strftime("%Y/%m/%d"), period=r_period,
                                subject=r_subject, unit=r_unit.strip(), indicator_id=r_indicator,
                            )
                        st.success(f"✅ 登記成功！")
                        st.session_state["show_register"] = False
                        st.rerun()
            with bc2:
                if st.button("取消", use_container_width=True, key="cancel_reg"):
                    st.session_state["show_register"] = False
                    st.rerun()

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    my_s = get_sessions_by_teacher(user["email"])
    if my_s.empty:
        st.info("您尚未登記任何公開觀課場次，請點上方「登記公開觀課」新增。")
    else:
        my_s = my_s.sort_values("date", ascending=False).reset_index(drop=True)
        st.markdown(f"<p style='font-size:13px;color:#7C8BA0;margin-bottom:8px;'>共 <b>{len(my_s)}</b> 場</p>", unsafe_allow_html=True)
        for _, row in my_s.iterrows():
            obs_count = len(obs_df[obs_df["session_id"] == row["session_id"]]) if not obs_df.empty else 0
            ind_name  = get_indicator_name(row["indicator_id"])
            badge_cls = IND_BADGE.get(row["indicator_id"], "ok-badge-gray")
            has_ref   = bool(str(row.get("teacher_reflection","")).strip())
            ref_badge = '<span class="ok-badge ok-badge-green">✅ 已填省思</span>' if has_ref else '<span class="ok-badge ok-badge-amber">⏳ 待填省思</span>'

            st.markdown(f"""
            <div class="ok-card">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;">
                    <div style="flex:1;min-width:0;">
                        <div class="ok-card-title">{row['subject']}｜{row['unit']}</div>
                        <div class="ok-card-meta" style="margin-top:6px;gap:8px;">
                            <span>📅 {row['date']}</span>
                            <span>🕐 {row['period']}</span>
                            <span class="ok-badge {badge_cls}">{row['indicator_id']}．{ind_name}</span>
                            <span>👥 {obs_count} 人觀課</span>
                        </div>
                    </div>
                    <div style="flex-shrink:0;">{ref_badge}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ════════════════════════════════════════
# 分頁二：學校近期觀課（未來場次）
# ════════════════════════════════════════
with tab2:
    if sessions_df.empty:
        st.info("目前尚無觀課場次")
    else:
        sessions_df["date_obj"] = sessions_df["date"].apply(parse_date)
        upcoming = sessions_df[
            sessions_df["date_obj"].apply(lambda d: d is not None and d >= today)
        ].sort_values("date_obj", ascending=True).reset_index(drop=True)

        if upcoming.empty:
            st.info("目前沒有即將到來的觀課場次")
        else:
            st.markdown(f"<p style='font-size:13px;color:#7C8BA0;margin-bottom:8px;'>共 <b>{len(upcoming)}</b> 場即將到來</p>", unsafe_allow_html=True)
            for _, row in upcoming.iterrows():
                obs_count = len(obs_df[obs_df["session_id"] == row["session_id"]]) if not obs_df.empty else 0
                is_own = row["teacher_email"] == user["email"]
                already = False
                if not obs_df.empty:
                    already = not obs_df[(obs_df["session_id"] == row["session_id"]) &
                                         (obs_df["observer_email"] == user["email"])].empty
                ind_name  = get_indicator_name(row["indicator_id"])
                badge_cls = IND_BADGE.get(row["indicator_id"], "ok-badge-gray")

                # 計算距今天數
                days_diff = (row["date_obj"] - today).days
                days_label = "今天" if days_diff == 0 else f"{days_diff} 天後"

                with st.container(border=True):
                    cc1, cc2 = st.columns([4, 1])
                    with cc1:
                        st.markdown(f"""
                        <div style="padding:2px 0;">
                            <div class="ok-card-title" style="font-size:14px;">{row['subject']}｜{row['unit']}</div>
                            <div class="ok-card-meta" style="margin-top:5px;">
                                <span>📅 {row['date']} <b style="color:#2563EB;">（{days_label}）</b></span>
                                <span>🕐 {row['period']}</span>
                                <span>👤 {row['teacher_name']}</span>
                                <span class="ok-badge {badge_cls}">{row['indicator_id']}．{ind_name}</span>
                                <span>👥 {obs_count} 人</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    with cc2:
                        if is_own:
                            st.markdown('<span class="ok-badge ok-badge-blue">自己的課</span>', unsafe_allow_html=True)
                        elif already:
                            st.markdown('<span class="ok-badge ok-badge-green">✅ 已填寫</span>', unsafe_allow_html=True)
                        else:
                            if st.button("填寫觀課紀錄 →", key=f"obs_{row['session_id']}", type="primary"):
                                st.session_state["selected_session"] = row.to_dict()
                                st.switch_page("pages/4_填寫觀課紀錄.py")

# ════════════════════════════════════════
# 分頁三：已結束觀課（近30筆，點擊查看）
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
            # 詳情檢視
            if "ended_session_id" in st.session_state:
                sel_id  = st.session_state["ended_session_id"]
                sel_row = ended[ended["session_id"] == sel_id]

                if sel_row.empty:
                    del st.session_state["ended_session_id"]
                    st.rerun()

                sel = sel_row.iloc[0]
                sel_obs = get_observations_by_session(sel_id)
                ind_name  = get_indicator_name(sel["indicator_id"])
                badge_cls = IND_BADGE.get(sel["indicator_id"], "ok-badge-gray")

                if st.button("← 返回列表"):
                    del st.session_state["ended_session_id"]
                    st.rerun()

                st.markdown(f"""
                <div class="ok-card" style="margin-bottom:1rem;">
                    <div class="ok-card-title" style="font-size:17px;">{sel['subject']}｜{sel['unit']}</div>
                    <div class="ok-card-meta" style="margin-top:8px;">
                        <span>📅 {sel['date']}</span>
                        <span>🕐 {sel['period']}</span>
                        <span>👤 {sel['teacher_name']}</span>
                        <span class="ok-badge {badge_cls}">{sel['indicator_id']}．{ind_name}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if sel_obs.empty:
                    st.info("本場次尚無觀課紀錄")
                else:
                    sub_items = get_sub_indicators(sel["indicator_id"])
                    st.markdown(f"#### 觀課紀錄（共 {len(sel_obs)} 位）")
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
                st.markdown(f"<p style='font-size:13px;color:#7C8BA0;margin-bottom:8px;'>最近 <b>{len(ended)}</b> 場（已結束）</p>", unsafe_allow_html=True)
                for _, row in ended.iterrows():
                    obs_count    = len(obs_df[obs_df["session_id"] == row["session_id"]]) if not obs_df.empty else 0
                    ind_name     = get_indicator_name(row["indicator_id"])
                    badge_cls    = IND_BADGE.get(row["indicator_id"], "ok-badge-gray")
                    teacher_done = bool(str(row.get("teacher_reflection","")).strip())
                    obs_done     = obs_count > 0

                    obs_badge     = '<span class="ok-badge ok-badge-green">觀課 ✅</span>' if obs_done else '<span class="ok-badge ok-badge-gray">觀課 ⬜</span>'
                    ref_badge     = '<span class="ok-badge ok-badge-green">省思 ✅</span>' if teacher_done else '<span class="ok-badge ok-badge-gray">省思 ⬜</span>'

                    with st.container(border=True):
                        ec1, ec2 = st.columns([4, 1])
                        with ec1:
                            st.markdown(f"""
                            <div style="padding:2px 0;">
                                <div class="ok-card-title" style="font-size:14px;">{row['subject']}｜{row['unit']}</div>
                                <div class="ok-card-meta" style="margin-top:5px;">
                                    <span>📅 {row['date']}</span>
                                    <span>🕐 {row['period']}</span>
                                    <span>👤 {row['teacher_name']}</span>
                                    <span class="ok-badge {badge_cls}">{row['indicator_id']}．{ind_name}</span>
                                    <span style="display:flex;gap:5px;">{obs_badge} {ref_badge}</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        with ec2:
                            if st.button("查看 →", key=f"ended_{row['session_id']}", use_container_width=True):
                                st.session_state["ended_session_id"] = row["session_id"]
                                st.rerun()
