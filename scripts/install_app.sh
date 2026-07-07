#!/bin/bash
# Install APK(s) with auto-grant all permissions + disable battery optimization
# Usage: ./install_app.sh [port] <apk_path_or_dir>
set -e

PORT="${1:-5555}"
TARGET="${2}"

if [ -z "$TARGET" ]; then
    echo "Usage: $0 [port] <apk_file_or_directory>"
    exit 1
fi

install_apk() {
    local APK="$1"
    local PKG=$(aapt dump badging "$APK" 2>/dev/null | grep "package: name" | sed "s/.*name='//" | sed "s/'.*//")
    
    echo "[*] Installing: $(basename $APK)"
    echo "    Package: $PKG"
    
    adb -s localhost:${PORT} install -r -g "$APK" 2>&1 | grep -v "Performing"
    
    if [ -n "$PKG" ]; then
        # Grant all runtime permissions
        for PERM in $(adb -s localhost:${PORT} shell pm list permissions -g 2>/dev/null | grep "permission:" | sed 's/.*permission://'); do
            adb -s localhost:${PORT} shell pm grant "$PKG" "$PERM" 2>/dev/null || true
        done
        
        # Disable battery optimization
        adb -s localhost:${PORT} shell dumpsys deviceidle whitelist +${PKG} 2>/dev/null || true
        adb -s localhost:${PORT} shell cmd appops set "$PKG" RUN_IN_BACKGROUND allow 2>/dev/null || true
        
        echo "    [✓] Installed + permissions granted"
    fi
}

if [ -d "$TARGET" ]; then
    for APK in "$TARGET"/*.apk; do
        [ -f "$APK" ] && install_apk "$APK"
    done
elif [ -f "$TARGET" ]; then
    install_apk "$TARGET"
else
    echo "[!] Not found: $TARGET"
    exit 1
fi
