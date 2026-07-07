#!/bin/bash
set -e

PORT="${1:-5555}"
PROXY_PORT="${2:-8080}"

echo "[*] Setting up mitmproxy (port $PORT)..."

adb -s localhost:${PORT} root 2>/dev/null; sleep 2

# Generate CA if needed
if [ ! -f /root/.mitmproxy/mitmproxy-ca-cert.cer ]; then
    echo "[*] Generating mitmproxy CA..."
    timeout 5 mitmdump >/dev/null 2>&1 || true
fi

CERT="/root/.mitmproxy/mitmproxy-ca-cert.cer"
if [ ! -f "$CERT" ]; then
    echo "[!] mitmproxy CA not found. Install mitmproxy first: pip install mitmproxy"
    exit 1
fi

HASH=$(openssl x509 -inform PEM -subject_hash_old -in "$CERT" | head -1)
echo "[*] CA hash: $HASH"

adb -s localhost:${PORT} shell "mount -o rw,remount /" 2>/dev/null || true
cp "$CERT" "/tmp/${HASH}.0"
adb -s localhost:${PORT} push "/tmp/${HASH}.0" "/system/etc/security/cacerts/${HASH}.0"
adb -s localhost:${PORT} shell "chmod 644 /system/etc/security/cacerts/${HASH}.0"
rm "/tmp/${HASH}.0"

# Detect gateway IP
GATEWAY=$(adb -s localhost:${PORT} shell "ip route | grep default | awk '{print \$3}'" 2>/dev/null | tr -d '\r')
[ -z "$GATEWAY" ] && GATEWAY="172.20.0.1"

echo "[*] Setting proxy: ${GATEWAY}:${PROXY_PORT}"
adb -s localhost:${PORT} shell "settings put global http_proxy ${GATEWAY}:${PROXY_PORT}"

echo ""
echo "[✓] MITM ready!"
echo "    Start proxy: mitmdump --set block_global=false"
echo "    Disable:     adb -s localhost:${PORT} shell settings put global http_proxy :0"
