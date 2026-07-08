#!/usr/bin/env python3
"""Spoof GPS location to match device country or custom coordinates"""
import subprocess, sys

COORDS = {
    'US':'37.7749,-122.4194','ID':'-6.2088,106.8456','NG':'6.5244,3.3792',
    'SA':'24.7136,46.6753','EG':'30.0444,31.2357','PK':'24.8607,67.0011',
    'TR':'41.0082,28.9784','TH':'13.7563,100.5018','PH':'14.5995,120.9842',
    'BR':'-23.5505,-46.6333','IN':'19.0760,72.8777','DE':'52.5200,13.4050',
    'GB':'51.5074,-0.1278','MY':'3.1390,101.6869','VN':'10.8231,106.6297',
}

def main():
    port = sys.argv[1] if len(sys.argv) > 1 else "5555"
    loc = sys.argv[2] if len(sys.argv) > 2 else "auto"
    
    adb = lambda c: subprocess.run(f"adb -s localhost:{port} shell \"{c}\"", shell=True, capture_output=True, text=True).stdout.strip()
    
    if loc == "auto":
        cc = adb("getprop gsm.sim.operator.iso-country").upper() or "US"
        coord = COORDS.get(cc, COORDS['US'])
    elif ',' in loc:
        coord = loc
    else:
        coord = COORDS.get(loc.upper(), COORDS['US'])
    
    lat, lon = coord.split(',')
    adb("settings put secure mock_location 1")
    adb(f"cmd location providers add-test-provider gps 0 0 0 false true true true false 1")
    adb(f"cmd location providers set-test-provider-enabled gps true")
    adb(f"cmd location providers set-test-provider-location gps --location {lat},{lon} --accuracy 5.0")
    print(f"[✓] GPS: lat={lat} lon={lon}")

if __name__ == "__main__":
    main()
