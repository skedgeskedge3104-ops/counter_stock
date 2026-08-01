from pathlib import Path
from uuid import uuid4
from fastapi import FastAPI, File, HTTPException,UploadFile
from ultralytics import YOLO


app = FastAPI(
    title = "Counter Stock AI API",
    description = "商品画像を解析のためのAPI",
    version = "1.0.0"
)


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents = True,exist_ok = True)

ALLOWED_CONTENT_TYPES = {
    "image/jpeg":".jpg",
    "image/png":".png",
    "image/webp":".webp"
}


model = YOLO("yolo11n.pt")

@app.get("/")
def root():
    return {"message": "counter AI API is running"}


@app.post("/upload")
async def upload_image(
    file: UploadFile = File(...)
):

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code = 400,
            detail = "JPEG,PNG,WEBP形式の画像を送信してください",
        )

    extension = ALLOWED_CONTENT_TYPES[file.content_type]
    saved_filename = f"{uuid4().hex}{extension}"
    saved_path = UPLOAD_DIR /saved_filename

    try:
        file_data = await file.read()

        if not file_data:
            raise HTTPException(
                status_code = 400,
                detail = "ファイル内容が空です",
            )
        with saved_path.open("wb") as output_file:
            output_file.write(file_data)

        results = model(str(saved_path))

        detections = []
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0].item())
                confidence = float(box.conf[0].item())

                x1,x2,y1,y2 = box.xyxy[0].tolist()

                detections.append({
                    "class_id":class_id,
                    "class_name":model.names[class_id],
                    "confidence":round(confidence,3),
                    "bounding_box":{
                        "x1":round(x1,3),
                        "y1":round(y1,3),
                        "x2":round(x2,3),
                        "y2":round(y2,3),
                    },

                })

        return {
            "message":"画像を受信しました",
            "original_filename":"file.filename",
            "saved_filename":saved_filename,
            "content_type":file.content_type,
            "size":len(file_data),
            "detection_count":len(detections),
            "detections":detections,
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code = 500,
            detail = f"画像の保存に失敗しました:{error}",
        ) from error

    finally:
        await file.close()

