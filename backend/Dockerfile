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
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install exact system deps from df1
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates build-essential libpq-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY uv.lock pyproject.toml ./
RUN uv sync --frozen --no-install-project

# Pre-cache EasyOCR models
RUN /app/.venv/bin/python -c "import easyocr; easyocr.Reader(['en'], gpu=False)"

# --- STAGE 2: Runtime ---
FROM python:3.12-slim
WORKDIR /app

# Keep runtime deps identical to df1 to ensure C-extensions load
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates build-essential libpq-dev ffmpeg \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /root/.EasyOCR /root/.EasyOCR

# --- THE FILE STRUCTURE ---
# Mimic df1's "COPY . ."
# This puts the 'app' folder at /app/app
COPY . . 

# --- ENVIRONMENT ---
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
# Since df1 needed the hack, we hardcode it here for safety, 
# or keep it in your docker-compose.
ENV PYTHONPATH="/app/app"

EXPOSE 8000

# Use the absolute path logic from df1
CMD ["/app/.venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]