#!/usr/bin/env python3
"""Rotate device identity at regular intervals"""
import time, sys, os, subprocess

port = sys.argv[1] if len(sys.argv) > 1 else "5555"
interval = int(sys.argv[2]) if len(sys.argv) > 2 else 3600

print(f"[*] Identity rotation: port={port}, interval={interval}s\n    Ctrl+C to stop\n")
script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "spoof_device.py")
while True:
    subprocess.run([sys.executable, script, port, "random"])
    print(f"    Next rotation in {interval}s...\n")
    time.sleep(interval)
