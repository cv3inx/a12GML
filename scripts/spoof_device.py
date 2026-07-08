#!/usr/bin/env python3
"""Spoof device to a REAL identity with valid IMEI from global TAC database"""
import sys, os, subprocess, tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.gen_identity import generate_identity

def adb(port, cmd):
    return subprocess.run(f"adb -s localhost:{port} shell \"{cmd}\"", 
                         shell=True, capture_output=True, text=True, timeout=15).stdout.strip()

def main():
    port = sys.argv[1] if len(sys.argv) > 1 else "5555"
    idx = sys.argv[2] if len(sys.argv) > 2 else "random"
    
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "spoofdb", "tac_database.json")
    identity = generate_identity(db_path, idx)
    
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  Device Spoof Applied                                    ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print(f"║  Brand:       {identity['brand']}")
    print(f"║  Model:       {identity['model']}")
    print(f"║  IMEI 1:      {identity['imei1']}")
    print(f"║  IMEI 2:      {identity['imei2']}")
    print(f"║  Serial:      {identity['serial']}")
    print(f"║  Android ID:  {identity['android_id']}")
    print(f"║  WiFi MAC:    {identity['wifi_mac']}")
    print(f"║  BT MAC:      {identity['bt_mac']}")
    print(f"║  Fingerprint: {identity['fingerprint'][:55]}...")
    print(f"║  Source DB:    {identity['specs']}")
    print("╚══════════════════════════════════════════════════════════╝")
    
    RP = "/etc/init/magisk/magisk resetprop"
    # Try /sbin/magisk first, fallback to /etc/init/magisk/magisk
    test = adb(port, "/sbin/magisk -c 2>/dev/null")
    if "MAGISK" in test:
        RP = "/sbin/magisk resetprop"
    
    props = [
        (f"{RP} ro.product.brand", identity['brand']),
        (f"{RP} ro.product.model", identity['model']),
        (f"{RP} ro.product.device", identity['device']),
        (f"{RP} ro.product.name", identity['product']),
        (f"{RP} ro.product.manufacturer", identity['manufacturer']),
        (f"{RP} ro.build.fingerprint", identity['fingerprint']),
        (f"{RP} ro.hardware", identity['hardware']),
        (f"{RP} ro.product.board", identity['board']),
        (f"{RP} ro.build.display.id", identity['display']),
        (f"{RP} ro.build.version.release", identity['android_ver']),
        (f"{RP} ro.build.tags", "release-keys"),
        (f"{RP} ro.build.type", "user"),
        (f"{RP} gsm.version.baseband", identity['baseband']),
        (f"{RP} ro.serialno", identity['serial']),
        (f"{RP} ro.boot.serialno", identity['serial']),
        (f"{RP} persist.radio.imei", identity['imei1']),
        (f"{RP} persist.radio.imei1", identity['imei1']),
        (f"{RP} persist.radio.imei2", identity['imei2']),
        (f"{RP} ro.ril.oem.imei", identity['imei1']),
        (f"{RP} persist.sys.wifi.mac", identity['wifi_mac']),
        (f"{RP} ro.boot.wifimacaddr", identity['wifi_mac']),
        (f"{RP} ro.boot.btmacaddr", identity['bt_mac']),
        (f"{RP} persist.bluetooth.address", identity['bt_mac']),
    ]
    
    for cmd, val in props:
        adb(port, f"{cmd} '{val}'")
    
    adb(port, f"settings put secure android_id '{identity['android_id']}'")
    adb(port, f"settings put global device_name '{identity['model']}'")
    adb(port, f"wm density {identity['density']}")
    
    print(f"\n[✓] Spoofed as {identity['brand']} {identity['model']}")
    print(f"    IMEI: {identity['imei1']} | Serial: {identity['serial']}")

if __name__ == "__main__":
    main()
