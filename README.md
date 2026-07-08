# Redroid GML

**Android 12-14 emulator with GApps + Magisk + Libndk + Frida + Device Spoofing**

Fork of [ayasa520/redroid-script](https://github.com/ayasa520/redroid-script) with extended features:
- Removed version gates (NDK now works on A12-14, not just A11)
- Added Frida server auto-install (renamed binary to avoid Play Integrity detection)
- Added real device spoofing (112 devices, 547 verified IMEI TAC codes from GSMA database)
- MindTheGapps support for A12-15 (Play Store + Google Services)
- Universal Frida bypass script (SSL pinning + root + emulator + frida detection)

## Quick Start

```bash
# Clone
git clone https://github.com/cv3inx/a12GML.git
cd a12GML

# Install dependencies
pip install -r redroid-script/requirements.txt
apt install lzip

# Build image (one command)
cd redroid-script
python3 redroid.py -a 12.0.0 -mtg -m -n -f -s

# Run
docker run -d --privileged --name redroid-gml -p 5555:5555 \
    redroid/redroid:12.0.0_gapps_ndk_magisk_frida_spoof \
    androidboot.redroid_gpu_mode=guest \
    ro.product.cpu.abilist=x86_64,arm64-v8a,x86,armeabi-v7a,armeabi \
    ro.product.cpu.abilist64=x86_64,arm64-v8a \
    ro.product.cpu.abilist32=x86,armeabi-v7a,armeabi \
    ro.dalvik.vm.isa.arm=x86 \
    ro.dalvik.vm.isa.arm64=x86_64 \
    ro.enable.native.bridge.exec=1 \
    ro.dalvik.vm.native.bridge=libndk_translation.so \
    ro.ndk_translation.version=0.2.2
```

Or use the helper scripts:

```bash
./run.sh          # Start container with auto Frida + device spoof
./test.sh         # Verify all components
./stop.sh         # Stop container
```

## Build Options

```
python3 redroid-script/redroid.py [options]

Android Version:
  -a {14.0.0,13.0.0,12.0.0,11.0.0}    (default: 12.0.0)

GApps (pick one):
  -mtg    MindTheGapps (recommended, A12-15)
  -lg     LiteGapps
  -g      OpenGapps (A11 only)

ARM Translation (pick one):
  -n      libndk translation (recommended for AMD)
  -i      libhoudini (Intel only)

Root & Tools:
  -m      Magisk (systemless root via init)
  -f      Frida server (auto-download, renamed binary)
  -s      Device spoofing (112 real devices, 547 TACs)
  -w      Widevine DRM (L3)
```

### Examples

```bash
# Recommended: Full A12 build
python3 redroid.py -a 12.0.0 -mtg -m -n -f -s

# Android 14 + GApps + Magisk + Frida (no NDK - use houdini or skip)
python3 redroid.py -a 14.0.0 -mtg -m -f

# Minimal: just root + frida
python3 redroid.py -a 12.0.0 -m -f

# Everything on A11 (legacy, all components proven)
python3 redroid.py -a 11.0.0 -g -m -n -f -s -w
```

## Features

| Feature | A11 | A12 | A13 | A14 | Method |
|---------|-----|-----|-----|-----|--------|
| MindTheGapps | ✅ | ✅ | ✅ | ✅ | System overlay |
| Magisk (root) | ✅ | ✅ | ✅ | ✅ | bootanim.rc init |
| libndk (ARM translation) | ✅ | ✅ | ✅ | ✅* | System overlay |
| Frida | ✅ | ✅ | ✅ | ✅ | /data/local/tmp/fs |
| Device Spoofing | ✅ | ✅ | ✅ | ✅ | resetprop |
| Widevine | ✅ | ✅ | ✅ | ✅ | System overlay |
| Houdini (Intel) | ✅ | ✅ | ✅ | ✅ | System overlay |

\* NDK on A13-14: works but some Flutter apps with NEON instructions may still SIGILL

## Device Spoofing

Spoof your emulator as a real device with valid IMEI, serial, MAC, and fingerprint:

```bash
# Random device identity
./scripts/spoof_device.sh 5555 random

# Specific device (index 0-111)
./scripts/spoof_device.sh 5555 0    # Samsung Galaxy S25 Ultra
./scripts/spoof_device.sh 5555 5    # OPPO A5 Pro 5G
./scripts/spoof_device.sh 5555 9    # Google Pixel 8

# Rotate identity every hour
./scripts/rotate_identity.sh 5555 3600
```

### What gets spoofed:
- `ro.product.brand`, `model`, `device`, `manufacturer`
- `ro.build.fingerprint` (full real fingerprint)
- `ro.hardware`, `ro.product.board`
- `persist.radio.imei` / `imei2` (valid Luhn checksum, real TAC prefix)
- `ro.serialno` (random, correct format per brand)
- `persist.sys.wifi.mac` (real manufacturer OUI)
- `ro.boot.btmacaddr`
- `android_id`, display density
- `ro.build.tags=release-keys`, `ro.build.type=user`

### Device Database
- **112 real devices** from 12 brands (Samsung, Xiaomi, OPPO, Realme, TECNO, vivo, Google, Motorola, Huawei, OnePlus, POCO, Nokia)
- **547 verified TAC codes** from GSMA global database (255K entries, filtered to 2024-2026)
- IMEIs generated with valid **Luhn checksum** (indistinguishable from real)
- MAC addresses use correct **manufacturer OUI** prefixes

## Frida

Frida starts with `./run.sh` or manually:

```bash
# Start frida (already on device at /data/local/tmp/fs)
adb shell /data/local/tmp/fs -D &
adb forward tcp:27042 tcp:27042

# Connect
frida -H 127.0.0.1:27042 -f com.example.app -l hook.js
frida-ps -H 127.0.0.1:27042
```

### Universal Bypass Script

One script that handles SSL pinning + root detection + emulator detection + frida detection:

```bash
frida -H 127.0.0.1:27042 -f com.target.app -l configs/frida_hooks/universal_bypass.js
```

Bypasses:
- **SSL Pinning**: OkHttp CertificatePinner, TrustManager, Conscrypt, Network Security Config, WebView SSL errors, HostnameVerifier
- **Root Detection**: su binary checks, Magisk package detection, build.prop tags, Runtime.exec blocking
- **Emulator Detection**: Build fields, system properties, telephony faking, file artifact hiding, ADB status
- **Frida Detection**: Port scanning block, /proc/maps filtering, process name hiding

## Helper Scripts

| Script | Description |
|--------|-------------|
| `run.sh [port]` | Start container + Frida + random device spoof |
| `test.sh [port]` | Verify all 13 components |
| `stop.sh` / `destroy.sh` | Lifecycle |
| `scripts/spoof_device.sh [port] [idx]` | Apply random real device identity |
| `scripts/spoof_gps.sh [port] [country]` | Mock GPS location |
| `scripts/check_detection.sh [port]` | Scan for detectable artifacts + auto-fix |
| `scripts/rotate_identity.sh [port] [sec]` | Identity rotation daemon |
| `scripts/snapshot.sh {save\|restore} [name]` | Container state save/restore |
| `scripts/install_app.sh [port] <apk>` | Install APK + auto-grant permissions |
| `scripts/install_gapps.sh [port]` | Manual GApps installer |
| `scripts/install_magisk.py [port]` | Magisk system priv-app installer |
| `scripts/setup_mitm.sh [port]` | mitmproxy CA + proxy config |

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Host (x86_64 Linux + Docker)                   │
│  ┌───────────────────────────────────────────┐  │
│  │  Redroid Container (privileged)           │  │
│  │  ┌─────────────────────────────────────┐  │  │
│  │  │  Android 12-14                      │  │  │
│  │  │  ├── Magisk (bootanim.rc init)      │  │  │
│  │  │  │   ├── magiskd (daemon)           │  │  │
│  │  │  │   ├── su, resetprop             │  │  │
│  │  │  │   └── SYSTEMMODE=true           │  │  │
│  │  │  ├── GApps (MindTheGapps)          │  │  │
│  │  │  │   ├── Play Store                │  │  │
│  │  │  │   └── Google Play Services      │  │  │
│  │  │  ├── libndk (ARM → x86 translation)│  │  │
│  │  │  ├── Frida (/data/local/tmp/fs)    │  │  │
│  │  │  └── Device spoof (resetprop)      │  │  │
│  │  └─────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

## How Magisk Works (Container Mode)

Unlike real devices, containers have no boot image to patch. This setup uses ayasa520's method:

1. `bootanim.rc` init script runs at boot:
   - `magiskpolicy --live --magisk` (SELinux policy)
   - `magisk --auto-selinux --setup-sbin` (create /sbin tmpfs)
   - `magisk --post-fs-data` / `--service` / `--boot-complete`
2. `magiskd` daemon runs from `/sbin/magisk`
3. Magisk app detects via `SYSTEMMODE=true` in config
4. `su`, `resetprop`, denylist, modules all functional

Binary: [ayasa520/Magisk](https://github.com/ayasa520/Magisk) (Delta fork with `--auto-selinux` support)

## Requirements

- Linux x86_64 host with Docker
- `adb` (android-tools)
- `python3` + `pip`
- `frida-tools` (`pip install frida-tools`)
- `lzip` (`apt install lzip`)

## Known Limitations

- **Flutter apps with NEON instructions** may SIGILL on x86_64 (Skia rendering crash) — this is a fundamental NDK translation limitation
- **SafetyNet/Play Integrity hardware attestation** will fail (device spoofing is prop-level only)
- **Magisk UI may show "Installed: N/A"** for ramdisk — root still works, this is cosmetic for container setups
- **Frida can't attach on some kernel configs** — use `adb root` (not su) for the container and ensure `ptrace_scope=0`

## Credits

- [redroid](https://github.com/remote-android/redroid-doc) - Android in Docker
- [ayasa520/redroid-script](https://github.com/ayasa520/redroid-script) - Original GApps/Magisk/NDK automation
- [ayasa520/Magisk](https://github.com/ayasa520/Magisk) - Container-compatible Magisk Delta
- [MindTheGapps](https://github.com/nicololau/nicololau/MindTheGappsBuilder) - Google Apps
- [Frida](https://frida.re/) - Dynamic instrumentation
- [MoazEb/tac-database](https://github.com/MoazEb/tac-database) - IMEI TAC database (255K entries)

## License

MIT
