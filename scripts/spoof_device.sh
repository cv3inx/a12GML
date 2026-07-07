#!/bin/bash
# Spoof device to a REAL identity with valid IMEI from global TAC database (250 real TACs, 50 devices)
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

# Apply to device
adb -s localhost:${PORT} shell "\
/etc/init/magisk/magisk resetprop ro.product.brand '${BRAND}';
/etc/init/magisk/magisk resetprop ro.product.model '${MODEL}';
/etc/init/magisk/magisk resetprop ro.product.device '${DEVICE}';
/etc/init/magisk/magisk resetprop ro.product.name '${PRODUCT}';
/etc/init/magisk/magisk resetprop ro.product.manufacturer '${MANUFACTURER}';
/etc/init/magisk/magisk resetprop ro.build.fingerprint '${FINGERPRINT}';
/etc/init/magisk/magisk resetprop ro.hardware '${HARDWARE}';
/etc/init/magisk/magisk resetprop ro.product.board '${BOARD}';
/etc/init/magisk/magisk resetprop ro.build.display.id '${DISPLAY}';
/etc/init/magisk/magisk resetprop ro.build.version.release '${ANDROID_VER}';
/etc/init/magisk/magisk resetprop persist.radio.imei '${IMEI1}';
/etc/init/magisk/magisk resetprop persist.radio.imei1 '${IMEI1}';
/etc/init/magisk/magisk resetprop persist.radio.imei2 '${IMEI2}';
/etc/init/magisk/magisk resetprop ro.ril.miui.imei0 '${IMEI1}';
/etc/init/magisk/magisk resetprop ro.ril.miui.imei1 '${IMEI2}';
/etc/init/magisk/magisk resetprop ro.ril.oem.imei '${IMEI1}';
/etc/init/magisk/magisk resetprop gsm.version.baseband '${BASEBAND}';
/etc/init/magisk/magisk resetprop ro.serialno '${SERIAL}';
/etc/init/magisk/magisk resetprop ro.boot.serialno '${SERIAL}';
/etc/init/magisk/magisk resetprop persist.sys.wifi.mac '${WIFI_MAC}';
/etc/init/magisk/magisk resetprop ro.boot.wifimacaddr '${WIFI_MAC}';
/etc/init/magisk/magisk resetprop ro.boot.btmacaddr '${BT_MAC}';
/etc/init/magisk/magisk resetprop persist.bluetooth.address '${BT_MAC}';
settings put secure android_id '${ANDROID_ID}';
wm density ${DENSITY}" 2>/dev/null

echo ""
echo "[✓] Spoofed as $BRAND $MODEL"
echo "    IMEI: $IMEI1 | Serial: $SERIAL"
