#!/bin/bash
# Forge Publisher Ops Startup Script
# Usage: ./startup.sh [start|stop|restart]

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
PIPELINE_DIR="$ROOT_DIR/pipeline"
UI_DIR="$ROOT_DIR/ui"
PYTHON="$VENV_DIR/bin/python"
MANAGE="$UI_DIR/manage.py"
REQUIREMENTS=("$ROOT_DIR/requirements.txt" "$PIPELINE_DIR/requirements.txt" "$UI_DIR/requirements.txt")


# Find an open port in a given range
find_open_port() {
    local start_port=$1
    local end_port=$2
    for ((port=start_port; port<=end_port; port++)); do
        if ! lsof -i :$port >/dev/null 2>&1; then
            echo $port
            return
        fi
    done
    echo ""  # No open port found
}

# Dynamically assign ports
UI_PORT_FILE="$ROOT_DIR/ops/ui.port"
PIPELINE_PORT_FILE="$ROOT_DIR/ops/pipeline.port"

PIPELINE_PID_FILE="$ROOT_DIR/ops/pipeline.pid"
UI_PID_FILE="$ROOT_DIR/ops/ui.pid"

get_ui_port() {
    if [ -f "$UI_PORT_FILE" ]; then
        cat "$UI_PORT_FILE"
    else
        local port=$(find_open_port 8000 8100)
        echo $port > "$UI_PORT_FILE"
        echo $port
    fi
}

get_pipeline_port() {
    if [ -f "$PIPELINE_PORT_FILE" ]; then
        cat "$PIPELINE_PORT_FILE"
    else
        # Avoid UI port
        local ui_port=$(get_ui_port)
        for ((port=8000; port<=8100; port++)); do
            if [ "$port" != "$ui_port" ] && ! lsof -i :$port >/dev/null 2>&1; then
                echo $port > "$PIPELINE_PORT_FILE"
                echo $port
                return
            fi
        done
        echo ""  # No open port found
    fi
}

function create_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        echo "[INFO] Creating Python virtual environment..."
        python3 -m venv "$VENV_DIR"
    fi
}

function install_requirements() {
    source "$VENV_DIR/bin/activate"
    for req in "${REQUIREMENTS[@]}"; do
        if [ -f "$req" ]; then
            echo "[INFO] Installing requirements from $req..."
            pip install -r "$req"
        fi
    done
    deactivate
}



function start_pipeline() {
    # The pipeline is not a server - it's called on-demand by the UI when building EPUBs
    # We just verify the pipeline directory and dependencies are ready
    local port=$(get_pipeline_port)
    echo "[INFO] Pipeline ready (called on-demand by UI for EPUB builds)"
    echo "[INFO] Pipeline directory: $PIPELINE_DIR"
    # Test that the pipeline can be imported
    source "$VENV_DIR/bin/activate"
    cd "$PIPELINE_DIR"
    "$PYTHON" -c "from scripts.pipeline import run_pipeline; print('✅ Pipeline module loaded successfully')" 2>&1 || echo "[WARN] Pipeline module load check failed"
    cd "$ROOT_DIR"
    deactivate
}



function start_ui() {
    local port=$(get_ui_port)
    if [ -z "$port" ]; then
        echo "[ERROR] No open port found for UI in 8000-8100."
        exit 1
    fi
    source "$VENV_DIR/bin/activate"
    echo "[INFO] Starting Django UI on port $port..."
    cd "$UI_DIR"
    nohup "$PYTHON" "$MANAGE" runserver 0.0.0.0:$port --noreload </dev/null > "$ROOT_DIR/ops/ui.log" 2>&1 &
    echo $! > "$UI_PID_FILE"
    cd "$ROOT_DIR"
    deactivate
    echo "[INFO] UI running on port $port. Log: $ROOT_DIR/ops/ui.log"
    echo "[INFO] Tailing UI log. Press Ctrl+C to stop viewing logs."
    tail -n 20 -f "$ROOT_DIR/ops/ui.log" &
    sleep 2
}


function stop_pipeline() {
    # Pipeline is not a running service, nothing to stop
    # Just clean up any stale PID files
    if [ -f "$PIPELINE_PID_FILE" ]; then
        rm -f "$PIPELINE_PID_FILE"
        rm -f "$PIPELINE_PORT_FILE"
    fi
    echo "[INFO] Pipeline cleanup done (pipeline runs on-demand, not as a service)"
}


function stop_ui() {
    if [ -f "$UI_PID_FILE" ]; then
        kill $(cat "$UI_PID_FILE") 2>/dev/null && echo "[INFO] Stopped UI." || echo "[WARN] UI not running."
        rm -f "$UI_PID_FILE"
        rm -f "$UI_PORT_FILE"
    fi
}

case "$1" in
    start)
        create_venv
        install_requirements
        echo "==============================="
        echo "🚀 Forge Publisher Startup 🚀"
        echo "==============================="
        start_pipeline
        start_ui
        echo "[INFO] Both services started. Logs are being tailed above."
        echo "[INFO] Access the UI at: http://localhost:$(get_ui_port)/dashboard/"
        ;;
    stop)
        stop_pipeline
        stop_ui
        echo "[INFO] All services stopped."
        ;;
    restart)
        stop_pipeline
        stop_ui
        create_venv
        install_requirements
        echo "==============================="
        echo "🚀 Forge Publisher Restart 🚀"
        echo "==============================="
        start_pipeline
        start_ui
        echo "[INFO] Both services restarted. Logs are being tailed above."
        echo "[INFO] Access the UI at: http://localhost:$(get_ui_port)/dashboard/"
        ;;
    *)
        echo "Usage: $0 [start|stop|restart]"
        exit 1
        ;;
esac
