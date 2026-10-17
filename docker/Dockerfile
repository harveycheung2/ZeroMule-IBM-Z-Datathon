# Multi-arch Dockerfile for ZeroMule
# Compatible with linux/amd64 and linux/s390x (IBM Z / LinuxONE)

FROM --platform=$TARGETPLATFORM python:3.10-slim

# System dependencies for scientific computing, graph processing, and network compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade pip and copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source tree and application
COPY src/ ./src/
COPY app/ ./app/
COPY benchmarks/ ./benchmarks/
COPY docs/ ./docs/
COPY weights/ ./weights/
COPY results/ ./results/

# Expose Streamlit default port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Environment flags for hardware optimization on IBM Z (s390x) and x86
ENV PYTHONUNBUFFERED=1 \
    OMP_NUM_THREADS=4 \
    MKL_NUM_THREADS=4 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false

ENTRYPOINT ["streamlit", "run", "app/dashboard.py"]
