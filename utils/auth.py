import streamlit as st
import requests
from authlib.integrations.requests_client import OAuth2Session
from utils.sheets import upsert_user_cache, is_admin

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

SCOPES = "openid email profile"

def get_oauth_session():
    return OAuth2Session(
        client_id=st.secrets["oauth"]["client_id"],
        client_secret=st.secrets["oauth"]["client_secret"],
        redirect_uri=st.secrets["oauth"]["redirect_uri"],
        scope=SCOPES,
    )

def login():
    params = st.query_params

    # 處理 OAuth callback
    if "code" in params:
        try:
            oauth = get_oauth_session()
            current_url = st.secrets["oauth"]["redirect_uri"] + "?code=" + params["code"]
            if "state" in params:
                current_url += "&state=" + params["state"]

            token = oauth.fetch_token(
                GOOGLE_TOKEN_URL,
                authorization_response=current_url,
                grant_type="authorization_code",
            )

            # 取得使用者資訊
            resp = oauth.get(GOOGLE_USERINFO_URL)
            user_info = resp.json()

            user = {
                "email": user_info["email"],
                "name": user_info.get("name", user_info["email"].split("@")[0]),
            }
            st.session_state["user"] = user
            upsert_user_cache(user["email"], user["name"])
            st.query_params.clear()
            st.rerun()

        except Exception as e:
            st.error(f"登入失敗，請重新整理頁面再試。（{e}）")
            st.query_params.clear()
            return

    # 未登入：顯示登入頁面
    if "user" not in st.session_state:
        st.markdown("""
            <div style='text-align:center; padding: 4rem 1rem;'>
                <div style='font-size:48px;'>📋</div>
                <h2 style='margin:1rem 0 0.5rem;'>公開觀課平台</h2>
                <p style='color:gray; margin-bottom:2rem;'>請使用學校 Google 帳號登入</p>
            </div>
        """, unsafe_allow_html=True)

        oauth = get_oauth_session()
        auth_url, state = oauth.create_authorization_url(
            GOOGLE_AUTH_URL,
            access_type="offline",
            prompt="select_account",
        )

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(f"""
                <a href="{auth_url}" target="_self" style="
                    display: block;
                    text-align: center;
                    background-color: #2563EB;
                    color: white;
                    padding: 0.6rem 1.2rem;
                    border-radius: 8px;
                    text-decoration: none;
                    font-size: 15px;
                    font-weight: 500;
                    margin-top: 0.5rem;
                ">🔐 使用 Google 帳號登入</a>
            """, unsafe_allow_html=True)
        st.stop()

def require_login():
    login()
    if "user" not in st.session_state:
        st.stop()
    return st.session_state["user"]

def require_admin():
    user = require_login()
    if not is_admin(user["email"]):
        st.error("⛔ 此頁面僅限單位主管使用")
        st.stop()
    return user

def logout():
    if "user" in st.session_state:
        del st.session_state["user"]
    st.rerun()
