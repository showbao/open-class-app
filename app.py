import io
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

APP_TITLE = "公開觀課 MVP"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

WORKSHEET_SCHEMAS = {
    "admins": ["email", "name", "note", "created_at"],
    "supervisors": ["email", "name", "title", "active", "created_at"],
    "sessions": [
        "session_id",
        "session_date",
        "teacher_email",
        "teacher_name",
        "grade",
        "class_name",
        "subject",
        "lesson_title",
        "observer_email",
        "observer_name",
        "status",
        "created_at",
        "updated_at",
    ],
    "observations": [
        "record_id",
        "session_id",
        "teacher_email",
        "teacher_name",
        "observer_email",
        "observer_name",
        "strengths",
        "suggestions",
        "observation_notes",
        "text_status",
        "photo_status",
        "photo_urls",
        "photo_count",
        "submitted_text_at",
        "submitted_photo_at",
        "last_saved_at",
    ],
}


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def safe_user_value(key: str, default: str = "") -> str:
    try:
        value = st.user.get(key)
        return value or default
    except Exception:
        return default


def get_user_email() -> str:
    return safe_user_value("email", "").strip().lower()


def get_user_name() -> str:
    return safe_user_value("name", "未命名使用者").strip()


def get_current_app_base_url() -> str:
    try:
        headers = st.context.headers
        proto = headers.get("x-forwarded-proto") or headers.get("X-Forwarded-Proto") or "https"
        host = headers.get("x-forwarded-host") or headers.get("host") or headers.get("Host")
        if host:
            return f"{proto}://{host}"
    except Exception:
        pass
    return "目前抓不到網址，可直接查看瀏覽器上方網址列"


def get_allowed_domains() -> List[str]:
    raw = st.secrets.get("ALLOWED_DOMAINS", [])
    if isinstance(raw, str):
        return [item.strip().lower() for item in raw.split(",") if item.strip()]
    if isinstance(raw, (list, tuple)):
        return [str(item).strip().lower() for item in raw if str(item).strip()]
    return []


def flatten_secret_check() -> List[str]:
    missing = []
    required_top = [
        "ALLOWED_DOMAINS",
        "GOOGLE_SHEET_KEY",
        "GOOGLE_DRIVE_FOLDER_ID",
        "gcp_service_account",
        "auth",
    ]
    for key in required_top:
        if key not in st.secrets:
            missing.append(key)

    auth_keys = [
        "redirect_uri",
        "cookie_secret",
        "client_id",
        "client_secret",
        "server_metadata_url",
    ]
    auth_block = st.secrets.get("auth", {})
    for key in auth_keys:
        if not auth_block.get(key):
            missing.append(f"auth.{key}")
    return missing


def validate_required_secrets() -> None:
    missing = flatten_secret_check()
    if not missing:
        return

    st.error("找不到必要設定，App 先暫停。")
    st.write("缺少的項目：")
    for item in missing:
        st.write(f"- {item}")
    st.info("請到 Streamlit Community Cloud 的 App settings → Secrets 修正。")
    st.code(
        f"目前偵測到的 App 網址參考：\n{get_current_app_base_url()}\n\n"
        f"登入回跳網址應該長這樣：\n{get_current_app_base_url()}/oauth2callback"
    )
    st.stop()


@st.cache_resource(show_spinner=False)
def get_google_clients():
    service_account_info = dict(st.secrets["gcp_service_account"])
    credentials = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    gc = gspread.authorize(credentials)
    drive_service = build("drive", "v3", credentials=credentials)
    return gc, drive_service


@st.cache_resource(show_spinner=False)
def get_spreadsheet():
    gc, _ = get_google_clients()
    return gc.open_by_key(st.secrets["GOOGLE_SHEET_KEY"])


def get_worksheet(name: str):
    spreadsheet = get_spreadsheet()
    try:
        return spreadsheet.worksheet(name)
    except gspread.WorksheetNotFound:
        return None


