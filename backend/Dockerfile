# Uses multi-stage builds to separate heavy compilation toolchains from the final runtime image.
# Installs 'uv' via pip in Stage 1 to build a locked virtual env, isolating thick OCR/ONNX caches.
# --- STAGE 1: Builder ---
FROM python:3.12-slim AS builder
WORKDIR /app

# Set an explicit path for models
ENV RAPIDOCR_MODEL_PATH=/app/ocr_models

# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential libpq-dev curl && apt-get clean && rm -rf /var/lib/apt/lists/*
# Add libgl1 and libglib2.0-0 here so the warm-up command can run
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    libgl1 \
    libglib2.0-0 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv
COPY uv.lock pyproject.toml ./
RUN uv sync --frozen --no-install-project

# EasyOCR lines removed, go to git if we need them back
# RUN .venv/bin/python -c "from rapidocr_onnxruntime import RapidOCR; RapidOCR()"
RUN .venv/bin/python -c "from rapidocr_onnxruntime import RapidOCR; RapidOCR()" && \
    mkdir -p /root/.rapidocr_models && \
    ls -la /root/.rapidocr_models || echo "Models might be elsewhere"

# --- STAGE 2: Runtime ---
FROM python:3.12-slim
WORKDIR /app

# RUN apt-get update && apt-get install -y --no-install-recommends \
#     libpq5 ca-certificates && apt-get clean && rm -rf /var/lib/apt/lists/*

# libgl1 and libglib2.0-0 are MANDATORY for OpenCV (RapidOCR dependency)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    ca-certificates \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv /app/.venv

# Transfer the cached models so they don't download
COPY --from=builder /root/.rapidocr_models /root/.rapidocr_models

# 1. Copy code LAST to protect the OCR cache
COPY . . 

# 2. Restore the PATH and PYTHONPATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:/app/app"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# 3. Use the top-level main.py
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]