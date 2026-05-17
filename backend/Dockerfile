# Uses multi-stage builds to separate heavy compilation toolchains from the final runtime image.
# Installs 'uv' via pip in Stage 1 to build a locked virtual env, isolating thick OCR/ONNX caches.

# --- STAGE 1: Builder ---
FROM python:3.12-slim AS builder
WORKDIR /app

# Set an explicit path for models
ENV RAPIDOCR_MODEL_PATH=/app/ocr_models

# Added 'apt-get upgrade -y' to clear builder vulnerabilities
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    libgl1 \
    libglib2.0-0 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv
COPY uv.lock pyproject.toml ./
RUN uv sync --frozen --no-install-project

# Pre-warm the OCR engine to bake the model weights directly into the builder layer cache
RUN .venv/bin/python -c "from rapidocr_onnxruntime import RapidOCR; RapidOCR()"

# --- STAGE 2: Runtime ---
FROM python:3.12-slim
WORKDIR /app

# Added 'apt-get upgrade -y' to secure the final runtime environment
# libgl1 and libglib2.0-0 are MANDATORY for OpenCV (RapidOCR dependency)
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    libpq5 \
    ca-certificates \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the lightweight, pre-compiled virtual environment
COPY --from=builder /app/.venv /app/.venv

# Copy code last to maximize layer caching efficiency 
COPY . . 

# Restore the PATH and PYTHONPATH tracking matrices
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:/app/app"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Fire up the engine using the top-level app entry point
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]