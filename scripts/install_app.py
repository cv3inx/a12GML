#!/usr/bin/env python3
"""Install APK with auto-grant all permissions"""
import subprocess, sys, os, glob

port = sys.argv[1] if len(sys.argv) > 1 else "5555"
target = sys.argv[2] if len(sys.argv) > 2 else None
ADB = f"adb -s localhost:{port}"

if not target:
    print("Usage: install_app.py [port] <apk_or_dir>"); sys.exit(1)

apks = glob.glob(f"{target}/*.apk") if os.path.isdir(target) else [target]

for apk in apks:
    print(f"[*] Installing {os.path.basename(apk)}...")
    subprocess.run(f"{ADB} install -r -g '{apk}'", shell=True)