def ensure_worksheet(name: str, headers: List[str]):
    spreadsheet = get_spreadsheet()
    worksheet = get_worksheet(name)
    if worksheet is None:
        worksheet = spreadsheet.add_worksheet(title=name, rows=200, cols=max(20, len(headers) + 2))
        worksheet.append_row(headers)
        return worksheet

    current_headers = worksheet.row_values(1)
    if current_headers != headers:
        worksheet.clear()
        worksheet.append_row(headers)
    return worksheet


def bootstrap_worksheets() -> List[str]:
    created = []
    for name, headers in WORKSHEET_SCHEMAS.items():
        worksheet = get_worksheet(name)
        if worksheet is None:
            ensure_worksheet(name, headers)
            created.append(f"已建立工作表：{name}")
        else:
            current_headers = worksheet.row_values(1)
            if current_headers != headers:
                ensure_worksheet(name, headers)
                created.append(f"已重設表頭：{name}")
    return created


def get_records(sheet_name: str) -> List[Dict[str, str]]:
    worksheet = ensure_worksheet(sheet_name, WORKSHEET_SCHEMAS[sheet_name])
    return worksheet.get_all_records()


def append_record(sheet_name: str, record: Dict[str, str]) -> None:
    worksheet = ensure_worksheet(sheet_name, WORKSHEET_SCHEMAS[sheet_name])
    row = [record.get(header, "") for header in WORKSHEET_SCHEMAS[sheet_name]]
    worksheet.append_row(row, value_input_option="USER_ENTERED")


def find_row_number_by_key(sheet_name: str, key_column: str, key_value: str) -> Optional[int]:
    worksheet = ensure_worksheet(sheet_name, WORKSHEET_SCHEMAS[sheet_name])
    headers = worksheet.row_values(1)
    if key_column not in headers:
        raise ValueError(f"{sheet_name} 找不到欄位：{key_column}")
    all_values = worksheet.get_all_values()
    key_index = headers.index(key_column)
    target = str(key_value).strip()
    for row_number, row in enumerate(all_values[1:], start=2):
        row_value = row[key_index].strip() if key_index < len(row) else ""
        if row_value == target:
            return row_number
    return None


def update_row_by_key(sheet_name: str, key_column: str, key_value: str, new_data: Dict[str, str]) -> None:
    worksheet = ensure_worksheet(sheet_name, WORKSHEET_SCHEMAS[sheet_name])
    row_number = find_row_number_by_key(sheet_name, key_column, key_value)
    if row_number is None:
        raise ValueError(
            f"更新失敗：找不到資料列。sheet_name={sheet_name}, key_column={key_column}, key_value={key_value}"
        )
    headers = worksheet.row_values(1)
    current_row = worksheet.row_values(row_number)
    padded_row = current_row + [""] * (len(headers) - len(current_row))
    for idx, header in enumerate(headers):
        if header in new_data:
            padded_row[idx] = str(new_data[header])
    cell_range = f"A{row_number}:{gspread.utils.rowcol_to_a1(row_number, len(headers)).split(str(row_number))[0]}{row_number}"
    worksheet.update(cell_range, [padded_row], value_input_option="USER_ENTERED")


def upsert_simple_record(sheet_name: str, key_column: str, key_value: str, record: Dict[str, str]) -> None:
    row_number = find_row_number_by_key(sheet_name, key_column, key_value)
    if row_number is None:
        append_record(sheet_name, record)
    else:
        update_row_by_key(sheet_name, key_column, key_value, record)


def build_drive_file_url(file_id: str) -> str:
    return f"https://drive.google.com/file/d/{file_id}/view"


