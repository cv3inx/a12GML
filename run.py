#!/usr/bin/env python3
"""Start Redroid GML container with Frida + device spoofing"""

import subprocess
import sys
import time
import os

IMAGE = "redroid/redroid:12.0.0-gml"
FALLBACK_IMAGE = "redroid/redroid:12.0.0_ndk_magisk"
CONTAINER = "redroid-gml"

def run(cmd, check=False):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return r.stdout.strip()

def main():
    port = sys.argv[1] if len(sys.argv) > 1 else "5555"
    frida_port = sys.argv[2] if len(sys.argv) > 2 else "27042"
    
    # Check image
    image = IMAGE
    if run(f"docker image inspect {IMAGE} 2>/dev/null") == "":
        print(f"[!] {IMAGE} not found, using fallback")
        image = FALLBACK_IMAGE
        if run(f"docker image inspect {FALLBACK_IMAGE} 2>/dev/null") == "":
            print("[!] No image found. Run: python3 build.py -a 12.0.0 -mtg -m -n -f -s")
            sys.exit(1)
    
    # Stop existing
    run(f"docker stop {CONTAINER} 2>/dev/null")
    run(f"docker rm {CONTAINER} 2>/dev/null")
    
    print(f"[*] Starting Redroid GML on port {port}...")
    run(f"""docker run -d --name {CONTAINER} --privileged -p {port}:5555 {image} \
        androidboot.redroid_gpu_mode=guest \
        androidboot.redroid_fps=30 \
        androidboot.hardware=redroid \
        ro.product.cpu.abilist=x86_64,arm64-v8a,x86,armeabi-v7a,armeabi \
        ro.product.cpu.abilist64=x86_64,arm64-v8a \
        ro.product.cpu.abilist32=x86,armeabi-v7a,armeabi \
        ro.dalvik.vm.isa.arm=x86 \
        ro.dalvik.vm.isa.arm64=x86_64 \
        ro.enable.native.bridge.exec=1 \
        ro.dalvik.vm.native.bridge=libndk_translation.so \
        ro.ndk_translation.version=0.2.2""")
    
    print("[*] Waiting for boot (~35s)...")
    time.sleep(35)
    run(f"adb connect localhost:{port}")
    run(f"adb -s localhost:{port} wait-for-device")
    run(f"adb -s localhost:{port} root")
    time.sleep(3)
    
    # Start Frida
    print("[*] Starting Frida...")
    run(f"adb -s localhost:{port} shell 'pkill -9 fs 2>/dev/null; /data/local/tmp/fs -D &'")
    time.sleep(2)
    run(f"adb -s localhost:{port} forward tcp:{frida_port} tcp:27042")
    
    # Apply device spoof
    print("[*] Spoofing device...")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    subprocess.run([sys.executable, os.path.join(script_dir, "scripts", "spoof_device.py"), port, "random"])
    
    print(f"""
╔══════════════════════════════════════════════════╗
║  Redroid GML - READY                             ║
╠══════════════════════════════════════════════════╣
║  ADB:     localhost:{port}                          ║
║  Frida:   127.0.0.1:{frida_port}                      ║
║  Root:    ✓ (adb root)                           ║
║  ARM64:   ✓ (libndk translation)                 ║
╚══════════════════════════════════════════════════╝

  frida -H 127.0.0.1:{frida_port} -f <package>
  adb -s localhost:{port} install app.apk
""")

if __name__ == "__main__":
    main()
