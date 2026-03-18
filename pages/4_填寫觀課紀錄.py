import streamlit as st
import json
from utils.auth import require_login
from utils.sheets import get_sub_indicators, add_observation, get_indicator_name, has_observation
from utils.drive import upload_photos

st.set_page_config(page_title="填寫觀課紀錄", page_icon="📝", layout="wide")
user = require_login()

# 確認有選取場次
if "selected_session" not in st.session_state:
    st.warning("請先從「近期場次」選擇要觀課的場次")
    st.page_link("pages/3_近期場次.py", label="← 返回近期場次")
    st.stop()

session = st.session_state["selected_session"]
indicator_id = session["indicator_id"]
ind_name = get_indicator_name(indicator_id)
sub_items = get_sub_indicators(indicator_id)

st.title("📝 填寫觀課紀錄")
with st.container(border=True):
    st.markdown(f"**{session['subject']}｜{session['unit']}**")
    st.caption(f"📅 {session['date']}　🕐 {session['period']}　👤 被觀課者：{session['teacher_name']}")
    st.caption(f"觀課指標：{indicator_id}．{ind_name}")

st.divider()

# 已填寫判斷
already = has_observation(session["session_id"], user["email"])
if already:
    st.info("您已填寫本場次觀課紀錄。")
    obs_df = st.session_state.get("obs_preview")
    st.page_link("pages/3_近期場次.py", label="← 返回近期場次")
    st.stop()

# ── 表單 ──────────────────────────────────────────────────
with st.form("obs_form"):

    # 1. 五點量表
    st.markdown(f"#### {indicator_id}．{ind_name} — 五點量表")
    st.caption("1 = 待加強　2 = 尚可　3 = 良好　4 = 優良　5 = 傑出")
    scores = {}
    for sub in sub_items:
        col_label, col_scale = st.columns([3, 2])
        with col_label:
            st.markdown(f"**{sub['sub_id']}**　{sub['sub_name']}")
        with col_scale:
            scores[sub["sub_id"]] = st.select_slider(
                label=sub["sub_id"],
                options=[1, 2, 3, 4, 5],
                value=3,
                label_visibility="collapsed",
                key=f"score_{sub['sub_id']}"
            )

    st.divider()

    # 2. 質性記錄
    st.markdown("#### 觀課質性記錄")
    qualitative = st.text_area(
        "質性記錄",
        placeholder="請描述本節課的觀察重點、亮點或值得關注的教學行為…",
        height=120,
        label_visibility="collapsed"
    )

    st.divider()

    # 3. 自我省思
    st.markdown("#### 對自己教學上的省思")
    self_reflection = st.text_area(
        "省思",
        placeholder="透過本次觀課，對自身教學有哪些反思或啟發？",
        height=100,
        label_visibility="collapsed"
    )

    st.divider()

    # 4. 照片上傳（必填）
    st.markdown("#### 課堂照片上傳（必填）")
    uploaded_files = st.file_uploader(
        "上傳照片",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    if uploaded_files:
        cols = st.columns(min(len(uploaded_files), 5))
        for i, f in enumerate(uploaded_files):
            with cols[i % 5]:
                st.image(f, use_container_width=True)

    st.divider()
    submitted = st.form_submit_button("✅ 送出觀課紀錄", use_container_width=True, type="primary")

if submitted:
    errors = []
    if not qualitative.strip():
        errors.append("請填寫觀課質性記錄")
    if not self_reflection.strip():
        errors.append("請填寫對自己教學的省思")
    if not uploaded_files:
        errors.append("請至少上傳一張課堂照片（必填）")

    if errors:
        for e in errors:
            st.error(e)
    else:
        with st.spinner("上傳照片並儲存中…"):
            photo_urls = upload_photos(uploaded_files, session["session_id"], user["email"])
            add_observation(
                session_id=session["session_id"],
                observer_email=user["email"],
                observer_name=user["name"],
                indicator_scores=scores,
                qualitative_notes=qualitative.strip(),
                self_reflection=self_reflection.strip(),
                photo_urls=photo_urls,
            )
        st.success("✅ 觀課紀錄已成功送出！")
        st.balloons()
        if st.button("← 返回近期場次"):
            del st.session_state["selected_session"]
            st.switch_page("pages/3_近期場次.py")
