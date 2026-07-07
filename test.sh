#!/bin/bash
PORT="${1:-5555}"
FRIDA_PORT="${2:-27042}"
PASS=0; FAIL=0

echo "╔══════════════════════════════════════════╗"
echo "║  Redroid A12 GML - Verification          ║"
echo "╚══════════════════════════════════════════╝"
echo ""

check() { if [ $1 -eq 0 ]; then echo "  [✓] $2"; PASS=$((PASS+1)); else echo "  [✗] $2"; FAIL=$((FAIL+1)); fi; }

adb -s localhost:${PORT} shell "echo ok" >/dev/null 2>&1; check $? "ADB connected"
adb -s localhost:${PORT} shell "id" 2>/dev/null | grep -q "uid=0"; check $? "Root access"
VER=$(adb -s localhost:${PORT} shell getprop ro.build.version.release 2>/dev/null | tr -d '\r')
[ "$VER" = "12" ]; check $? "Android 12 (got: $VER)"
adb -s localhost:${PORT} shell getprop ro.product.cpu.abilist 2>/dev/null | grep -q "arm64-v8a"; check $? "ARM64 translation ABI"
adb -s localhost:${PORT} shell "ls /system/lib64/libndk_translation.so" >/dev/null 2>&1; check $? "libndk present"
adb -s localhost:${PORT} shell getprop ro.enable.native.bridge.exec 2>/dev/null | grep -q "1"; check $? "Native bridge enabled"
adb -s localhost:${PORT} shell "ls /data/adb/magisk/busybox" >/dev/null 2>&1; check $? "Magisk installed"
adb -s localhost:${PORT} shell pm list packages 2>/dev/null | grep -q "com.android.vending"; check $? "Play Store"
adb -s localhost:${PORT} shell pm list packages 2>/dev/null | grep -q "com.google.android.gms"; check $? "Google Play Services"
adb -s localhost:${PORT} shell "ls /system/etc/security/cacerts/c8750f0d.0" >/dev/null 2>&1; check $? "mitmproxy CA cert"

# Frida
TESTPID=$(adb -s localhost:${PORT} shell pidof com.android.systemui 2>/dev/null | tr -d '\r')
if [ -n "$TESTPID" ] && command -v frida &>/dev/null; then
    timeout 10 frida -H 127.0.0.1:${FRIDA_PORT} -p $TESTPID -e 'console.log("OK")' 2>&1 | grep -q "OK"; check $? "Frida works"
else
    echo "  [?] Frida - skipped (no PID or frida not installed)"; FAIL=$((FAIL+1))
fi

# Device spoof check
MODEL=$(adb -s localhost:${PORT} shell getprop ro.product.model 2>/dev/null | tr -d '\r')
IMEI=$(adb -s localhost:${PORT} shell getprop persist.radio.imei 2>/dev/null | tr -d '\r')
[ -n "$MODEL" ] && [ "$MODEL" != "redroid" ]; check $? "Device spoofed (model: $MODEL)"
[ -n "$IMEI" ] && [ ${#IMEI} -eq 15 ]; check $? "IMEI set (${IMEI:-none})"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
printf "  Results: %d passed, %d failed\n" $PASS $FAIL
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
