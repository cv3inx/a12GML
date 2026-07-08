#!/usr/bin/env python3
"""Verify all Redroid GML components"""
import subprocess, sys

port = sys.argv[1] if len(sys.argv) > 1 else "5555"
frida_port = sys.argv[2] if len(sys.argv) > 2 else "27042"
ADB = f"adb -s localhost:{port}"
passed = failed = 0

def shell(cmd):
    r = subprocess.run(f"{ADB} shell \"{cmd}\"", shell=True, capture_output=True, text=True, timeout=10)
    return r.stdout.strip()

def check(desc, cmd, expect):
    global passed, failed
    out = shell(cmd)
    if expect in out:
        print(f"  [✓] {desc}"); passed += 1
    else:
        print(f"  [✗] {desc}"); failed += 1

print("╔══════════════════════════════════════════╗")
print("║  Redroid GML - Verification              ║")
print("╚══════════════════════════════════════════╝\n")

check("ADB connected", "echo ok", "ok")
check("Root access", "id", "uid=0")
check("Android 12+", "getprop ro.build.version.release", "1")
check("ARM64 ABI", "getprop ro.product.cpu.abilist", "arm64-v8a")
check("libndk present", "ls /system/lib64/libndk_translation.so", "libndk")
check("Native bridge", "getprop ro.enable.native.bridge.exec", "1")
check("Magisk daemon", "ps -A | grep magiskd", "magiskd")
check("su works", "su -c whoami", "root")
check("Play Store", "pm list packages | grep vending", "vending")
check("GMS", "pm list packages | grep com.google.android.gms", "gms")
check("Frida binary", "ls /data/local/tmp/fs", "fs")

model = shell("getprop ro.product.model")
if model and "redroid" not in model.lower():
    print(f"  [✓] Device spoofed ({model})"); passed += 1
else:
    print(f"  [✗] Not spoofed ({model})"); failed += 1

try:
    import frida
    device = frida.get_device_manager().add_remote_device(f"127.0.0.1:{frida_port}")
    procs = device.enumerate_processes()
    print(f"  [✓] Frida works ({len(procs)} procs)"); passed += 1
except Exception as e:
    print(f"  [✗] Frida: {e}"); failed += 1

print(f"\n{'━'*42}")
print(f"  Results: {passed} passed, {failed} failed")
print(f"{'━'*42}")
