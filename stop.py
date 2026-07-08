#!/usr/bin/env python3
"""Stop Redroid GML container"""
import subprocess
r = subprocess.run("docker stop redroid-gml", shell=True, capture_output=True)
print("[✓] Stopped" if r.returncode == 0 else "[!] Not running")
