FROM python:3.10-slim

# Create a 'build argument' with a default value of 'cpu'
ARG INSTALL_MODE=cpu

WORKDIR /app

# 1. Install system-level dependencies for Postgres and building Python extensions
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Conditional installation logic
RUN if [ "$INSTALL_MODE" = "gpu" ]; then \
        pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121; \
    else \
        pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu; \
    fi

# 2. Copy only requirements first
COPY requirements.txt .
    
# 3. Install heavy AI/Data libraries (This layer is cached)
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the rest of the application code
COPY . .

# 5. Run the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]