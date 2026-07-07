#!/bin/bash
# Rotate device identity at regular intervals
# Usage: ./rotate_identity.sh [port] [interval_seconds]
#        Default: rotate every 3600s (1 hour)

PORT="${1:-5555}"
INTERVAL="${2:-3600}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "[*] Identity rotation daemon started"
echo "    Port: $PORT | Interval: ${INTERVAL}s"
echo "    Press Ctrl+C to stop"
echo ""

while true; do
    "$SCRIPT_DIR/spoof_device.sh" "$PORT" random
    echo "    Next rotation in ${INTERVAL}s..."
    echo ""
    sleep "$INTERVAL"
done
