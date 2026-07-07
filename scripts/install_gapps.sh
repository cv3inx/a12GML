#!/bin/bash
set -e

PORT="${1:-5555}"
WORKDIR="/opt/a12GML/work/gapps"
mkdir -p "$WORKDIR"

echo "[*] Installing MindTheGapps on port $PORT..."

adb -s localhost:${PORT} root 2>/dev/null
sleep 2

GAPPS_ZIP="$WORKDIR/MindTheGapps-12.zip"

# Download from multiple sources
if [ ! -f "$GAPPS_ZIP" ] || ! file "$GAPPS_ZIP" 2>/dev/null | grep -q "Zip"; then
    echo "[*] Downloading MindTheGapps for Android 12 (x86_64)..."
    URLS=(
        "https://github.com/nicololau/nicololau/releases/download/v0/MindTheGapps-12.0.0-x86_64-20220215_100039.zip"
        "https://sourceforge.net/projects/nicholasgapps/files/MindTheGapps-12.0.0-x86_64-20220215_100039.zip/download"
    )
    for URL in "${URLS[@]}"; do
        echo "  Trying: ${URL:0:60}..."
        curl -sL "$URL" -o "$GAPPS_ZIP" 2>/dev/null
        if file "$GAPPS_ZIP" 2>/dev/null | grep -q "Zip"; then
            echo "  [✓] Downloaded successfully"
            break
        fi
    done
fi

if ! file "$GAPPS_ZIP" 2>/dev/null | grep -q "Zip"; then
    echo ""
    echo "[!] Automatic download failed. Please download manually:"
    echo "    URL: https://wiki.lineageos.org/gapps"
    echo "    File: MindTheGapps-12.0.0-x86_64-*.zip"
    echo "    Save to: $GAPPS_ZIP"
    echo ""
    echo "    Or use LiteGapps: https://litegapps.github.io/"
    exit 1
fi

echo "[*] Extracting..."
rm -rf "$WORKDIR/extracted"
mkdir -p "$WORKDIR/extracted"
unzip -q "$GAPPS_ZIP" -d "$WORKDIR/extracted"

echo "[*] Mounting system as writable..."
adb -s localhost:${PORT} shell "mount -o rw,remount /" 2>/dev/null || true

echo "[*] Pushing GApps..."
if [ -d "$WORKDIR/extracted/system" ]; then
    adb -s localhost:${PORT} push "$WORKDIR/extracted/system/" /system/ 2>/dev/null
    
    # Fix permissions
    adb -s localhost:${PORT} shell "
        find /system/priv-app -type d -exec chmod 755 {} \;
        find /system/priv-app -type f -exec chmod 644 {} \;
        find /system/app -type d -exec chmod 755 {} \;
        find /system/app -type f -exec chmod 644 {} \;
        find /system/product -type d -exec chmod 755 {} \; 2>/dev/null
        find /system/product -type f -exec chmod 644 {} \; 2>/dev/null
        chmod 644 /system/etc/permissions/*.xml 2>/dev/null
        chmod 644 /system/etc/sysconfig/*.xml 2>/dev/null
    " 2>/dev/null
    echo "[✓] GApps pushed"
else
    echo "[!] No system/ directory found in ZIP"
    exit 1
fi

echo "[*] Rebooting..."
adb -s localhost:${PORT} reboot
echo "[*] Waiting for reboot (~40s)..."
sleep 40
adb connect localhost:${PORT} >/dev/null 2>&1
adb -s localhost:${PORT} wait-for-device
adb -s localhost:${PORT} root >/dev/null 2>&1
sleep 5

# Verify
if adb -s localhost:${PORT} shell pm list packages 2>/dev/null | grep -q "com.google.android.gms"; then
    echo ""
    echo "[✓] GApps installed!"
    adb -s localhost:${PORT} shell pm list packages | grep -E "gms|vending|gsf" 
else
    echo "[!] GApps not detected. May need another reboot."
fi
