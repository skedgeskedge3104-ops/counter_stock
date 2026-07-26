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

@app.get("/")
def root():
    return{
        "message":"Counter Stock AI API in running"
    }

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "counter-stock-ai",
    }

@app.post("/upload")
async def upload_image(
    file:UploadFile = File(...)
):

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code = 400,
            detail = "JPEG、PNG、WebP形式の画像を送信してください",
        )

    extension = ALLOWED_CONTENT_TYPES[file.content_type]
    saved_filename = f"{uuid4().hex}{extension}"
    saved_path = UPLOAD_DIR/saved_filename

    try:
        file_data = await file.read()

        if not file_data:
            raise HTTPException(
                status_code = 400,
                detail = "ファイル内容が空です"
            )

        with saved_patth.open("wb") as output_file:
            output_file.write(file_data)


    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code = 500,
            detail = f"画像の保存に失敗しました:{error}",
        ) from error

    finally:
        await file.close()

    return {
        "message":"画像を受信しました",
        "original_filename":"file.filename",
        "saved_filename":"saved_filename",
        "countent_type":"file.countent_type",
        "size":"len(file_data)"
    }

