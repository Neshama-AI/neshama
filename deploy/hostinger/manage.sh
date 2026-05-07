#!/bin/bash
# Start/stop script for Neshama Cloud API
# Usage: ./manage.sh [start|stop|restart|status|logs]

INSTALL_DIR="$HOME/neshama-cloud"
PID_FILE="$INSTALL_DIR/server.pid"
LOG_FILE="$INSTALL_DIR/server.log"
PORT=${NESHAMA_PORT:-8420}

# Load env
if [ -f "$INSTALL_DIR/.env" ]; then
    set -a
    source "$INSTALL_DIR/.env"
    set +a
    PORT=${NESHAMA_PORT:-8420}
fi

get_pid() {
    if [ -f "$PID_FILE" ]; then
        cat "$PID_FILE"
    fi
}

is_running() {
    local pid=$(get_pid)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        return 0
    fi
    return 1
}

case "${1:-status}" in
    start)
        if is_running; then
            echo "Server already running (PID: $(get_pid))"
        else
            echo "Starting Neshama Cloud API..."
            cd "$INSTALL_DIR"
            if [ -f "$INSTALL_DIR/venv/bin/python3" ]; then
                PYTHON="$INSTALL_DIR/venv/bin/python3"
            else
                PYTHON="python3"
            fi
            nohup $PYTHON "$INSTALL_DIR/cloud_server.py" >> "$LOG_FILE" 2>&1 &
            echo $! > "$PID_FILE"
            echo "Started with PID: $(get_pid)"
            sleep 3
            if is_running; then
                echo "✓ Server is running"
            else
                echo "✗ Server failed to start. Check logs:"
                tail -20 "$LOG_FILE"
            fi
        fi
        ;;
    stop)
        if is_running; then
            echo "Stopping server (PID: $(get_pid))..."
            kill $(get_pid)
            sleep 2
            if is_running; then
                kill -9 $(get_pid)
            fi
            rm -f "$PID_FILE"
            echo "Stopped"
        else
            echo "Server not running"
        fi
        ;;
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    status)
        if is_running; then
            echo "✓ Server running (PID: $(get_pid))"
            HEALTH=$(curl -s http://localhost:$PORT/health 2>/dev/null || echo "unreachable")
            echo "  Health: $HEALTH"
        else
            echo "✗ Server not running"
        fi
        ;;
    logs)
        tail -f "$LOG_FILE"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        ;;
esac
