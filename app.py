from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
from PIL import Image
import io
import time
import os

app = FastAPI(
    title="RUAS AI Microservice",
    description="FastAPI service running YOLO26 (yolo26n.pt) for road damage detection",
    version="1.0.0",
)

# CORS configuration
allowed_origins_env = os.getenv("CORS_ORIGINS", "*")
allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load YOLO26 model
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MODEL_PATH = os.path.join(CURRENT_DIR, "yolo26n.pt")
MODEL_PATH = os.getenv("MODEL_PATH", DEFAULT_MODEL_PATH)
try:
    model = YOLO(MODEL_PATH)
except Exception as e:
    print(f"Warning: Model load failure at startup: {e}")
    model = None

@app.get("/")
def health_check():
    """
    Health check endpoint untuk memverifikasi kesiapan service di Render
    tanpa memerlukan upload file.
    """
    return {
        "status": "ok",
        "service": "ruas-ai",
        "model_loaded": model is not None,
        "model_version": "yolo26n-v1",
    }

# Pemetaan nama kelas YOLO ke snake_case standar contract
CLASS_NAME_MAP = {
    "retak memanjang": "retak_memanjang",
    "retak melintang": "retak_melintang",
    "retak buaya": "retak_buaya",
    "lubang": "lubang",
}

@app.post("/deteksi")
async def deteksi(file: UploadFile = File(...)):
    """
    Endpoint deteksi kerusakan jalan.
    Menerima file gambar via multipart/form-data.
    Mengembalikan array deteksi berformat standar:
    {
      "detections": [
        { "class_name": str, "confidence": float, "x": float, "y": float, "w": float, "h": float }
      ],
      "model_version": "yolo26n-v1",
      "processing_time_ms": int
    }
    """
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Model AI belum berhasil dimuat. Periksa file yolo26n.pt pada environment.",
        )

    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail=f"Format file tidak didukung: {file.content_type}. Unggah file gambar.",
        )

    start_time = time.time()

    try:
        image_bytes = await file.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="File gambar kosong.")

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Gagal memproses file gambar: {str(e)}",
        )

    try:
        # Jalankan prediksi dengan input size 640 standar YOLO26
        results = model.predict(image, imgsz=640)
        detections = []

        if results and len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes
            for box in boxes:
                # Koordinat xywh normalisasi 0.0 - 1.0 (sesuai spesifikasi techstack.md)
                x, y, w, h = box.xywhn[0].tolist()
                class_idx = int(box.cls[0].item())
                confidence = float(box.conf[0].item())
                raw_name = model.names.get(class_idx, f"unknown_{class_idx}")
                class_name = CLASS_NAME_MAP.get(str(raw_name).strip().lower(), str(raw_name).lower().replace(" ", "_"))

                detections.append({
                    "class_name": class_name,
                    "confidence": round(confidence, 4),
                    "x": round(x, 4),
                    "y": round(y, 4),
                    "w": round(w, 4),
                    "h": round(h, 4),
                })

        processing_time_ms = int((time.time() - start_time) * 1000)

        return {
            "detections": detections,
            "model_version": "yolo26n-v1",
            "processing_time_ms": processing_time_ms,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Kesalahan internal saat inferensi model: {str(e)}",
        )
