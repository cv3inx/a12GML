#!/usr/bin/env python3
"""Save/restore container snapshots"""
import subprocess, sys

action = sys.argv[1] if len(sys.argv) > 1 else "list"
name = sys.argv[2] if len(sys.argv) > 2 else None

def run(cmd): return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()

if action == "save":
    if not name: print("Usage: snapshot.py save <name>"); sys.exit(1)
    run(f"docker commit redroid-gml redroid-gml-snap:{name}")
    print(f"[✓] Saved: redroid-gml-snap:{name}")
elif action == "list":
    print("Snapshots:")
    print(run("docker images --format '  {{.Tag}}\\t{{.CreatedSince}}\\t{{.Size}}' redroid-gml-snap") or "  (none)")
elif action == "delete":
    if not name: print("Usage: snapshot.py delete <name>"); sys.exit(1)
    run(f"docker rmi redroid-gml-snap:{name}")
    print(f"[✓] Deleted: {name}")
