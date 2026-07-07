#!/bin/bash
# Spoof GPS location to match device country or custom coordinates
# Usage: ./spoof_gps.sh [port] [country_code|lat,lon]

PORT="${1:-5555}"
LOCATION="${2:-auto}"

declare -A COORDS
COORDS[US]="37.7749,-122.4194"    # San Francisco
COORDS[ID]="−6.2088,106.8456"    # Jakarta
COORDS[NG]="6.5244,3.3792"       # Lagos
COORDS[SA]="24.7136,46.6753"     # Riyadh
COORDS[EG]="30.0444,31.2357"     # Cairo
COORDS[PK]="24.8607,67.0011"     # Karachi
COORDS[BD]="23.8103,90.4125"     # Dhaka
COORDS[TR]="41.0082,28.9784"     # Istanbul
COORDS[TH]="13.7563,100.5018"    # Bangkok
COORDS[PH]="14.5995,120.9842"    # Manila
COORDS[BR]="−23.5505,−46.6333"  # São Paulo
COORDS[IN]="19.0760,72.8777"     # Mumbai
COORDS[DE]="52.5200,13.4050"     # Berlin
COORDS[GB]="51.5074,-0.1278"     # London
COORDS[MY]="3.1390,101.6869"     # Kuala Lumpur
COORDS[VN]="10.8231,106.6297"    # Ho Chi Minh

if [ "$LOCATION" = "auto" ]; then
    # Get country from device spoof
    CC=$(adb -s localhost:${PORT} shell getprop gsm.sim.operator.iso-country 2>/dev/null | tr -d '\r')
    [ -z "$CC" ] && CC="US"
    CC=$(echo "$CC" | tr '[:lower:]' '[:upper:]')
    COORD="${COORDS[$CC]:-${COORDS[US]}}"
    echo "[*] Auto GPS: country=$CC -> $COORD"
elif echo "$LOCATION" | grep -q ","; then
    COORD="$LOCATION"
    echo "[*] Custom GPS: $COORD"
else
    CC=$(echo "$LOCATION" | tr '[:lower:]' '[:upper:]')
    COORD="${COORDS[$CC]:-${COORDS[US]}}"
    echo "[*] Country GPS: $CC -> $COORD"
fi

LAT=$(echo "$COORD" | cut -d',' -f1)
LON=$(echo "$COORD" | cut -d',' -f2)

# Enable mock location
adb -s localhost:${PORT} shell "settings put secure mock_location 1" 2>/dev/null
adb -s localhost:${PORT} shell "appops set com.android.shell android:mock_location allow" 2>/dev/null

# Set location via geo fix (emulator command via telnet isn't available in redroid)
# Use the am broadcast method instead
adb -s localhost:${PORT} shell "
    cmd location providers add-test-provider gps 0 0 0 false true true true false 1;
    cmd location providers set-test-provider-enabled gps true;
    cmd location providers set-test-provider-location gps --location $LAT,$LON --accuracy 5.0;
" 2>/dev/null

echo "[✓] GPS set: lat=$LAT lon=$LON"
echo "    Verify: adb -s localhost:${PORT} shell dumpsys location | grep 'last location'"