def get_or_create_drive_folder(folder_name: str, parent_id: str) -> str:
    _, drive_service = get_google_clients()
    escaped_name = folder_name.replace("'", "\\'")
    query = (
        f"name = '{escaped_name}' and '{parent_id}' in parents and "
        "mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    )
    response = drive_service.files().list(q=query, fields="files(id, name)").execute()
    files = response.get("files", [])
    if files:
        return files[0]["id"]

    metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    created = drive_service.files().create(body=metadata, fields="id").execute()
    return created["id"]


def upload_file_to_drive(file_bytes: bytes, filename: str, mime_type: str, parent_id: str) -> str:
    _, drive_service = get_google_clients()
    media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype=mime_type, resumable=False)
    metadata = {"name": filename, "parents": [parent_id]}
    uploaded = drive_service.files().create(body=metadata, media_body=media, fields="id").execute()
    return uploaded["id"]


def normalize_file_name(session_id: str, record_id: str, index: int, original_name: str) -> str:
    ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else "jpg"
    return f"{session_id}_{record_id}_{index}.{ext}"


def reset_observation_flow_state() -> None:
    for key in ["text_saved_record_id", "saving_text", "uploading_photo", "photo_1", "photo_2"]:
        if key in st.session_state:
            del st.session_state[key]


def get_role_maps() -> Tuple[set, set]:
    admins = {row["email"].strip().lower() for row in get_records("admins") if row.get("email")}
    supervisors = {
        row["email"].strip().lower()
        for row in get_records("supervisors")
        if row.get("email") and str(row.get("active", "TRUE")).strip().upper() != "FALSE"
    }
    return admins, supervisors


def get_sessions_for_teacher(email: str) -> List[Dict[str, str]]:
    rows = get_records("sessions")
    teacher_rows = [row for row in rows if row.get("teacher_email", "").strip().lower() == email]
    return sorted(teacher_rows, key=lambda x: x.get("session_date", ""), reverse=True)


def get_sessions_for_supervisor(email: str) -> List[Dict[str, str]]:
    rows = get_records("sessions")
    observer_rows = [row for row in rows if row.get("observer_email", "").strip().lower() == email]
    return sorted(observer_rows, key=lambda x: x.get("session_date", ""), reverse=True)


def find_observation_by_session_and_teacher(session_id: str, teacher_email: str) -> Optional[Dict[str, str]]:
    rows = get_records("observations")
    for row in rows:
        if (
            row.get("session_id", "").strip() == session_id
            and row.get("teacher_email", "").strip().lower() == teacher_email.strip().lower()
        ):
            return row
    return None


def login_guard() -> None:
    st.title(APP_TITLE)
    st.caption("校內公開觀課用。請先用 Google 帳號登入。")
    st.button("使用 Google 登入", on_click=st.login, type="primary")
    st.stop()


def domain_guard() -> None:
    email = get_user_email()
    allowed_domains = get_allowed_domains()
    if not email or "@" not in email:
        st.error("抓不到登入信箱，請重新登入。")
        st.button("登出", on_click=st.logout)
        st.stop()

    user_domain = email.split("@")[-1]
    if allowed_domains and user_domain not in allowed_domains:
        st.error("這個帳號不在允許名單內。")
        st.write(f"目前登入：{email}")
        st.write(f"允許網域：{', '.join(allowed_domains)}")
        st.button("登出", on_click=st.logout)
        st.stop()


def header_block(role_text: str) -> None:
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title(APP_TITLE)
        st.caption(f"登入者：{get_user_name()}｜{get_user_email()}｜身分：{role_text}")
    with col2:
        st.button("登出", on_click=st.logout, use_container_width=True)


