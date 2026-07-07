#!/bin/bash
# Check for detectable emulator/root artifacts and fix them
set -e

PORT="${1:-5555}"
PASS=0; FAIL=0; FIXED=0

echo "╔══════════════════════════════════════════╗"
echo "║  Detection Check & Auto-Fix              ║"
echo "╚══════════════════════════════════════════╝"
echo ""

check_fix() {
    local desc="$1" check="$2" fix="$3"
    if eval "$check" 2>/dev/null; then
        echo "  [✓] $desc"
        PASS=$((PASS+1))
    else
        if [ -n "$fix" ]; then
            eval "$fix" 2>/dev/null
            FIXED=$((FIXED+1))
            echo "  [~] $desc (auto-fixed)"
        else
            echo "  [✗] $desc"
            FAIL=$((FAIL+1))
        fi
    fi
}

S="adb -s localhost:${PORT} shell"

echo "=== Build Props ==="
check_fix "ro.build.tags = release-keys" \
    "[ \"\$($S getprop ro.build.tags)\" = 'release-keys' ]" \
    "$S setprop ro.build.tags release-keys"

check_fix "ro.build.type = user" \
    "[ \"\$($S getprop ro.build.type)\" = 'user' ]" \
    "$S setprop ro.build.type user"

check_fix "ro.hardware != redroid/goldfish" \
    "! echo \$($S getprop ro.hardware) | grep -qE 'redroid|goldfish|ranchu'" \
    "$S setprop ro.hardware qcom"

check_fix "ro.product.model != redroid/sdk" \
    "! echo \$($S getprop ro.product.model) | grep -qiE 'redroid|sdk|emulator'" \
    ""

check_fix "ro.kernel.qemu = 0 or empty" \
    "[ \"\$($S getprop ro.kernel.qemu)\" != '1' ]" \
    "$S setprop ro.kernel.qemu 0"

check_fix "ro.boot.qemu = 0 or empty" \
    "[ \"\$($S getprop ro.boot.qemu)\" != '1' ]" \
    "$S setprop ro.boot.qemu 0"

echo ""
echo "=== File Artifacts ==="
check_fix "No /dev/qemu_pipe" \
    "! $S ls /dev/qemu_pipe" ""

check_fix "No /dev/goldfish_pipe" \
    "! $S ls /dev/goldfish_pipe" ""

check_fix "No /system/bin/qemu-props" \
    "! $S ls /system/bin/qemu-props" ""

echo ""
echo "=== Root Artifacts ==="
check_fix "No /system/bin/su" \
    "! $S ls /system/bin/su" ""

check_fix "No /system/xbin/su" \
    "! $S ls /system/xbin/su" ""

check_fix "Magisk pkg hidden" \
    "! $S pm list packages 2>/dev/null | grep -q 'topjohnwu.magisk'" ""

echo ""
echo "=== Frida Artifacts ==="
check_fix "No frida-server in process list" \
    "! $S ps -A 2>/dev/null | grep -qE 'frida-server|frida'" ""

check_fix "Port 27042 not in /proc/net/tcp" \
    "! $S cat /proc/net/tcp 2>/dev/null | grep -qi '69B2'" ""

echo ""
echo "=== Network ==="
check_fix "No 10.0.2.x IP (emulator gateway)" \
    "! $S ip addr 2>/dev/null | grep -q '10.0.2'" ""

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
printf "  Results: %d clean, %d fixed, %d exposed\n" $PASS $FIXED $FAIL
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
[ $FAIL -gt 0 ] && echo "  [!] Use Frida universal_bypass.js to hide remaining artifacts at runtime"
