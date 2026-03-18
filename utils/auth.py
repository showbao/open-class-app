import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
import datetime
import secrets
import hashlib
import base64
from utils.sheets import upsert_user_cache, is_admin

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

def get_flow():
    client_config = {
        "web": {
            "client_id": st.secrets["oauth"]["client_id"],
            "client_secret": st.secrets["oauth"]["client_secret"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [st.secrets["oauth"]["redirect_uri"]],
        }
    }
    flow = Flow.from_client_config(client_config, scopes=SCOPES)
    flow.redirect_uri = st.secrets["oauth"]["redirect_uri"]
    return flow

def generate_pkce():
    """產生 PKCE code_verifier 與 code_challenge"""
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b"=").decode()
    return code_verifier, code_challenge

def login():
    """顯示登入按鈕，處理 OAuth callback"""
    params = st.query_params

    # 處理 OAuth callback
    if "code" in params:
        try:
            flow = get_flow()
            # 取回之前存的 code_verifier
            code_verifier = st.session_state.get("pkce_verifier", None)
            if code_verifier:
                flow.fetch_token(
                    code=params["code"],
                    code_verifier=code_verifier
                )
            else:
                flow.fetch_token(code=params["code"])

            credentials = flow.credentials
            id_info = id_token.verify_oauth2_token(
                credentials.id_token,
                grequests.Request(),
                st.secrets["oauth"]["client_id"]
            )
            user = {
                "email": id_info["email"],
                "name": id_info.get("name", id_info["email"].split("@")[0]),
            }
            st.session_state["user"] = user
            # 清除 PKCE verifier
            if "pkce_verifier" in st.session_state:
                del st.session_state["pkce_verifier"]
            upsert_user_cache(user["email"], user["name"])
            st.query_params.clear()
            st.rerun()
        except Exception as e:
            st.error(f"登入失敗，請重新嘗試。（{e}）")
            # 清除殘留參數，讓使用者可以重新登入
            st.query_params.clear()
            if "pkce_verifier" in st.session_state:
                del st.session_state["pkce_verifier"]
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

        # 產生 PKCE 並存入 session
        code_verifier, code_challenge = generate_pkce()
        st.session_state["pkce_verifier"] = code_verifier

        flow = get_flow()
        auth_url, _ = flow.authorization_url(
            prompt="select_account",
            access_type="offline",
            code_challenge=code_challenge,
            code_challenge_method="S256"
        )

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.link_button("🔐 使用 Google 帳號登入", auth_url, use_container_width=True)
        st.stop()

def require_login():
    """確保已登入，否則導向登入流程"""
    login()
    if "user" not in st.session_state:
        st.stop()
    return st.session_state["user"]

def require_admin():
    """確保為主管身份"""
    user = require_login()
    if not is_admin(user["email"]):
        st.error("⛔ 此頁面僅限單位主管使用")
        st.stop()
    return user

def logout():
    if "user" in st.session_state:
        del st.session_state["user"]
    st.rerun()
