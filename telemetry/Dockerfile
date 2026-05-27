FROM python:3.12-slim

WORKDIR /app

# 1. Install system utilities and clean layer cache immediately
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 2. Install uv globally and expose binary pathway
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

# 3. Copy project definition manifests from the backend directory
# Relative to the root context (.) defined in docker-compose
COPY backend/pyproject.toml backend/uv.lock ./

# 4. Synchronize production dependencies via uv package manager
RUN uv sync --frozen --no-dev

# 5. Inject application logic from the telemetry folder into workspace root
COPY telemetry/app.py ./

ENV PYTHONUNBUFFERED=1

# Expose the default Streamlit network interface port
EXPOSE 8501

# 6. Execute Streamlit through the localized uv environment wrapper
# Append the base path flag to prevent static asset breakdown (404s) on the UI
CMD ["uv", "run", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.baseUrlPath=/telemetry"]