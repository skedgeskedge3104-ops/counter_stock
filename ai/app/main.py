from fastapi import FastAPI

app = FastAPI(
    title="Counter Stock AI API",
    description="景品管理アプリの画像認識・OCR用API",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "counter-stock-ai",
    }
