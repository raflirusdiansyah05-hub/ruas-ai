FROM python:3.11-slim

WORKDIR /app

# Install dependensi sistem untuk OpenCV & PIL
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render otomatis menginjeksi environment variable $PORT saat startup container
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port $PORT"]
