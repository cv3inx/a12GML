#!/usr/bin/env python3
"""Destroy Redroid GML container and data"""
import subprocess, shutil, os
confirm = input("[!] Destroy container + data? [y/N] ").strip().lower()
if confirm == 'y':
    subprocess.run("docker stop redroid-gml 2>/dev/null; docker rm redroid-gml 2>/dev/null", shell=True)
    if os.path.exists("/opt/a12GML/data"):
        shutil.rmtree("/opt/a12GML/data")
    print("[✓] Destroyed")
else:
    print("Cancelled")
