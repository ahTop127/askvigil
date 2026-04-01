FROM python:3.12-slim

# Matches the 'args' in your docker-compose.override.yml
ARG INSTALL_MODE=cpu 

WORKDIR /app

# 1. Install system dependencies and uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    build-essential \
    libpq-dev \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.local/bin:$PATH"

# 2. Copy lockfiles 
COPY uv.lock pyproject.toml ./

# 3. Sync the environment + the specific extra (cpu or gpu)
# uv automatically reads the INSTALL_MODE variable and resolves the correct PyTorch wheels
RUN uv sync --frozen --extra ${INSTALL_MODE}

# 4. Copy app code
COPY . .

# 5. Run the app using the absolute path to the Linux binary
CMD ["/app/.venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]