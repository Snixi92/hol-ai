# Dockerfile multi-plateforme optimisé Hugging Face Spaces (UID 1000) & Cloud
FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860

WORKDIR /app

# Dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Création de l'utilisateur non-root (obligatoire sur Hugging Face Spaces)
RUN useradd -m -u 1000 user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Installation des dépendances Python
COPY services/core-engine/requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir qrcode pillow

# Copie de l'intégralité du projet
COPY --chown=user:user . /app

# Création et attribution des droits pour la persistance SQLite
RUN mkdir -p /app/services/core-engine/data && chown -R user:user /app

USER user

WORKDIR /app/services/core-engine

EXPOSE 7860

# Démarrage sur le port 7860 (Hugging Face) ou variable dynamique $PORT
CMD ["sh", "-c", "uvicorn src.api.server:app --host 0.0.0.0 --port ${PORT:-7860}"]
