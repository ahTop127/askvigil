FROM python:3.12-slim

WORKDIR /app

# 1. Install curl to fetch uv, then clean up to keep the image slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 2. Download and install uv globally inside this container
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

# 3. Copy the script last to maximize Docker build caching
COPY main.py .

ENV PYTHONUNBUFFERED=1

# 4. uv run will automatically parse the script metadata, handle dependencies, and stay running
CMD ["uv", "run", "main.py"]