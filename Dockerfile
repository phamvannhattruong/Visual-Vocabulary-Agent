FROM python:3.12-slim-bookworm AS vision-export

WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir "ultralytics==8.4.155" "onnx>=1.16,<2"
COPY backend/resources/models/yolo11n.pt backend/resources/models/
COPY training/scripts/export_yolo_onnx.py training/scripts/
RUN python training/scripts/export_yolo_onnx.py

FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=vision-export /app/backend/resources/models/yolo11n.onnx backend/resources/models/

ENV PORT=7860
EXPOSE 7860

CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
