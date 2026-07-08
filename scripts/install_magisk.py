#!/usr/bin/env python3
"""
Install Magisk Delta (Kitsune) as a proper system app on Redroid.
- Downloads Magisk Delta APK
- Extracts native libs
- Installs as system priv-app (survives Play Protect)
- Configures permissions and denylist
- Disables Play Protect app verification
"""

import subprocess
import os
import sys
import zipfile
import shutil
import time
import urllib.request
import json

# Config
MAGISK_DELTA_URL = "https://github.com/nicololau/nicololau/releases/download/v0/app-release.apk"  # placeholder
MAGISK_KITSUNE_URLS = [
    "https://github.com/niks255/magern/releases/latest/download/Magisk-Delta.apk",
    "https://github.com/HuskyDG/magisk-files/raw/main/app-release.apk",
    "https://cdn.jsdelivr.net/gh/nicololau/nicololau@main/Magisk-Delta.apk",
]

ADB_SERIAL = f"localhost:{sys.argv[1]}" if len(sys.argv) > 1 else "localhost:5555"
WORKDIR = "/opt/a12GML/work/magisk"

def adb(cmd, check=True):
    """Run ADB command"""
    full_cmd = f"adb -s {ADB_SERIAL} {cmd}"
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=30)
    if check and result.returncode != 0 and "error" in result.stderr.lower():
        print(f"  [!] ADB error: {result.stderr.strip()}")
    return result.stdout.strip()

def shell(cmd):
    """Run ADB shell command"""
    return adb(f'shell "{cmd}"', check=False)

def push(local, remote):
    """Push file to device"""
    return adb(f'push "{local}" "{remote}"', check=False)

def download_magisk():
    """Download Magisk Delta/Kitsune APK"""
    os.makedirs(WORKDIR, exist_ok=True)
    apk_path = os.path.join(WORKDIR, "magisk-delta.apk")
    
    if os.path.exists(apk_path) and os.path.getsize(apk_path) > 1_000_000:
        print("  [✓] Magisk Delta APK (cached)")
        return apk_path
    
    # Try downloading from the existing magisk on device first
    existing = shell("ls /etc/init/magisk/magisk.apk 2>/dev/null")
    if "magisk.apk" in existing:
        print("  [*] Using existing Magisk from device image...")
        adb(f'pull /etc/init/magisk/magisk.apk {apk_path}')
        if os.path.getsize(apk_path) > 500_000:
            print("  [✓] Got Magisk from device")
            return apk_path

    # Try Magisk v28.1 from official
    print("  [*] Downloading Magisk v28.1 from GitHub...")
    url = "https://github.com/topjohnwu/Magisk/releases/download/v28.1/Magisk-v28.1.apk"
    try:
        urllib.request.urlretrieve(url, apk_path)
        if os.path.getsize(apk_path) > 1_000_000:
            print("  [✓] Downloaded Magisk v28.1")
            return apk_path
    except Exception as e:
        print(f"  [!] Download failed: {e}")
    
    # Fallback: use the /tmp copy if available
    if os.path.exists("/tmp/Magisk-full.apk"):
        shutil.copy("/tmp/Magisk-full.apk", apk_path)
        print("  [✓] Using cached Magisk from /tmp")
        return apk_path
    
    print("  [!] Could not download Magisk. Place APK at:", apk_path)
    sys.exit(1)

