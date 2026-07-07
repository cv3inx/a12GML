#!/bin/bash
set -e

IMAGE="redroid/redroid:12.0.0-gml"
CONTAINER="redroid-gml"
PORT="${1:-5555}"
FRIDA_PORT="${2:-27042}"

# Fallback if final image not built yet
if ! docker image inspect "$IMAGE" &>/dev/null; then
    echo "[!] Final GML image not found. Falling back to ndk_magisk base."
    echo "    Run ./build.sh for full setup."
    IMAGE="redroid/redroid:12.0.0_ndk_magisk"
    if ! docker image inspect "$IMAGE" &>/dev/null; then
        echo "[!] No suitable image found. Run ./build.sh first."
        exit 1
    fi
fi

# Stop existing
docker stop "$CONTAINER" 2>/dev/null || true
docker rm "$CONTAINER" 2>/dev/null || true

echo "[*] Starting Redroid A12 GML (port $PORT)..."
docker run -d --name "$CONTAINER" \
    --privileged \
    -p ${PORT}:5555 \
    "$IMAGE" \
    androidboot.redroid_gpu_mode=guest \
    androidboot.redroid_fps=30 \
    androidboot.hardware=redroid \
    ro.product.cpu.abilist=x86_64,arm64-v8a,x86,armeabi-v7a,armeabi \
    ro.product.cpu.abilist64=x86_64,arm64-v8a \
    ro.product.cpu.abilist32=x86,armeabi-v7a,armeabi \
    ro.dalvik.vm.isa.arm=x86 \
    ro.dalvik.vm.isa.arm64=x86_64 \
    ro.enable.native.bridge.exec=1 \
    ro.dalvik.vm.native.bridge=libndk_translation.so \
    ro.ndk_translation.version=0.2.2 >/dev/null

echo "[*] Waiting for boot (~30s)..."
sleep 30
adb connect localhost:${PORT} >/dev/null 2>&1
adb -s localhost:${PORT} wait-for-device
adb -s localhost:${PORT} root >/dev/null 2>&1
sleep 3

# Start Frida automatically
echo "[*] Starting Frida..."
adb -s localhost:${PORT} shell "pkill -9 fs" 2>/dev/null || true
adb -s localhost:${PORT} shell "/data/local/tmp/fs -D &" 2>/dev/null
sleep 2
adb -s localhost:${PORT} forward tcp:${FRIDA_PORT} tcp:27042 >/dev/null

# Apply random device spoof
echo "[*] Spoofing device identity..."
/opt/a12GML/scripts/spoof_device.sh ${PORT} random 2>/dev/null || true

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  Redroid A12 GML - READY                         ║"
echo "╠══════════════════════════════════════════════════╣"
echo "║  ADB:   localhost:${PORT}                           ║"
echo "║  Frida: 127.0.0.1:${FRIDA_PORT}                       ║"
echo "║  Root:  ✓ (adb root)                             ║"
echo "║  ARM64: ✓ (libndk translation)                   ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "  frida -H 127.0.0.1:${FRIDA_PORT} -f <package>"
echo "  adb -s localhost:${PORT} install app.apk"