def teacher_page() -> None:
    st.subheader("老師填寫")
    email = get_user_email()
    teacher_name = get_user_name()
    sessions = get_sessions_for_teacher(email)
    if not sessions:
        st.info("你目前沒有被指派的觀課場次。")
        return

    options = {
        f"{row['session_date']}｜{row['subject']}｜{row['class_name']}｜{row['lesson_title']}": row
        for row in sessions
    }
    selected_label = st.selectbox("選擇場次", list(options.keys()))
    session = options[selected_label]
    session_id = session["session_id"]

    existing_record = find_observation_by_session_and_teacher(session_id, email)
    if existing_record and existing_record.get("record_id"):
        st.success("已找到先前紀錄，你可以直接續填或續傳照片。")
        st.session_state["text_saved_record_id"] = existing_record["record_id"]

    with st.container(border=True):
        st.write(f"**日期**：{session['session_date']}")
        st.write(f"**年級班級**：{session['grade']} {session['class_name']}")
        st.write(f"**科目**：{session['subject']}")
        st.write(f"**課題**：{session['lesson_title']}")
        st.write(f"**主管**：{session['observer_name']}（{session['observer_email']}）")

    strengths_default = existing_record.get("strengths", "") if existing_record else ""
    suggestions_default = existing_record.get("suggestions", "") if existing_record else ""
    notes_default = existing_record.get("observation_notes", "") if existing_record else ""

    strengths = st.text_area("這堂課做得好的地方", value=strengths_default, height=120)
    suggestions = st.text_area("我想再調整的地方", value=suggestions_default, height=120)
    observation_notes = st.text_area("補充說明", value=notes_default, height=120)

    if st.button("先存文字", type="primary", use_container_width=True):
        st.session_state["saving_text"] = True
        record_id = existing_record["record_id"] if existing_record else f"rec_{uuid.uuid4().hex[:10]}"
        payload = {
            "record_id": record_id,
            "session_id": session_id,
            "teacher_email": email,
            "teacher_name": session.get("teacher_name") or teacher_name,
            "observer_email": session["observer_email"],
            "observer_name": session["observer_name"],
            "strengths": strengths,
            "suggestions": suggestions,
            "observation_notes": observation_notes,
            "text_status": "done",
            "photo_status": existing_record.get("photo_status", "pending") if existing_record else "pending",
            "photo_urls": existing_record.get("photo_urls", "") if existing_record else "",
            "photo_count": existing_record.get("photo_count", "0") if existing_record else "0",
            "submitted_text_at": existing_record.get("submitted_text_at") or now_text() if existing_record else now_text(),
            "submitted_photo_at": existing_record.get("submitted_photo_at", "") if existing_record else "",
            "last_saved_at": now_text(),
        }
        upsert_simple_record("observations", "record_id", record_id, payload)
        st.session_state["text_saved_record_id"] = record_id
        st.success("文字已存好。現在可以上傳照片。")

    record_id = st.session_state.get("text_saved_record_id") or (existing_record or {}).get("record_id")
    if not record_id:
        st.warning("請先按『先存文字』，再上傳照片。")
        return

    st.markdown("---")
    st.subheader("第二步：上傳照片")
    photo_1 = st.file_uploader("照片 1", type=["jpg", "jpeg", "png"], key="photo_1")
    photo_2 = st.file_uploader("照片 2", type=["jpg", "jpeg", "png"], key="photo_2")

    existing_urls = []
    if existing_record and existing_record.get("photo_urls"):
        existing_urls = [item for item in existing_record["photo_urls"].split("\n") if item.strip()]
        if existing_urls:
            st.write("已上傳照片：")
            for idx, url in enumerate(existing_urls, start=1):
                st.markdown(f"{idx}. [查看照片]({url})")

    if st.button("送出照片", use_container_width=True):
        st.session_state["uploading_photo"] = True
        upload_files = [file for file in [photo_1, photo_2] if file is not None]
        if not upload_files:
            st.warning("至少要選 1 張照片。")
            return

        session_folder_id = get_or_create_drive_folder(session_id, st.secrets["GOOGLE_DRIVE_FOLDER_ID"])
        record_folder_id = get_or_create_drive_folder(record_id, session_folder_id)

        new_urls = list(existing_urls)
        for index, file in enumerate(upload_files, start=len(existing_urls) + 1):
            new_name = normalize_file_name(session_id, record_id, index, file.name)
            file_id = upload_file_to_drive(file.getvalue(), new_name, file.type or "image/jpeg", record_folder_id)
            new_urls.append(build_drive_file_url(file_id))

        update_row_by_key(
            "observations",
            "record_id",
            record_id,
            {
                "photo_status": "done",
                "photo_urls": "\n".join(new_urls),
                "photo_count": str(len(new_urls)),
                "submitted_photo_at": now_text(),
                "last_saved_at": now_text(),
            },
        )
        update_row_by_key(
            "sessions",
            "session_id",
            session_id,
            {"status": "completed", "updated_at": now_text()},
        )
        st.success("照片已上傳完成，這堂課已送出。")
        reset_observation_flow_state()


