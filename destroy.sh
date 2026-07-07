#!/bin/bash
echo "[!] This will destroy the container and all data"
read -p "Continue? [y/N] " -n 1 -r; echo
[[ $REPLY =~ ^[Yy]$ ]] || exit 0
docker stop redroid-gml 2>/dev/null; docker rm redroid-gml 2>/dev/null
rm -rf /opt/a12GML/data
echo "[✓] Destroyed"
