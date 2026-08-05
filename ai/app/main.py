from typing import Annotated
from pathlib import Path
from uuid import uuid4
import cv2
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from ultralytics import YOLO

app = FastAPI(
    title="Counter Stock AI API",
    description="商品画像を解析のためのAPI",
    version="1.0.0",
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

RESULT_DIR = Path("results")
RESULT_DIR.mkdir(parents=True, exist_ok=True)

app.mount(
    "/results",
    StaticFiles(directory=RESULT_DIR),
    name = "results"
)

ALLOWED_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

model = YOLO("yolo11n.pt")


@app.get("/")
def root():
    return {"message": "counter AI API is running"}

@app.get("/health")
def health_check():
    return {"status":"healthy"}


@app.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="JPEG,PNG,WEBP形式の画像を送信してください",
        )

    extension = ALLOWED_CONTENT_TYPES[file.content_type]
    saved_filename = f"{uuid4().hex}{extension}"
    saved_path = UPLOAD_DIR / saved_filename

    try:
        file_data = await file.read()

        if not file_data:
            raise HTTPException(
                status_code=400,
                detail="ファイル内容が空です",
            )
        with saved_path.open("wb") as output_file:
            output_file.write(file_data)

        results = model(str(saved_path))
        annotated_image = results[0].plot()

        detections = []
        class_counts = {}
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0].item())
                class_name = model.names[class_id]
                confidence = float(box.conf[0].item())

                # x1, y1, x2, y2 の順序に修正
                x1, y1, x2, y2 = box.xyxy[0].tolist()

                class_counts[class_name] = class_counts.get(class_name, 0)+1

                detections.append(
                    {
                        "class_id": class_id,
                        "class_name": class_name,
                        "confidence": round(confidence, 3),
                        "bounding_box": {
                            "x1": round(x1, 3),
                            "y1": round(y1, 3),
                            "x2": round(x2, 3),
                            "y2": round(y2, 3),
                        },
                    }
                )

        result_filename = f"result_{saved_filename}"
        result_path = RESULT_DIR / result_filename
        image_saved = cv2.imwrite(str(result_path), annotated_image)

        if not image_saved:
            raise HTTPException(
                status_code = 500,
                detail = "検出画像の保存に失敗しました"
            )


        return {
            "message": "画像の解析が完了しました",
            "original_filename": file.filename,
            "saved_filename": saved_filename,
            "result_filename": result_filename,
            "content_type": file.content_type,
            "size": len(file_data),
            "detection_count": len(detections),
            "class_counts":class_counts,
            "detections": detections,
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"画像の解析に失敗しました:{error}",
        ) from error

    finally:
        await file.close()
  