def supervisor_page(is_admin: bool = False) -> None:
    st.subheader("主管查看")
    email = get_user_email()
    session_rows = get_records("sessions")
    observation_rows = get_records("observations")

    if not is_admin:
        session_ids = {
            row["session_id"]
            for row in session_rows
            if row.get("observer_email", "").strip().lower() == email
        }
        observation_rows = [row for row in observation_rows if row.get("session_id") in session_ids]

    if not observation_rows:
        st.info("目前沒有可查看的紀錄。")
        return

    status_filter = st.selectbox("篩選狀態", ["全部", "已完成", "只有文字"])
    for row in sorted(observation_rows, key=lambda x: x.get("last_saved_at", ""), reverse=True):
        photo_done = row.get("photo_status") == "done"
        if status_filter == "已完成" and not photo_done:
            continue
        if status_filter == "只有文字" and photo_done:
            continue

        with st.container(border=True):
            st.write(f"**場次**：{row['session_id']}")
            st.write(f"**老師**：{row['teacher_name']}（{row['teacher_email']}）")
            st.write(f"**主管**：{row['observer_name']}（{row['observer_email']}）")
            st.write(f"**文字狀態**：{row['text_status']}｜**照片狀態**：{row['photo_status']}")
            st.write(f"**優點**：{row['strengths']}")
            st.write(f"**可調整**：{row['suggestions']}")
            st.write(f"**補充**：{row['observation_notes']}")
            urls = [item for item in row.get("photo_urls", "").split("\n") if item.strip()]
            if urls:
                st.write("**照片**：")
                for idx, url in enumerate(urls, start=1):
                    st.markdown(f"{idx}. [查看照片]({url})")
            st.caption(f"最後更新：{row.get('last_saved_at', '')}")


