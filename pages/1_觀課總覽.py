import streamlit as st
import datetime
import json
from utils.auth import require_login, logout
from utils.style import inject_global_css, MORANDI
from utils.sheets import (get_sessions_all, get_sessions_by_teacher,
                           get_observations_all, get_observations_by_session,
                           get_indicator_name, add_session, get_indicators,
                           is_admin, get_sub_indicators)
from utils.drive import decode_photo_urls

st.set_page_config(page_title="觀課總覽", page_icon="📋", layout="wide")
inject_global_css()

# 額外 CSS：卡片字體放大、點擊效果
st.markdown("""
<style>
.ok-card-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
    margin-bottom: 6px;
}
@media (max-width: 768px) {
    .ok-card-grid { grid-template-columns: 1fr !important; }
}
.ok-session-card {
    background: #FAFAF8;
    border-radius: 16px;
    border: 1px solid #DDD9D3;
    padding: 1.1rem 1.2rem 1rem;
    transition: box-shadow 0.2s, transform 0.15s, border-color 0.2s;
    cursor: pointer;
    height: 100%;
    box-sizing: border-box;
}
.ok-session-card:hover {
    box-shadow: 0 6px 20px rgba(0,0,0,0.09);
    transform: translateY(-2px);
    border-color: #7B8FA1;
}
.ok-card-subject {
    font-size: 20px;
    font-weight: 700;
    color: #3D3B38;
    margin-bottom: 10px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.ok-card-date {
    font-size: 18px;
    color: #857F76;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.ok-card-info {
    font-size: 16px;
    color: #857F76;
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 8px;
}
.ok-badge {
    display: inline-flex; align-items: center;
    font-size: 14px; font-weight: 600;
    padding: 4px 12px; border-radius: 20px; white-space: nowrap;
}
.ok-badge-blue  { background: #DDE4EC; color: #5C7080; }
.ok-badge-green { background: #D8E5DC; color: #4A7059; }
.ok-badge-amber { background: #EAE0D0; color: #8C6A3F; }
.ok-badge-red   { background: #E8D8D8; color: #8A4F4F; }
.ok-badge-gray  { background: #E5E1DB; color: #857F76; }
.ok-days-badge  { color: #7B8FA1; font-weight: 700; font-size: 13px; }
</style>
""", unsafe_allow_html=True)

user = require_login()

SUBJECTS = ["國語","數學","英語","社會","自然","生活","美術","音樂","體育","健康","資訊","綜合","彈性"]
PERIODS  = [f"第{i}節" for i in range(1, 8)]
IND_BADGE = {"A": "ok-badge-blue", "B": "ok-badge-green", "C": "ok-badge-amber", "D": "ok-badge-gray"}

# ── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
        <div style="padding:1rem 0.5rem 0.5rem;">
            <div style="width:44px;height:44px;border-radius:50%;
                background:linear-gradient(135deg,#7B8FA1,#A8937A);
                display:flex;align-items:center;justify-content:center;
                font-size:16px;font-weight:700;color:white;margin-bottom:10px;">
                {user['name'][0]}
            </div>
            <div style="font-size:14px;font-weight:600;color:#E2E8F0;">{user['name']}</div>
            <div style="font-size:11px;color:#94A3B8;margin-top:2px;">{user['email']}</div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("<hr style='border-color:rgba(255,255,255,0.1);margin:8px 0;'>", unsafe_allow_html=True)
    st.page_link("pages/1_觀課總覽.py",        label="📋 總覽")
    st.page_link("pages/5_我的被觀課紀錄.py",  label="📂 我的被觀課紀錄")
    st.page_link("pages/7_歷年紀錄.py",        label="📊 歷年觀課彙整")
    if is_admin(user["email"]):
        st.page_link("pages/6_主管總覽.py",    label="🔑 主管總覽")
    st.divider()
    if st.button("登出", use_container_width=True):
        logout()

# ── 資料讀取 ──────────────────────────────────────────────
sessions_df = get_sessions_all()
obs_df      = get_observations_all()
today       = datetime.date.today()

def parse_date(d):
    try:
        return datetime.datetime.strptime(str(d), "%Y/%m/%d").date()
    except:
        return None

st.markdown(f"""
<div style="margin-bottom:1.2rem;">
    <h1 style="margin:0 0 4px;">📋 觀課總覽</h1>
    <p style="color:#857F76;font-size:14px;margin:0;">歡迎回來，{user['name']}！</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📌 我的觀課列表", "🏫 學校近期觀課", "📁 已結束觀課"])

# ══════════════════════════════════════════════════════════
# 共用：用 st.columns 渲染卡片（避免 HTML 渲染問題）
# ══════════════════════════════════════════════════════════
def render_session_cards(rows, key_prefix, on_click_key,
                         show_teacher=False, show_days=False,
                         show_ref_status=False, show_obs_status=False):
    """
    用 st.columns 搭配 st.markdown 渲染卡片，每列最多3張
    on_click_key: session_state 的 key，點擊後設定此 key = session_id
    """
    for i in range(0, len(rows), 3):
        chunk = rows.iloc[i:i+3]
        cols = st.columns(3)
        for j, (_, row) in enumerate(chunk.iterrows()):
            with cols[j]:
                ind_name  = get_indicator_name(row["indicator_id"])
                badge_cls = IND_BADGE.get(row["indicator_id"], "ok-badge-gray")
                has_ref   = bool(str(row.get("teacher_reflection","")).strip())
                obs_count = len(obs_df[obs_df["session_id"] == row["session_id"]]) if not obs_df.empty else 0

                # 日期行
                date_html = f'<span>{row["date"]}</span><span>{row["period"]}</span>'
                if show_days:
                    d = parse_date(row["date"])
                    if d:
                        diff = (d - today).days
                        label = "今天" if diff == 0 else f"{diff} 天後"
                        date_html = f'<span>{row["date"]}</span><span class="ok-days-badge">({label})</span><span>{row["period"]}</span>'

                # 狀態 badge
                status_html = ""
                if show_ref_status:
                    status_html += '<span class="ok-badge ok-badge-green">✅ 已填省思</span>' if has_ref else '<span class="ok-badge ok-badge-amber">⏳ 待填省思</span>'
                if show_obs_status:
                    status_html += ' <span class="ok-badge ok-badge-green">觀課 ✅</span>' if obs_count > 0 else ' <span class="ok-badge ok-badge-gray">觀課 ⬜</span>'
                    status_html += ' <span class="ok-badge ok-badge-green">省思 ✅</span>' if has_ref else ' <span class="ok-badge ok-badge-gray">省思 ⬜</span>'

                teacher_html = f'<span>👤 {row["teacher_name"]}</span>' if show_teacher else ''

                st.markdown(f"""
                <div class="ok-session-card">
                    <div class="ok-card-subject">{row['subject']}｜{row['unit']}</div>
                    <div class="ok-card-date">{date_html}</div>
                    <div class="ok-card-info">
                        {teacher_html}
                        <span class="ok-badge {badge_cls}">{row['indicator_id']}．{ind_name}</span>
                    </div>
                    {"<div class='ok-card-info'>" + status_html + "</div>" if status_html else ""}
                </div>
                """, unsafe_allow_html=True)

                if st.button("→ 進入", key=f"{key_prefix}_{row['session_id']}", use_container_width=True):
                    st.session_state[on_click_key] = row["session_id"]
                    if on_click_key == "view_session_id":
                        st.switch_page("pages/5_我的被觀課紀錄.py")
                    elif on_click_key == "obs_session_id":
                        st.session_state["selected_session"] = row.to_dict()
                        st.switch_page("pages/4_填寫觀課紀錄.py")
                    else:
                        st.rerun()

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
                            add_session(
                                teacher_email=user["email"], teacher_name=user["name"],
                                date=r_date.strftime("%Y/%m/%d"), period=r_period,
                                subject=r_subject, unit=r_unit.strip(), indicator_id=r_indicator,
                            )
                        st.success("✅ 登記成功！")
                        st.session_state["show_register"] = False
                        st.rerun()
            with bc2:
                if st.button("取消", use_container_width=True, key="cancel_reg"):
                    st.session_state["show_register"] = False
                    st.rerun()

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    my_s = get_sessions_by_teacher(user["email"])
    if my_s.empty:
        st.info("您尚未登記任何公開觀課場次，請點上方「登記公開觀課」新增。")
    else:
        my_s = my_s.sort_values("date", ascending=False).reset_index(drop=True)
        st.markdown(f"<p style='font-size:13px;color:#857F76;margin-bottom:10px;'>共 <b>{len(my_s)}</b> 場</p>", unsafe_allow_html=True)
        render_session_cards(my_s, "my", "view_session_id", show_ref_status=True)

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
            st.markdown(f"<p style='font-size:13px;color:#857F76;margin-bottom:10px;'>共 <b>{len(upcoming)}</b> 場即將到來</p>", unsafe_allow_html=True)

            for i in range(0, len(upcoming), 3):
                chunk = upcoming.iloc[i:i+3]
                cols = st.columns(3)
                for j, (_, row) in enumerate(chunk.iterrows()):
                    with cols[j]:
                        ind_name  = get_indicator_name(row["indicator_id"])
                        badge_cls = IND_BADGE.get(row["indicator_id"], "ok-badge-gray")
                        d = row["date_obj"]
                        diff = (d - today).days if d else 0
                        days_label = "今天" if diff == 0 else f"{diff} 天後"
                        is_own = row["teacher_email"] == user["email"]
                        already = False
                        if not obs_df.empty:
                            already = not obs_df[
                                (obs_df["session_id"] == row["session_id"]) &
                                (obs_df["observer_email"] == user["email"])
                            ].empty

                        st.markdown(f"""
                        <div class="ok-session-card">
                            <div class="ok-card-subject">{row['subject']}｜{row['unit']}</div>
                            <div class="ok-card-date">
                                <span>{row['date']}</span>
                                <span class="ok-days-badge">({days_label})</span>
                                <span>{row['period']}</span>
                            </div>
                            <div class="ok-card-info">
                                <span>👤 {row['teacher_name']}</span>
                                <span class="ok-badge {badge_cls}">{row['indicator_id']}．{ind_name}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        if is_own:
                            st.markdown('<span class="ok-badge ok-badge-gray" style="margin-top:4px;display:inline-flex;">自己的課</span>', unsafe_allow_html=True)
                        elif already:
                            st.markdown('<span class="ok-badge ok-badge-green" style="margin-top:4px;display:inline-flex;">✅ 已填寫</span>', unsafe_allow_html=True)
                        else:
                            if st.button("填寫觀課紀錄 →", key=f"obs_{row['session_id']}", type="primary", use_container_width=True):
                                st.session_state["selected_session"] = row.to_dict()
                                st.switch_page("pages/4_填寫觀課紀錄.py")

# ════════════════════════════════════════
# 分頁三：已結束觀課（近30筆）
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
        elif "ended_session_id" in st.session_state:
            sel_id   = st.session_state["ended_session_id"]
            sel_rows = ended[ended["session_id"] == sel_id]
            if sel_rows.empty:
                del st.session_state["ended_session_id"]
                st.rerun()
            sel      = sel_rows.iloc[0]
            sel_obs  = get_observations_by_session(sel_id)
            ind_name = get_indicator_name(sel["indicator_id"])
            badge_cls= IND_BADGE.get(sel["indicator_id"], "ok-badge-gray")

            if st.button("← 返回列表"):
                del st.session_state["ended_session_id"]
                st.rerun()

            st.markdown(f"""
            <div class="ok-session-card" style="cursor:default;margin-bottom:1rem;">
                <div class="ok-card-subject" style="font-size:19px;">{sel['subject']}｜{sel['unit']}</div>
                <div class="ok-card-date">{sel['date']}　{sel['period']}</div>
                <div class="ok-card-info">
                    <span>👤 {sel['teacher_name']}</span>
                    <span class="ok-badge {badge_cls}">{sel['indicator_id']}．{ind_name}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if sel_obs.empty:
                st.info("本場次尚無觀課紀錄")
            else:
                sub_items_list = get_sub_indicators(sel["indicator_id"])
                st.markdown(f"#### 觀課紀錄（共 {len(sel_obs)} 位）")
                for _, obs in sel_obs.iterrows():
                    with st.expander(f"👤 {obs['observer_name']}　（{obs['submitted_at']}）"):
                        try:
                            scores = json.loads(obs["indicator_scores"])
                        except:
                            scores = {}
                        if scores and sub_items_list:
                            score_cols = st.columns(len(sub_items_list))
                            for i, sub in enumerate(sub_items_list):
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
            st.markdown(f"<p style='font-size:13px;color:#857F76;margin-bottom:10px;'>最近 <b>{len(ended)}</b> 場（已結束）</p>", unsafe_allow_html=True)
            render_session_cards(ended, "ended", "ended_session_id",
                                 show_teacher=True, show_obs_status=True)
