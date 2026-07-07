#!/bin/bash
set -e

echo "╔══════════════════════════════════════════════════╗"
echo "║  Redroid A12 GML Builder                         ║"
echo "║  Android 12 + GApps + Magisk + Libndk + Frida   ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

WORKDIR="/opt/a12GML/work"
SCRIPTS="/opt/a12GML/scripts"
FINAL_IMAGE="redroid/redroid:12.0.0-gml"
BASE_IMAGE="redroid/redroid:12.0.0-latest"
CONTAINER_NAME="redroid-gml-build"
BUILD_PORT=5558

mkdir -p "$WORKDIR"/{gapps,frida,magisk,ndk}

# ============================================================
# Step 1: Pull base image
# ============================================================
echo "[1/7] Pulling base image..."
docker pull "$BASE_IMAGE" 2>&1 | grep -E "Pull|Digest|Status" || true
echo "[✓] Base image ready"

# ============================================================
# Step 2: Download components
# ============================================================
echo ""
echo "[2/7] Downloading components..."

# Frida server
FRIDA_VER="17.15.3"
if [ ! -f "$WORKDIR/frida/frida-server" ]; then
    echo "  [*] Downloading frida-server $FRIDA_VER..."
    curl -sL "https://github.com/frida/frida/releases/download/$FRIDA_VER/frida-server-$FRIDA_VER-android-x86_64.xz" \
        -o "$WORKDIR/frida/frida-server.xz"
    xz -d "$WORKDIR/frida/frida-server.xz"
    chmod 755 "$WORKDIR/frida/frida-server"
    echo "  [✓] frida-server"
else
    echo "  [✓] frida-server (cached)"
fi

# MindTheGapps - try multiple mirrors
GAPPS_ZIP="$WORKDIR/gapps/MindTheGapps-12.zip"
if [ ! -f "$GAPPS_ZIP" ] || ! file "$GAPPS_ZIP" 2>/dev/null | grep -q "Zip"; then
    echo "  [*] Downloading MindTheGapps..."
    for URL in \
        "https://github.com/nicololau/nicololau/releases/download/v0/MindTheGapps-12.0.0-x86_64-20220215_100039.zip" \
        "https://dl.google.com/dl/android/aosp/MindTheGapps-12.0.0-x86_64.zip" \
        "https://objects.githubusercontent.com/github-production-release-asset/MindTheGapps-12.0.0-x86_64-20220215_100039.zip"; do
        curl -sL "$URL" -o "$GAPPS_ZIP" 2>/dev/null
        if file "$GAPPS_ZIP" 2>/dev/null | grep -q "Zip"; then
            echo "  [✓] MindTheGapps downloaded"
            break
        fi
    done
    if ! file "$GAPPS_ZIP" 2>/dev/null | grep -q "Zip"; then
        echo "  [!] Auto-download failed."
        echo "      Please manually download MindTheGapps-12.0.0-x86_64 and place at:"
        echo "      $GAPPS_ZIP"
        echo "      Download from: https://wiki.lineageos.org/gapps"
        echo ""
        echo "      Continuing without GApps (install later with ./scripts/install_gapps.sh)"
        SKIP_GAPPS=1
    fi
else
    echo "  [✓] MindTheGapps (cached)"
fi

# ============================================================
# Step 3: Build NDK + Magisk layer using redroid-script
# ============================================================
echo ""
echo "[3/7] Building NDK + Magisk layer..."
if docker image inspect "redroid/redroid:12.0.0_ndk_magisk" &>/dev/null; then
    echo "  [✓] ndk_magisk layer exists (cached)"
    BASE_IMAGE="redroid/redroid:12.0.0_ndk_magisk"
else
    if [ -d "/opt/redroid-script" ]; then
        echo "  [*] Building via redroid-script..."
        cd /opt/redroid-script
        python3 redroid.py -a 12.0.0 -m -n
        BASE_IMAGE="redroid/redroid:12.0.0_ndk_magisk"
        cd /opt/a12GML
        echo "  [✓] ndk + magisk built"
    else
        echo "  [!] redroid-script not found at /opt/redroid-script"
        echo "      Install: curl -sL https://codeload.github.com/ayasa520/redroid-script/zip/refs/heads/main -o /tmp/rs.zip && unzip /tmp/rs.zip -d /opt/ && mv /opt/redroid-script-main /opt/redroid-script"
        exit 1
    fi
