# FROM python:3.12-slim

# WORKDIR /app

# # 1. Install system dependencies and uv
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     curl \
#     ca-certificates \
#     build-essential \
#     libpq-dev \
#     ffmpeg \
#     && curl -LsSf https://astral.sh/uv/install.sh | sh \
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/*

# ENV PATH="/root/.local/bin:$PATH"

# # 2. Copy lockfiles 
# COPY uv.lock pyproject.toml ./

# # 3. Sync the environment
# RUN uv sync --frozen

# # Cache easy OCR so it doesn't keep redownloading
# RUN /app/.venv/bin/python -c "import easyocr; easyocr.Reader(['en'], gpu=False)"

# # 4. Copy app code
# COPY . .

# # 5. Run the app using the absolute path to the Linux binary
# CMD ["/app/.venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Faster version
# --- STAGE 1: Builder ---
FROM python:3.12-slim AS builder
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv
COPY uv.lock pyproject.toml ./
RUN uv sync --frozen --no-install-project

# Cache EasyOCR models - pinned to a specific path
ENV EASYOCR_MODULE_PATH=/app/.EasyOCR
RUN .venv/bin/python -c "import easyocr; easyocr.Reader(['en'], gpu=False)"

# --- STAGE 2: Runtime ---
FROM python:3.12-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 ca-certificates && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/.EasyOCR /root/.EasyOCR

# 1. Copy code LAST to protect the OCR cache
COPY . . 

# 2. Restore the PATH and PYTHONPATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:/app/app"
ENV EASYOCR_MODULE_PATH=/root/.EasyOCR
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# 3. Use the top-level main.py
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]