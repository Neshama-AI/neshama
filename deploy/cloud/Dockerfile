FROM python:3.11-slim

LABEL maintainer="Neshama AI <team@neshama.ai>"
LABEL description="Neshama Soul OS - Cloud Backend API"

WORKDIR /app

# Install system dependencies (Aliyun mirror for China servers)
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list 2>/dev/null || true && \
    apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md ./
COPY neshama/ neshama/
COPY configs/ configs/

# Install neshama with web dependencies (Tsinghua pip mirror for China servers)
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -e ".[web]"

# Create data directories
RUN mkdir -p /app/data /app/billing_data

# Expose API port
EXPOSE 8420

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=15s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8420/health')" || exit 1

# Run the server
CMD ["uvicorn", "neshama.web.server:create_app", "--factory", "--host", "0.0.0.0", "--port", "8420", "--workers", "2"]
