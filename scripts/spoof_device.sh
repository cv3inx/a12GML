#!/bin/bash
# Spoof device to a REAL identity with valid IMEI from global TAC database (547 real TACs, 112 devices)
# Uses Magisk resetprop to override read-only system properties
# Usage: ./spoof_device.sh [port] [random|index]
set -e

PORT="${1:-5555}"
DEVICE_IDX="${2:-random}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TAC_DB="$ROOT_DIR/spoofdb/tac_database.json"
VARS_FILE=$(mktemp)

# Generate identity
python3 "$SCRIPT_DIR/gen_identity.py" "$TAC_DB" "$DEVICE_IDX" "$VARS_FILE"
source "$VARS_FILE"
rm -f "$VARS_FILE"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Device Spoof Applied                                    ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  Brand:       $BRAND"
echo "║  Model:       $MODEL"
echo "║  IMEI 1:      $IMEI1"
echo "║  IMEI 2:      $IMEI2"
echo "║  Serial:      $SERIAL"
echo "║  Android ID:  $ANDROID_ID"
echo "║  WiFi MAC:    $WIFI_MAC"
echo "║  BT MAC:      $BT_MAC"
echo "║  Fingerprint: ${FINGERPRINT:0:55}..."
echo "║  Source DB:    $SPECS"
echo "╚══════════════════════════════════════════════════════════╝"

# Apply using resetprop (overrides read-only ro.* properties)
RP="/etc/init/magisk/magisk resetprop"
adb -s localhost:${PORT} shell "$RP ro.product.brand '${BRAND}'"
adb -s localhost:${PORT} shell "$RP ro.product.model '${MODEL}'"
adb -s localhost:${PORT} shell "$RP ro.product.device '${DEVICE}'"
adb -s localhost:${PORT} shell "$RP ro.product.name '${PRODUCT}'"
adb -s localhost:${PORT} shell "$RP ro.product.manufacturer '${MANUFACTURER}'"
adb -s localhost:${PORT} shell "$RP ro.build.fingerprint '${FINGERPRINT}'"
adb -s localhost:${PORT} shell "$RP ro.hardware '${HARDWARE}'"
adb -s localhost:${PORT} shell "$RP ro.product.board '${BOARD}'"
adb -s localhost:${PORT} shell "$RP ro.build.display.id '${DISPLAY}'"
adb -s localhost:${PORT} shell "$RP ro.build.version.release '${ANDROID_VER}'"
adb -s localhost:${PORT} shell "$RP ro.build.tags release-keys"
adb -s localhost:${PORT} shell "$RP ro.build.type user"
adb -s localhost:${PORT} shell "$RP gsm.version.baseband '${BASEBAND}'"
adb -s localhost:${PORT} shell "$RP ro.serialno '${SERIAL}'"
adb -s localhost:${PORT} shell "$RP ro.boot.serialno '${SERIAL}'"
adb -s localhost:${PORT} shell "$RP persist.radio.imei '${IMEI1}'"
adb -s localhost:${PORT} shell "$RP persist.radio.imei1 '${IMEI1}'"
adb -s localhost:${PORT} shell "$RP persist.radio.imei2 '${IMEI2}'"
adb -s localhost:${PORT} shell "$RP ro.ril.oem.imei '${IMEI1}'"
adb -s localhost:${PORT} shell "$RP persist.sys.wifi.mac '${WIFI_MAC}'"
adb -s localhost:${PORT} shell "$RP ro.boot.wifimacaddr '${WIFI_MAC}'"
adb -s localhost:${PORT} shell "$RP ro.boot.btmacaddr '${BT_MAC}'"
adb -s localhost:${PORT} shell "$RP persist.bluetooth.address '${BT_MAC}'"
adb -s localhost:${PORT} shell "settings put secure android_id '${ANDROID_ID}'" 2>/dev/null
adb -s localhost:${PORT} shell "settings put global device_name '${MODEL}'" 2>/dev/null
adb -s localhost:${PORT} shell "wm density ${DENSITY}" 2>/dev/null

echo ""
echo "[✓] Spoofed as $BRAND $MODEL"
echo "    IMEI: $IMEI1 | Serial: $SERIAL"
