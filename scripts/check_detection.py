#!/usr/bin/env python3
"""Check and auto-fix emulator/root detection artifacts"""
import subprocess, sys

port = sys.argv[1] if len(sys.argv) > 1 else "5555"
ADB = f"adb -s localhost:{port}"
passed = failed = fixed = 0

def shell(cmd):
    return subprocess.run(f"{ADB} shell \"{cmd}\"", shell=True, capture_output=True, text=True, timeout=10).stdout.strip()

def check(desc, cmd, bad_val=None, fix_cmd=None):
    global passed, failed, fixed
    out = shell(cmd)
    is_bad = (bad_val in out) if bad_val else (out == "" or "not found" in out.lower())
    if not is_bad:
        print(f"  [✓] {desc}"); passed += 1
    elif fix_cmd:
        shell(fix_cmd); print(f"  [~] {desc} (fixed)"); fixed += 1
    else:
        print(f"  [✗] {desc}"); failed += 1

print("╔══════════════════════════════════════════╗")
print("║  Detection Check & Auto-Fix              ║")
print("╚══════════════════════════════════════════╝\n")

print("=== Build Props ===")
check("ro.build.tags = release-keys", "getprop ro.build.tags", "test-keys", "/sbin/magisk resetprop ro.build.tags release-keys")
check("ro.build.type = user", "getprop ro.build.type", "userdebug", "/sbin/magisk resetprop ro.build.type user")
check("ro.hardware != redroid", "getprop ro.hardware", "redroid", "/sbin/magisk resetprop ro.hardware qcom")
check("ro.product.model != redroid", "getprop ro.product.model", "redroid")
check("ro.kernel.qemu != 1", "getprop ro.kernel.qemu", "1", "/sbin/magisk resetprop ro.kernel.qemu 0")

print("\n=== Root Artifacts ===")
check("No /system/bin/su visible", "ls /system/bin/su 2>/dev/null", "su")
check("Magisk pkg hidden from pm", "pm list packages | grep topjohnwu.magisk", "magisk")

print("\n=== Frida Artifacts ===")
check("No frida in process list", "ps -A | grep -E 'frida|fs' | grep -v grep", "frida")

print(f"\n{'━'*42}")
print(f"  Results: {passed} clean, {fixed} fixed, {failed} exposed")
print(f"{'━'*42}")
