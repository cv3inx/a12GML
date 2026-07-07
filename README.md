# Redroid A12 GML

**Android 12 emulator with GApps + Magisk + Libndk ARM translation + Frida + Device Spoofing**

A fully automated setup for running a rooted Android 12 instance on any x86_64 Linux host with Docker. Designed for security research, app testing, and reverse engineering.

## Features

| Feature | Status |
|---------|--------|
| Android 12 | ✅ |
| Root (Magisk + adb root) | ✅ |
| Google Play Store & Services | ✅ |
| ARM64 app support (libndk translation) | ✅ |
| Frida (auto-start, renamed binary) | ✅ |
| Real device spoofing (IMEI, fingerprint, MAC) | ✅ |
| mitmproxy CA (optional) | ✅ |

## Requirements

- Linux x86_64 host
- Docker
- `adb` (android-tools)
- `frida` CLI (`pip install frida-tools`)
- `python3` with `json` module
- [redroid-script](https://github.com/ayasa520/redroid-script) at `/opt/redroid-script`

## Quick Start

```bash
# 1. Build the image (first time only)
./build.sh

# 2. Start the container
./run.sh
# Starts on port 5555 by default, auto-starts Frida, applies random device spoof

# 3. Verify everything works
./test.sh
```

## Scripts

| Script | Description |
|--------|-------------|
| `build.sh` | Build the Docker image with all components |
| `run.sh [port]` | Start container with Frida + device spoof |
| `test.sh [port]` | Verify all components are working |
| `stop.sh` | Stop the container |
| `destroy.sh` | Remove container + data |
| `scripts/spoof_device.sh [port] [idx\|random]` | Randomize device identity |
| `scripts/install_gapps.sh [port]` | Install MindTheGapps |
| `scripts/setup_mitm.sh [port]` | Install mitmproxy CA + set proxy |

## Device Spoofing

The spoof system uses a database of 13 **real device fingerprints** with:
- Valid IMEI (generated with correct Luhn checksum from real TAC prefixes)
- Real build fingerprints
- Manufacturer-correct WiFi/BT MAC OUI prefixes
- Correct baseband versions
- Proper display density per device

```bash
# Random device each time
./scripts/spoof_device.sh 5555 random

# Specific device (index 0-12)
./scripts/spoof_device.sh 5555 3  # Xiaomi 11T Pro
```

### Supported Devices

| # | Device | Brand |
|---|--------|-------|
| 0 | Galaxy S21 (SM-G991B) | Samsung |
| 1 | Galaxy A54 (SM-A546E) | Samsung |
| 2 | Galaxy S23 Ultra (SM-S918B) | Samsung |
| 3 | 11T Pro (2201116SG) | Xiaomi |
| 4 | 13T Pro (23078PND5G) | Xiaomi |
| 5 | Reno (CPH2449) | OPPO |
| 6 | V2219 | vivo |
| 7 | RMX3630 | realme |
| 8 | CPH2581 | OnePlus |
| 9 | Pixel 8 | Google |
| 10 | Pixel 7 Pro | Google |
| 11 | X6739 | Infinix |
| 12 | CK8n | TECNO |

## Frida Usage

Frida starts automatically with `run.sh`. Connect via:

```bash
# List processes
frida-ps -H 127.0.0.1:27042

# Attach to running app
frida -H 127.0.0.1:27042 -p <PID> -l hook.js

# Spawn app with hooks
frida -H 127.0.0.1:27042 -f com.example.app -l hook.js
```

## Architecture

```
┌─────────────────────────────────────────┐
│  Host (x86_64 Linux)                    │
│  ┌───────────────────────────────────┐  │
│  │  Docker (privileged)              │  │
│  │  ┌─────────────────────────────┐  │  │
│  │  │  Redroid Android 12         │  │  │
│  │  │  ├── Magisk (root)          │  │  │
│  │  │  ├── GApps (Play Store)     │  │  │
│  │  │  ├── libndk (ARM→x86)      │  │  │
│  │  │  ├── Frida server          │  │  │
│  │  │  └── Device spoof (props)   │  │  │
│  │  └─────────────────────────────┘  │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## Notes

- ARM translation via libndk works for most apps but **Flutter apps with Skia NEON instructions may still crash** (SIGILL)
- Frida binary is renamed to avoid Play Integrity detection
- Device spoof is prop-level only (sufficient for most apps, but SafetyNet/Play Integrity will still fail hardware attestation)
- mitmproxy setup is optional and separate (`scripts/setup_mitm.sh`)

## Credits

- [redroid](https://github.com/remote-android/redroid-doc) - Android container
- [redroid-script](https://github.com/ayasa520/redroid-script) - GApps/Magisk/NDK automation
- [Frida](https://frida.re/) - Dynamic instrumentation
- [MindTheGapps](https://wiki.lineageos.org/gapps) - Google Apps package

## License

MIT
