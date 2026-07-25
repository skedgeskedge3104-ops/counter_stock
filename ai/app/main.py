from pathlib import Path
from uuid import uuid4
from fastapi import FastAPI,UploadFile,File,HTTPException

app = FastAPI(
    title="Counter Stock AI API",
    description="景品管理アプリの画像認識・OCR用API",
    version="0.1.0",
)

#アップロードされた画像の保存先
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

#受け付ける画像形式
ALLOWED_CONTENT_TYPES ={
    "image/jpeg":".JPG",
    "image/png":".PNG",
    "image/WEBP":".WEBP"
}



@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "counter-stock-ai",
    }