fi

# ============================================================
# Step 4: Start temp container and install GApps + Frida
# ============================================================
echo ""
echo "[4/7] Starting build container..."
docker stop "$CONTAINER_NAME" 2>/dev/null; docker rm "$CONTAINER_NAME" 2>/dev/null

docker run -d --name "$CONTAINER_NAME" --privileged -p ${BUILD_PORT}:5555 "$BASE_IMAGE" \
    androidboot.redroid_gpu_mode=guest \
    ro.product.cpu.abilist=x86_64,arm64-v8a,x86,armeabi-v7a,armeabi \
    ro.product.cpu.abilist64=x86_64,arm64-v8a \
    ro.product.cpu.abilist32=x86,armeabi-v7a,armeabi \
    ro.dalvik.vm.isa.arm=x86 \
    ro.dalvik.vm.isa.arm64=x86_64 \
    ro.enable.native.bridge.exec=1 \
    ro.dalvik.vm.native.bridge=libndk_translation.so >/dev/null

echo "  [*] Waiting for boot..."
sleep 35
adb connect localhost:${BUILD_PORT} >/dev/null 2>&1
adb -s localhost:${BUILD_PORT} wait-for-device
adb -s localhost:${BUILD_PORT} root >/dev/null 2>&1
sleep 3

# ============================================================
# Step 5: Install GApps
# ============================================================
echo ""
echo "[5/7] Installing GApps..."
if [ -z "$SKIP_GAPPS" ] && file "$GAPPS_ZIP" 2>/dev/null | grep -q "Zip"; then
    rm -rf "$WORKDIR/gapps/extracted"
    mkdir -p "$WORKDIR/gapps/extracted"
    unzip -q "$GAPPS_ZIP" -d "$WORKDIR/gapps/extracted"
    
    adb -s localhost:${BUILD_PORT} shell "mount -o rw,remount /" 2>/dev/null || true
    
    if [ -d "$WORKDIR/gapps/extracted/system" ]; then
        adb -s localhost:${BUILD_PORT} push "$WORKDIR/gapps/extracted/system/" /system/ 2>/dev/null
        echo "  [✓] GApps pushed to /system"
    fi
else
    echo "  [!] Skipped (ZIP not available)"
fi

# ============================================================
# Step 6: Install Frida + configure system
# ============================================================
echo ""
echo "[6/7] Installing Frida + system config..."

adb -s localhost:${BUILD_PORT} shell "mount -o rw,remount /" 2>/dev/null || true

# Push frida-server (renamed to avoid detection)
adb -s localhost:${BUILD_PORT} push "$WORKDIR/frida/frida-server" /data/local/tmp/fs >/dev/null
adb -s localhost:${BUILD_PORT} shell "chmod 755 /data/local/tmp/fs"
echo "  [✓] Frida server installed at /data/local/tmp/fs"

# Set timezone
adb -s localhost:${BUILD_PORT} shell "setprop persist.sys.timezone Asia/Jakarta" 2>/dev/null || true

# Disable proxy by default
adb -s localhost:${BUILD_PORT} shell "settings put global http_proxy :0" 2>/dev/null || true

echo "  [✓] System configured"

# ============================================================
# Step 7: Commit final image
# ============================================================
echo ""
echo "[7/7] Committing final image..."
docker stop "$CONTAINER_NAME" >/dev/null 2>&1
docker commit "$CONTAINER_NAME" "$FINAL_IMAGE" >/dev/null 2>&1
docker rm "$CONTAINER_NAME" >/dev/null 2>&1

# Cleanup port
adb disconnect localhost:${BUILD_PORT} 2>/dev/null || true

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  Build complete!                                 ║"
echo "║  Image: $FINAL_IMAGE               ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "  Start:  ./run.sh"
echo "  Test:   ./test.sh"
echo "  Spoof:  ./scripts/spoof_device.sh"