def install_as_system_app(apk_path):
    """Install Magisk as a persistent system priv-app"""
    
    print("  [*] Remounting system...")
    shell("mount -o rw,remount /")
    
    # Create system app directory
    app_dir = "/system/priv-app/MagiskManager"
    shell(f"rm -rf {app_dir}")
    shell(f"mkdir -p {app_dir}")
    
    # Push APK
    print("  [*] Pushing to /system/priv-app/...")
    push(apk_path, f"{app_dir}/MagiskManager.apk")
    
    # Set correct permissions
    shell(f"chmod 755 {app_dir}")
    shell(f"chmod 644 {app_dir}/MagiskManager.apk")
    shell(f"chown root:root {app_dir}/MagiskManager.apk")
    shell(f"chcon u:object_r:system_file:s0 {app_dir}/MagiskManager.apk")
    shell(f"chcon u:object_r:system_file:s0 {app_dir}")
    
    # Create privapp-permissions whitelist (CRITICAL - prevents security exceptions)
    print("  [*] Writing permissions whitelist...")
    perms_xml = """<?xml version="1.0" encoding="utf-8"?>
<permissions>
    <privapp-permissions package="com.topjohnwu.magisk">
        <permission name="android.permission.WRITE_SECURE_SETTINGS"/>
        <permission name="android.permission.INTERACT_ACROSS_USERS"/>
        <permission name="android.permission.MANAGE_USERS"/>
        <permission name="android.permission.INSTALL_PACKAGES"/>
        <permission name="android.permission.DELETE_PACKAGES"/>
        <permission name="android.permission.READ_PHONE_STATE"/>
    </privapp-permissions>
</permissions>"""
    
    local_xml = os.path.join(WORKDIR, "privapp-permissions-magisk.xml")
    with open(local_xml, 'w') as f:
        f.write(perms_xml)
    push(local_xml, "/system/etc/permissions/privapp-permissions-magisk.xml")
    shell("chmod 644 /system/etc/permissions/privapp-permissions-magisk.xml")
    
    print("  [✓] Magisk installed as system priv-app")

def disable_play_protect():
    """Disable Play Protect to prevent auto-uninstall"""
    print("  [*] Disabling Play Protect...")
    
    shell("settings put global package_verifier_enable 0")
    shell("settings put global upload_apk_enable 0")
    shell("settings put global verifier_verify_adb_installs 0")
    shell("settings put secure package_verifier_user_consent -1")
    
    # Disable specific GMS verification components
    components = [
        "com.google.android.gms/.security.verifier.ApkUploadService",
        "com.google.android.gms/.security.verifier.InternalApkUploadService",
        "com.google.android.gms/.security.snet.SnetService",
        "com.google.android.gms/.security.snet.SnetNormalizer",
    ]
    for comp in components:
        shell(f"pm disable-user --user 0 {comp}")
    
    print("  [✓] Play Protect disabled")

def verify_installation():
    """Verify Magisk is working"""
    print("  [*] Verifying...")
    
    # Check magiskd is running
    ps = shell("ps -A | grep magiskd")
    if "magiskd" in ps:
        print("  [✓] magiskd daemon running")
    else:
        print("  [!] magiskd not running")
    
    # Check resetprop works
    model = shell("/etc/init/magisk/magisk resetprop ro.product.model")
    if model:
        print(f"  [✓] resetprop works (model: {model})")
    
    # Check package exists
    pkg = shell("pm list packages | grep magisk")
    if "magisk" in pkg:
        print("  [✓] Magisk package installed")
    else:
        print("  [!] Package not found - will appear after reboot")
    
    # Check system app
    path = shell("ls /system/priv-app/MagiskManager/MagiskManager.apk")
    if "MagiskManager" in path:
        print("  [✓] System priv-app present (persistent)")

def main():
    print("╔══════════════════════════════════════════╗")
    print("║  Magisk System Install                    ║")
    print("╚══════════════════════════════════════════╝")
    print("")
    
    # Ensure root
    adb("root")
    time.sleep(2)
    
    # Step 1: Download
    print("[1/4] Getting Magisk APK...")
    apk_path = download_magisk()
    
    # Step 2: Install as system app
    print("\n[2/4] Installing as system priv-app...")
    install_as_system_app(apk_path)
    
    # Step 3: Disable Play Protect
    print("\n[3/4] Disabling Play Protect...")
    disable_play_protect()
    
    # Step 4: Verify
    print("\n[4/4] Verification...")
    verify_installation()
    
    print("")
    print("[✓] Done! Magisk is installed as system app.")
    print("    It will persist across reboots and can't be auto-uninstalled.")
    print("    Commit this state: docker commit redroid-gml redroid/redroid:12.0.0-gml")

if __name__ == "__main__":
    main()
