import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.service_account import Credentials
import io

SCOPES = ["https://www.googleapis.com/auth/drive"]

@st.cache_resource
def get_drive_service():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)

def upload_photo(file_bytes: bytes, filename: str, mime_type: str = "image/jpeg") -> str:
    """
    上傳照片至 Google Drive 觀課照片資料夾
    回傳可公開存取的圖片 URL
    """
    service = get_drive_service()
    folder_id = st.secrets["drive"]["photo_folder_id"]

    file_metadata = {
        "name": filename,
        "parents": [folder_id],
    }
    media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype=mime_type, resumable=False)

    uploaded = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()

    file_id = uploaded.get("id")

    # 設定公開讀取權限
    service.permissions().create(
        fileId=file_id,
        body={"type": "anyone", "role": "reader"},
    ).execute()

    return f"https://drive.google.com/thumbnail?id={file_id}&sz=w400"

def upload_photos(uploaded_files, session_id: str, observer_email: str) -> list[str]:
    """
    批次上傳多張照片，回傳 URL 清單
    """
    urls = []
    for i, f in enumerate(uploaded_files):
        ext = f.name.split(".")[-1].lower()
        mime = "image/png" if ext == "png" else "image/jpeg"
        filename = f"{session_id}_{observer_email.split('@')[0]}_{i+1}.{ext}"
        url = upload_photo(f.read(), filename, mime)
        urls.append(url)
    return urls
