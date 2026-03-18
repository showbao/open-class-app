import base64
import io
from PIL import Image

def compress_and_encode(file_bytes: bytes, max_size_kb: int = 200) -> str:
    """
    壓縮圖片並轉為 base64 字串
    預設壓縮到 200KB 以下，避免 Sheets 單格超過限制
    """
    img = Image.open(io.BytesIO(file_bytes))

    # 轉為 RGB（避免 PNG 透明度問題）
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # 縮小尺寸：最大寬度 800px
    max_width = 800
    if img.width > max_width:
        ratio = max_width / img.width
        new_size = (max_width, int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)

    # 壓縮品質直到低於 max_size_kb
    quality = 85
    while quality >= 30:
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        size_kb = buffer.tell() / 1024
        if size_kb <= max_size_kb:
            break
        quality -= 10

    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"

def encode_photos(uploaded_files) -> list[str]:
    """
    批次處理多張上傳照片，回傳 base64 字串清單
    """
    result = []
    for f in uploaded_files:
        b64 = compress_and_encode(f.read())
        result.append(b64)
    return result

def decode_photo_urls(photo_data: str) -> list[str]:
    """
    從 Sheets 讀出的資料解析成 base64 字串清單
    base64 字串之間用 ||| 分隔（避免和 base64 內容衝突）
    """
    if not photo_data or not str(photo_data).strip():
        return []
    return [p.strip() for p in str(photo_data).split("|||") if p.strip()]
