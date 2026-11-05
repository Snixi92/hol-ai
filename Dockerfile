FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/services/core-engine \
    PORT=10000

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY services/core-engine/requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir qrcode pillow

COPY . /app

RUN mkdir -p /app/services/core-engine/data && chmod -R 777 /app

WORKDIR /app/services/core-engine

EXPOSE 10000 8000 7860

CMD ["python", "main.py"]
