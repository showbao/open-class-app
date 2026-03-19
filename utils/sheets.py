import gspread
import streamlit as st
from google.oauth2.service_account import Credentials
import datetime
import json
import pandas as pd

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

@st.cache_resource
def get_client():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )
    return gspread.authorize(creds)

def get_sheet(sheet_name: str):
    client = get_client()
    spreadsheet_id = st.secrets["sheets"]["spreadsheet_id"]
    return client.open_by_key(spreadsheet_id).worksheet(sheet_name)

# ── 加入快取：所有讀取都快取 120 秒，大幅降低 API 呼叫次數 ──
@st.cache_data(ttl=120)
def get_df(sheet_name: str) -> pd.DataFrame:
    ws = get_sheet(sheet_name)
    data = ws.get_all_records()
    return pd.DataFrame(data)

def clear_cache():
    """寫入資料後呼叫，清除快取讓下次讀取取得最新資料"""
    get_df.clear()

def generate_id(prefix: str) -> str:
    ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{prefix}{ts}"

# ── sessions ──────────────────────────────────────────────

def add_session(teacher_email, teacher_name, date, period, subject, unit, indicator_id):
    ws = get_sheet("sessions")
    session_id = generate_id("S")
    now = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    ws.append_row([
        session_id, teacher_email, teacher_name,
        date, period, subject, unit, indicator_id,
        "", "",
        now
    ])
    clear_cache()
    return session_id

def get_sessions_all() -> pd.DataFrame:
    return get_df("sessions")

def get_sessions_by_teacher(email: str) -> pd.DataFrame:
    df = get_df("sessions")
    if df.empty:
        return df
    return df[df["teacher_email"] == email].reset_index(drop=True)

def update_teacher_reflection(session_id, reflection, adjustment):
    ws = get_sheet("sessions")
    records = ws.get_all_records()
    for i, row in enumerate(records, start=2):
        if row["session_id"] == session_id:
            ws.update_cell(i, 9, reflection)
            ws.update_cell(i, 10, adjustment)
            break
    clear_cache()

# ── observations ─────────────────────────────────────────

def add_observation(session_id, observer_email, observer_name,
                    indicator_scores: dict, qualitative_notes,
                    self_reflection, photo_urls: list):
    ws = get_sheet("observations")
    obs_id = generate_id("O")
    now = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    ws.append_row([
        obs_id, session_id, observer_email, observer_name,
        json.dumps(indicator_scores, ensure_ascii=False),
        qualitative_notes, self_reflection,
        ",".join(photo_urls),
        now
    ])
    clear_cache()
    return obs_id

def get_observations_all() -> pd.DataFrame:
    """一次讀取所有觀課紀錄，供首頁統計使用"""
    return get_df("observations")

def get_observations_by_session(session_id: str) -> pd.DataFrame:
    df = get_df("observations")
    if df.empty:
        return df
    return df[df["session_id"] == session_id].reset_index(drop=True)

def has_observation(session_id: str, observer_email: str) -> bool:
    df = get_df("observations")
    if df.empty:
        return False
    return not df[(df["session_id"] == session_id) & (df["observer_email"] == observer_email)].empty

# ── indicators ───────────────────────────────────────────

@st.cache_data(ttl=3600)
def get_indicators() -> pd.DataFrame:
    return get_df("indicators")

def get_sub_indicators(indicator_id: str) -> list[dict]:
    df = get_indicators()
    sub = df[df["indicator_id"] == indicator_id]
    return sub[["sub_id", "sub_name"]].to_dict("records")

def get_indicator_name(indicator_id: str) -> str:
    df = get_indicators()
    row = df[df["indicator_id"] == indicator_id]
    if row.empty:
        return indicator_id
    return row.iloc[0]["indicator_name"]

# ── admins ───────────────────────────────────────────────

@st.cache_data(ttl=3600)
def get_admins() -> pd.DataFrame:
    return get_df("admins")

def is_admin(email: str) -> bool:
    df = get_admins()
    if df.empty:
        return False
    return email in df["admin_email"].values

# ── users_cache ──────────────────────────────────────────

def upsert_user_cache(email: str, name: str):
    ws = get_sheet("users_cache")
    records = ws.get_all_records()
    now = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    for i, row in enumerate(records, start=2):
        if row["email"] == email:
            ws.update_cell(i, 2, name)
            ws.update_cell(i, 3, now)
            return
    ws.append_row([email, name, now])
    clear_cache()

def get_all_teachers() -> pd.DataFrame:
    users = get_df("users_cache")
    admins = get_admins()
    if users.empty:
        return users
    admin_emails = admins["admin_email"].tolist() if not admins.empty else []
    return users[~users["email"].isin(admin_emails)].reset_index(drop=True)
