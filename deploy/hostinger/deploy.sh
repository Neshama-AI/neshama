#!/bin/bash
# Neshama Cloud API - Deployment Script for Shared Hosting
# Run this script on the server after uploading the deployment package

set -e

INSTALL_DIR="$HOME/neshama-cloud"
VENV_DIR="$INSTALL_DIR/venv"
LOG_FILE="$INSTALL_DIR/server.log"
PID_FILE="$INSTALL_DIR/server.pid"

echo "=== Neshama Cloud API Deployment ==="
echo "Install dir: $INSTALL_DIR"

# 1. Create install directory
mkdir -p "$INSTALL_DIR"

# 2. Create virtual environment (without pip, then bootstrap pip)
echo "[1/6] Creating virtual environment..."
python3 -m venv --without-pip "$VENV_DIR" 2>/dev/null || {
    echo "venv creation failed, trying alternative..."
    # Alternative: just use a local directory structure
    mkdir -p "$VENV_DIR/bin" "$VENV_DIR/lib"
    cp "$(which python3)" "$VENV_DIR/bin/python3" 2>/dev/null || true
    ln -sf "$(which python3)" "$VENV_DIR/bin/python" 2>/dev/null || true
}

# 3. Bootstrap pip into the virtual environment
echo "[2/6] Installing pip..."
"$VENV_DIR/bin/python3" -m ensurepip --upgrade 2>/dev/null || {
    echo "ensurepip failed, trying get-pip.py..."
    curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
    "$VENV_DIR/bin/python3" /tmp/get-pip.py 2>/dev/null || {
        echo "get-pip.py failed, using system pip..."
        # Fallback: install to user site-packages
        python3 -m pip install --user --upgrade pip 2>/dev/null || true
    }
}

# 4. Install dependencies
echo "[3/6] Installing dependencies..."
if [ -f "$VENV_DIR/bin/pip" ]; then
    "$VENV_DIR/bin/pip" install --no-cache-dir -r "$INSTALL_DIR/requirements.txt" 2>&1
    PYTHON_CMD="$VENV_DIR/bin/python3"
else
    # Fallback to user install
    python3 -m pip install --user --no-cache-dir -r "$INSTALL_DIR/requirements.txt" 2>&1
    PYTHON_CMD="python3"
fi

# 5. Load environment variables
echo "[4/6] Loading environment..."
if [ -f "$INSTALL_DIR/.env" ]; then
    set -a
    source "$INSTALL_DIR/.env"
    set +a
    echo "Environment loaded from .env"
else
    echo "WARNING: No .env file found!"
fi

# 6. Stop existing server if running
echo "[5/6] Stopping existing server..."
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "Stopping old server (PID: $OLD_PID)..."
        kill "$OLD_PID" 2>/dev/null || true
        sleep 2
        kill -9 "$OLD_PID" 2>/dev/null || true
    fi
    rm -f "$PID_FILE"
fi

# 7. Start server
echo "[6/6] Starting server..."
cd "$INSTALL_DIR"
nohup $PYTHON_CMD "$INSTALL_DIR/cloud_server.py" >> "$LOG_FILE" 2>&1 &
SERVER_PID=$!
echo "$SERVER_PID" > "$PID_FILE"
echo "Server started with PID: $SERVER_PID"

# 8. Wait and verify
echo "Waiting for server to start..."
sleep 5

# Check if process is still running
if kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "✓ Server process is running (PID: $SERVER_PID)"
else
    echo "✗ Server process died! Check logs:"
    tail -20 "$LOG_FILE"
    exit 1
fi

# Try health check
HEALTH_CHECK=$(curl -s http://localhost:${NESHAMA_PORT:-8420}/health 2>/dev/null || echo "FAILED")
if echo "$HEALTH_CHECK" | grep -q "ok"; then
    echo "✓ Health check passed: $HEALTH_CHECK"
else
    echo "⚠ Health check returned: $HEALTH_CHECK"
    echo "  Server may still be starting up. Check logs:"
    tail -10 "$LOG_FILE"
fi

echo ""
echo "=== Deployment Complete ==="
echo "API URL: http://$(hostname -I 2>/dev/null | awk '{print $1}' || echo 'localhost'):${NESHAMA_PORT:-8420}"
echo "Health:  http://localhost:${NESHAMA_PORT:-8420}/health"
echo "Docs:    http://localhost:${NESHAMA_PORT:-8420}/docs"
echo "Logs:    tail -f $LOG_FILE"
echo "Stop:    kill \$(cat $PID_FILE)"
echo "Restart: bash $INSTALL_DIR/deploy.sh"