def admin_page() -> None:
    st.subheader("管理者設定")
    st.caption("這裡用來建立表頭、加主管、加管理者、開觀課場次。")

    with st.container(border=True):
        st.write("**資料表檢查**")
        if st.button("建立 / 修正四張工作表", use_container_width=True):
            messages = bootstrap_worksheets()
            if messages:
                for msg in messages:
                    st.success(msg)
            else:
                st.success("四張工作表都已就緒。")

    with st.container(border=True):
        st.write("**新增主管**")
        with st.form("add_supervisor_form"):
            email = st.text_input("主管信箱")
            name = st.text_input("主管姓名")
            title = st.text_input("職稱", value="主任")
            submitted = st.form_submit_button("新增主管")
            if submitted:
                payload = {
                    "email": email.strip().lower(),
                    "name": name.strip(),
                    "title": title.strip(),
                    "active": "TRUE",
                    "created_at": now_text(),
                }
                upsert_simple_record("supervisors", "email", payload["email"], payload)
                st.success("主管已存好。")

    with st.container(border=True):
        st.write("**新增管理者**")
        with st.form("add_admin_form"):
            email = st.text_input("管理者信箱")
            name = st.text_input("管理者姓名")
            note = st.text_input("備註", value="")
            submitted = st.form_submit_button("新增管理者")
            if submitted:
                payload = {
                    "email": email.strip().lower(),
                    "name": name.strip(),
                    "note": note.strip(),
                    "created_at": now_text(),
                }
                upsert_simple_record("admins", "email", payload["email"], payload)
                st.success("管理者已存好。")

    supervisors = get_records("supervisors")
    supervisor_options = {
        f"{row['name']}｜{row['email']}": row
        for row in supervisors
        if row.get("email") and str(row.get("active", "TRUE")).strip().upper() != "FALSE"
    }

    with st.container(border=True):
        st.write("**新增觀課場次**")
        with st.form("add_session_form"):
            session_date = st.date_input("日期")
            teacher_email = st.text_input("老師信箱")
            teacher_name = st.text_input("老師姓名")
            grade = st.text_input("年級", value="五年級")
            class_name = st.text_input("班級", value="1班")
            subject = st.text_input("科目", value="國語")
            lesson_title = st.text_input("課題", value="課程主題")
            selected_supervisor_label = st.selectbox(
                "指派主管",
                list(supervisor_options.keys()) if supervisor_options else ["請先建立主管"],
            )
            submitted = st.form_submit_button("建立場次")
            if submitted:
                if not supervisor_options:
                    st.error("請先建立主管名單。")
                else:
                    supervisor = supervisor_options[selected_supervisor_label]
                    session_id = f"ses_{uuid.uuid4().hex[:8]}"
                    payload = {
                        "session_id": session_id,
                        "session_date": str(session_date),
                        "teacher_email": teacher_email.strip().lower(),
                        "teacher_name": teacher_name.strip(),
                        "grade": grade.strip(),
                        "class_name": class_name.strip(),
                        "subject": subject.strip(),
                        "lesson_title": lesson_title.strip(),
                        "observer_email": supervisor["email"],
                        "observer_name": supervisor["name"],
                        "status": "assigned",
                        "created_at": now_text(),
                        "updated_at": now_text(),
                    }
                    append_record("sessions", payload)
                    st.success(f"場次已建立，編號：{session_id}")

    with st.expander("查看目前名單與場次"):
        st.write("**管理者**")
        st.dataframe(get_records("admins"), use_container_width=True)
        st.write("**主管**")
        st.dataframe(get_records("supervisors"), use_container_width=True)
        st.write("**場次**")
        st.dataframe(get_records("sessions"), use_container_width=True)


def determine_role() -> Tuple[bool, bool, bool]:
    email = get_user_email()
    admins, supervisors = get_role_maps()
    is_admin = email in admins
    is_supervisor = email in supervisors or bool(get_sessions_for_supervisor(email))
    is_teacher = bool(get_sessions_for_teacher(email))
    return is_admin, is_supervisor, is_teacher


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="📘", layout="centered")
    validate_required_secrets()

    if not st.user.is_logged_in:
        login_guard()

    domain_guard()
    bootstrap_worksheets()

    is_admin, is_supervisor, is_teacher = determine_role()
    role_text_list = []
    if is_admin:
        role_text_list.append("管理者")
    if is_supervisor:
        role_text_list.append("主管")
    if is_teacher:
        role_text_list.append("老師")
    if not role_text_list:
        role_text_list.append("一般登入者")

    header_block(" / ".join(role_text_list))

    pages = []
    if is_teacher:
        pages.append("老師填寫")
    if is_supervisor or is_admin:
        pages.append("主管查看")
    if is_admin:
        pages.append("管理者設定")

    if not pages:
        st.warning("你已登入，但目前沒有可用頁面。請請管理者把你加入名單或建立場次。")
        return

    selected_page = st.segmented_control("功能", options=pages, default=pages[0], selection_mode="single")

    if selected_page == "老師填寫":
        teacher_page()
    elif selected_page == "主管查看":
        supervisor_page(is_admin=is_admin)
    elif selected_page == "管理者設定":
        admin_page()


if __name__ == "__main__":
    main()
