#!/usr/bin/env python3
"""Verify all Redroid GML components"""
import subprocess, sys

port = sys.argv[1] if len(sys.argv) > 1 else "5555"
frida_port = sys.argv[2] if len(sys.argv) > 2 else "27042"
ADB = f"adb -s localhost:{port}"

passed = 0
failed = 0

def check(desc, cmd, expect=None):
    global passed, failed
    r = subprocess.run(f"{ADB} shell \"{cmd}\"", shell=True, capture_output=True, text=True, timeout=10)
    out = r.stdout.strip()
    ok = (expect in out) if expect else (r.returncode == 0 and out != "")
    if ok:
        print(f"  [✓] {desc}")
        passed += 1
    else:
        print(f"  [✗] {desc}")
        failed += 1
    return ok

print("╔══════════════════════════════════════════╗")
print("║  Redroid GML - Verification              ║")
print("╚══════════════════════════════════════════╝\n")

check("ADB connected", "echo ok", "ok")
check("Root access", "id", "uid=0")
check("Android 12+", "getprop ro.build.version.release", "1")
check("ARM64 ABI", "getprop ro.product.cpu.abilist", "arm64-v8a")
check("libndk present", "ls /system/lib64/libndk_translation.so", "libndk")
check("Native bridge enabled", "getprop ro.enable.native.bridge.exec", "1")
check("Magisk daemon", "ps -A | grep magiskd", "magiskd")
check("su works", "su -c whoami", "root")
check("Play Store", "pm list packages | grep vending", "vending")
check("Google Play Services", "pm list packages | grep com.google.android.gms", "gms")
check("Frida binary", "ls /data/local/tmp/fs", "fs")

# Device spoof check
model = subprocess.run(f"{ADB} shell getprop ro.product.model", shell=True, capture_output=True, text=True).stdout.strip()
if model and "redroid" not in model.lower():
    print(f"  [✓] Device spoofed (model: {model})")
    passed += 1
else:
    print(f"  [✗] Device not spoofed (model: {model})")
    failed += 1

# Frida test
try:
    r = subprocess.run(f"timeout 10 frida -H 127.0.0.1:{frida_port} -p 1 -e 'console.log(\"OK\")'",
                      shell=True, capture_output=True, text=True, timeout=15)
    if "OK" in r.stdout:
        print(f"  [✓] Frida works (port {frida_port})")
        passed += 1
    else:
        print(f"  [✗] Frida failed")
        failed += 1
except:
    print(f"  [?] Frida - skipped")
    failed += 1

print(f"\n{'━'*42}")
print(f"  Results: {passed} passed, {failed} failed")
print(f"{'━'*42}")
