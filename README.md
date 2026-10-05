# RUAS AI Service — YOLO26 Microservice

Microservice inferensi model deteksi kerusakan jalan RUAS berbasis **FastAPI** dan **YOLO26** (`yolo26n.pt`).
Dirancang untuk dideploy ke **Render Web Service** menggunakan runtime Docker.

## Struktur Repository

```
ruas-ai/
├── app.py             # Entrypoint FastAPI, CORS, GET /, POST /deteksi
├── yolo26n.pt         # Model bobot resmi YOLO26
├── requirements.txt   # Dependensi Python
├── Dockerfile         # Dockerfile resmi Render ($PORT dinamis)
├── .dockerignore      # Filter file build Docker
└── README.md          # Dokumentasi deployment
```

## Endpoint

- `GET /` — Health check status service dan kesiapan model.
- `POST /deteksi` — Menerima file gambar (`multipart/form-data`) dan mengembalikan bounding box serta kelas kerusakan jalan (lubang, retak_buaya, retak_melintang, retak_memanjang).

## Langkah Deploy ke Render (User Manual Action)

1. Buat repository baru di GitHub (misal: `ruas-ai`).
2. Masukkan seluruh isi folder ini (`ruas-ai/*`) ke repository GitHub tersebut lalu push.
3. Buka Dashboard [Render](https://dashboard.render.com).
4. Klik **New** → **Web Service**.
5. Hubungkan (Connect) repository GitHub `ruas-ai`.
6. Pengaturan Service:
   - **Name:** `ruas-ai`
   - **Environment:** `Docker` (Render otomatis mendeteksi `Dockerfile`)
   - **Region:** Singapore / terdekat
   - **Instance Type:** Free (512MB RAM)
7. Klik **Deploy Web Service**.
8. Setelah status **Live**, uji endpoint:
   - `https://<nama-service>.onrender.com/` (harus mengembalikan `{"status": "ok", ...}`)
9. Salin URL publik tersebut ke konfigurasi Vercel:
   - `AI_PROVIDER=remote`
   - `AI_REMOTE_ENDPOINT=https://<nama-service>.onrender.com`
