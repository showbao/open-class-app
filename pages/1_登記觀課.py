import streamlit as st
import datetime
from utils.auth import require_login
from utils.sheets import add_session, get_indicators

st.set_page_config(page_title="登記觀課", page_icon="✏️", layout="wide")
user = require_login()

SUBJECTS = ["國語","數學","英語","社會","自然","生活","美術","音樂","體育","健康","資訊","綜合","彈性"]
PERIODS  = [f"第{i}節" for i in range(1, 8)]

st.title("✏️ 登記公開觀課")
st.caption("填寫完畢後，資料將自動儲存至系統。")
st.divider()

# 先取得所有指標資料（在 form 外面，才能做連動）
indicators_df = get_indicators()
indicator_options = indicators_df.drop_duplicates("indicator_id")[["indicator_id","indicator_name"]].values.tolist()
indicator_labels = {row[0]: f"{row[0]}．{row[1]}" for row in indicator_options}

with st.form("register_form"):
    st.markdown("#### 基本資訊")
    c1, c2, c3 = st.columns(3)
    with c1:
        date = st.date_input("觀課日期", min_value=datetime.date.today())
    with c2:
        period = st.selectbox("節次", PERIODS)
    with c3:
        subject = st.selectbox("觀課科目", SUBJECTS)

    unit = st.text_input("觀課單元", placeholder="請輸入本次觀課單元名稱，例如：水的三態變化")

    st.divider()
    st.markdown("#### 選擇觀課大指標（擇一）")

    selected_indicator = st.radio(
        "觀課大指標",
        options=list(indicator_labels.keys()),
        format_func=lambda x: indicator_labels[x],
        horizontal=True,
        label_visibility="collapsed",
        key="indicator_radio"
    )

    st.divider()
    submitted = st.form_submit_button("✅ 送出登記", use_container_width=True, type="primary")

# ── 子項目預覽（在 form 外面，才能即時連動）──────────────────
st.markdown("#### 所選指標子項目")
sub_items = indicators_df[indicators_df["indicator_id"] == selected_indicator][["sub_id","sub_name"]].values.tolist()
ind_name = indicator_labels.get(selected_indicator, "")

with st.container(border=True):
    st.markdown(f"**{ind_name}**　共 {len(sub_items)} 個子項目")
    for sub in sub_items:
        st.markdown(f"- **{sub[0]}**　{sub[1]}")

st.divider()

if submitted:
    if not unit.strip():
        st.error("請填寫觀課單元名稱")
    else:
        with st.spinner("儲存中…"):
            session_id = add_session(
                teacher_email=user["email"],
                teacher_name=user["name"],
                date=date.strftime("%Y/%m/%d"),
                period=period,
                subject=subject,
                unit=unit.strip(),
                indicator_id=selected_indicator,
            )
        st.success(f"✅ 登記成功！場次編號：`{session_id}`")
        st.info("前往「我的觀課場次」可查看已登記場次。")
        st.page_link("pages/2_我的行事曆.py", label="📅 前往我的觀課場次")
