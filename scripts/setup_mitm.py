#!/usr/bin/env python3
"""Install mitmproxy CA cert and configure proxy"""
import subprocess, sys, os

port = sys.argv[1] if len(sys.argv) > 1 else "5555"
proxy_port = sys.argv[2] if len(sys.argv) > 2 else "8080"
ADB = f"adb -s localhost:{port}"

def shell(cmd): return subprocess.run(f"{ADB} shell \"{cmd}\"", shell=True, capture_output=True, text=True).stdout.strip()
def run(cmd): return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()

cert = os.path.expanduser("~/.mitmproxy/mitmproxy-ca-cert.cer")
if not os.path.exists(cert):
    print("[*] Generating mitmproxy CA...")
    subprocess.run("timeout 5 mitmdump >/dev/null 2>&1", shell=True)

if not os.path.exists(cert):
    print("[!] mitmproxy CA not found. Install: pip install mitmproxy"); sys.exit(1)

hash_val = run(f"openssl x509 -inform PEM -subject_hash_old -in {cert} | head -1")
print(f"[*] CA hash: {hash_val}")

subprocess.run(f"{ADB} root", shell=True); import time; time.sleep(2)
shell("mount -o rw,remount /")
subprocess.run(f"cp {cert} /tmp/{hash_val}.0", shell=True)
subprocess.run(f"{ADB} push /tmp/{hash_val}.0 /system/etc/security/cacerts/{hash_val}.0", shell=True)
shell(f"chmod 644 /system/etc/security/cacerts/{hash_val}.0")

gateway = shell("ip route | grep default | awk '{print $3}'") or "172.20.0.1"
shell(f"settings put global http_proxy {gateway}:{proxy_port}")

print(f"\n[✓] MITM ready! Proxy: {gateway}:{proxy_port}")
print(f"    Start: mitmdump --set block_global=false")
print(f"    Disable: adb -s localhost:{port} shell settings put global http_proxy :0")
