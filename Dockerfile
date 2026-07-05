FROM python:3.11-slim

WORKDIR /app

# Install ffmpeg for audio processing (OGG conversion)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cloud Run always uses PORT env var
ENV PORT=8080
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers 1
