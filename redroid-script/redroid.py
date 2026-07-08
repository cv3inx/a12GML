#!/usr/bin/env python3
"""
Redroid GML Builder - Fork of ayasa520/redroid-script
Extended with: Android 12-14 support, Frida, Device Spoofing, removed version gates

Usage:
    python3 redroid.py -a 12.0.0 -mtg -m -n -f -s    # Full build
    python3 redroid.py -a 14.0.0 -mtg -m -f           # Android 14 + GApps + Magisk + Frida
"""

import argparse
import subprocess
import os
import sys

from stuff.gapps import Gapps
from stuff.litegapps import LiteGapps
from stuff.magisk import Magisk
from stuff.mindthegapps import MindTheGapps
from stuff.ndk import Ndk
from stuff.houdini import Houdini
from stuff.houdini_hack import Houdini_Hack
from stuff.widevine import Widevine
from stuff.frida import Frida
from stuff.spoofing import DeviceSpoofing
import tools.helper as helper


def main():
    dockerfile = ""
    tags = []
    
    parser = argparse.ArgumentParser(
        description="Redroid GML Builder - Android emulator image with root, GApps, ARM translation, Frida & spoofing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -a 12.0.0 -mtg -m -n -f -s     Full A12 build (recommended)
  %(prog)s -a 14.0.0 -mtg -m -f            A14 + GApps + Magisk + Frida  
  %(prog)s -a 11.0.0 -g -m -n -f -s -w     Everything on A11
        """)
    
    parser.add_argument('-a', '--android-version', dest='android',
                        default='12.0.0',
                        choices=['14.0.0', '13.0.0', '12.0.0', '12.0.0_64only', '11.0.0', '10.0.0', '9.0.0'],
                        help='Android version (default: 12.0.0)')
    
    # GApps options
    gapps_group = parser.add_mutually_exclusive_group()
    gapps_group.add_argument('-g', '--install-gapps', dest='gapps', action='store_true',
                             help='Install OpenGapps (Android 11 only)')
    gapps_group.add_argument('-lg', '--install-litegapps', dest='litegapps', action='store_true',
                             help='Install LiteGapps')
    gapps_group.add_argument('-mtg', '--install-mindthegapps', dest='mindthegapps', action='store_true',
                             help='Install MindTheGapps (recommended, supports A12-15)')
    
    # ARM translation
    arm_group = parser.add_mutually_exclusive_group()
    arm_group.add_argument('-n', '--install-ndk-translation', dest='ndk', action='store_true',
                           help='Install libndk ARM translation (recommended for AMD)')
    arm_group.add_argument('-i', '--install-houdini', dest='houdini', action='store_true',
                           help='Install houdini ARM translation (Intel only)')
    
    # Root & security
    parser.add_argument('-m', '--install-magisk', dest='magisk', action='store_true',
                        help='Install Magisk (systemless root)')
    parser.add_argument('-f', '--install-frida', dest='frida', action='store_true',
                        help='Install Frida server (renamed to avoid detection)')
    
    # Extras
    parser.add_argument('-s', '--device-spoofing', dest='spoofing', action='store_true',
                        help='Add device spoofing (112 real devices, 547 TAC codes)')
    parser.add_argument('-w', '--install-widevine', dest='widevine', action='store_true',
                        help='Install Widevine DRM (L3)')
    
    # Docker
    parser.add_argument('-c', '--container', dest='container', default='docker',
                        choices=['docker', 'podman'], help='Container runtime')

    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"  Redroid GML Builder")
    print(f"  Android {args.android} | Arch: {helper.host()[0]}")
    print(f"{'='*60}\n")

    dockerfile = f"FROM redroid/redroid:{args.android}-latest\n"
    tags.append(args.android)

    # === GApps ===
    if args.gapps:
        if args.android in ["11.0.0"]:
            Gapps().install()
            dockerfile += "COPY gapps /\n"
            tags.append("gapps")
        else:
            helper.print_color("WARNING: OpenGapps only supports 11.0.0. Use -mtg for MindTheGapps.", helper.bcolors.YELLOW)
    
    if args.litegapps:
        LiteGapps(args.android).install()
        dockerfile += "COPY litegapps /\n"
        tags.append("litegapps")
    
    if args.mindthegapps:
        if args.android in MindTheGapps.dl_links:
            MindTheGapps(args.android).install()
            dockerfile += "COPY mindthegapps /\n"
            tags.append("gapps")
        else:
            helper.print_color(f"WARNING: MindTheGapps not available for {args.android}", helper.bcolors.YELLOW)

    # === ARM Translation ===
    if args.ndk:
        arch = helper.host()[0]
        if arch in ("x86", "x86_64"):
            # Removed version gate - NDK works on 11-14
            Ndk().install()
            dockerfile += "COPY ndk /\n"
            tags.append("ndk")
        else:
            helper.print_color("WARNING: NDK translation only needed on x86/x86_64 hosts", helper.bcolors.YELLOW)
    
    if args.houdini:
        arch = helper.host()[0]
        if arch in ("x86", "x86_64"):
            Houdini(args.android).install()
            if args.android != "8.1.0":
                Houdini_Hack(args.android).install()
            dockerfile += "COPY houdini /\n"
            tags.append("houdini")

    # === Magisk ===
    if args.magisk:
        Magisk().install()
        dockerfile += "COPY magisk /\n"
        tags.append("magisk")

    # === Frida ===
    if args.frida:
        Frida().install()
        dockerfile += "COPY frida /\n"
        tags.append("frida")

    # === Device Spoofing ===
    if args.spoofing:
        DeviceSpoofing().install()
        dockerfile += "COPY spoofing /\n"
        tags.append("spoof")

    # === Widevine ===
    if args.widevine:
        Widevine(args.android).install()
        dockerfile += "COPY widevine /\n"
        tags.append("widevine")

    # === Build Docker Image ===
    print(f"\n{'='*60}")
    print(f"Dockerfile:\n{dockerfile}")
    
    with open("./Dockerfile", "w") as f:
        f.write(dockerfile)
    
    new_image_name = "redroid/redroid:" + "_".join(tags)
    print(f"Building: {new_image_name}")
    print(f"{'='*60}\n")
    
    result = subprocess.run([args.container, "build", "-t", new_image_name, "."])
    
    if result.returncode == 0:
        helper.print_color(f"\n[✓] Successfully built: {new_image_name}", helper.bcolors.GREEN)
        print(f"\nRun with:")
        print(f"  docker run -d --privileged -p 5555:5555 {new_image_name} \\")
        print(f"    androidboot.redroid_gpu_mode=guest \\")
        if args.ndk:
            print(f"    ro.product.cpu.abilist=x86_64,arm64-v8a,x86,armeabi-v7a,armeabi \\")
            print(f"    ro.product.cpu.abilist64=x86_64,arm64-v8a \\")
            print(f"    ro.product.cpu.abilist32=x86,armeabi-v7a,armeabi \\")
            print(f"    ro.dalvik.vm.isa.arm=x86 \\")
            print(f"    ro.dalvik.vm.isa.arm64=x86_64 \\")
            print(f"    ro.enable.native.bridge.exec=1 \\")
            print(f"    ro.dalvik.vm.native.bridge=libndk_translation.so")
        if args.frida:
            print(f"\nFrida: adb shell /data/local/tmp/fs -D")
        if args.spoofing:
            print(f"Spoof: scripts/spoof_device.sh 5555 random")
    else:
        helper.print_color(f"\n[✗] Build failed!", helper.bcolors.RED)
        sys.exit(1)


if __name__ == "__main__":
    main()
