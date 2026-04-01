FROM python:3.12-slim

# Create a 'build argument' with a default value of 'cpu'
ARG INSTALL_MODE=cpu

WORKDIR /app

# 1. Install system-level dependencies + curl, then run the official uv installer
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    build-essential \
    libpq-dev \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 2. Add uv to the PATH (The installer puts it in /root/.local/bin)
ENV PATH="/root/.local/bin:$PATH"

# Conditional installation logic
RUN if [ "$INSTALL_MODE" = "gpu" ]; then \
        pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121; \
    else \
        pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu; \
    fi

# 3. Copy the lockfile and the requirements
COPY uv.lock pyproject.toml ./

# 4. Install dependencies using uv (Much faster than pip)
# --system tells uv to install into the global site-packages
RUN uv pip install --system --no-cache -r pyproject.toml

# 5. Copy the rest of the application code
COPY . .

# 6. Run the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]