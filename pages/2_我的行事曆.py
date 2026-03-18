import streamlit as st
from utils.auth import require_login
from utils.sheets import get_sessions_by_teacher, get_indicator_name
from streamlit_calendar import calendar

st.set_page_config(page_title="我的行事曆", page_icon="📅", layout="wide")
user = require_login()

st.title("📅 我的觀課行事曆")
st.divider()

sessions = get_sessions_by_teacher(user["email"])

if sessions.empty:
    st.info("尚未登記任何公開觀課場次，請前往「登記觀課」新增。")
    st.page_link("pages/1_登記觀課.py", label="✏️ 前往登記")
else:
    # 建立行事曆事件
    COLORS = {"A": "#2563EB", "B": "#0EA5E9", "C": "#10B981", "D": "#F59E0B"}
    events = []
    for _, row in sessions.iterrows():
        color = COLORS.get(row["indicator_id"], "#6B7280")
        events.append({
            "title": f"{row['period']} {row['subject']}｜{row['unit']}",
            "start": row["date"].replace("/", "-"),
            "end":   row["date"].replace("/", "-"),
            "color": color,
            "extendedProps": {
                "session_id": row["session_id"],
                "period": row["period"],
                "subject": row["subject"],
                "unit": row["unit"],
                "indicator": get_indicator_name(row["indicator_id"]),
            }
        })

    calendar_options = {
        "initialView": "dayGridMonth",
        "locale": "zh-tw",
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,listMonth"
        },
        "height": 600,
    }

    cal_result = calendar(events=events, options=calendar_options)

    # 圖例
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    for col, (k, label, color) in zip(
        [col1, col2, col3, col4],
        [("A","課程設計","#2563EB"),("B","教學策略","#0EA5E9"),
         ("C","學生學習","#10B981"),("D","班級經營","#F59E0B")]
    ):
        with col:
            st.markdown(f'<span style="color:{color}">●</span> {k}．{label}', unsafe_allow_html=True)

    # 點擊事件：顯示場次詳情
    if cal_result.get("eventClick"):
        props = cal_result["eventClick"]["event"]["extendedProps"]
        with st.expander("📌 場次詳情", expanded=True):
            st.markdown(f"**科目**：{props['subject']}")
            st.markdown(f"**單元**：{props['unit']}")
            st.markdown(f"**節次**：{props['period']}")
            st.markdown(f"**觀課指標**：{props['indicator']}")
