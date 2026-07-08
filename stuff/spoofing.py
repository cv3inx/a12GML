import os
import shutil
import json
from tools.helper import bcolors, print_color

class DeviceSpoofing:
    """Adds device spoofing database and scripts to the image"""
    copy_dir = "./spoofing"
    
    def install(self):
        print_color("Adding device spoofing support...", bcolors.GREEN)
        self.copy()
    
    def copy(self):
        if os.path.exists(self.copy_dir):
            shutil.rmtree(self.copy_dir)
        
        # Create directory structure
        spoof_dir = os.path.join(self.copy_dir, "data", "local", "tmp", "spoofing")
        os.makedirs(spoof_dir, exist_ok=True)
        
        # Copy TAC database from our spoofdb
        src_db = os.path.join(os.path.dirname(os.path.dirname(__file__)), "spoofdb", "tac_database.json")
        if os.path.exists(src_db):
            shutil.copy(src_db, os.path.join(spoof_dir, "tac_database.json"))
        
        # Copy gen_identity.py
        src_gen = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts", "gen_identity.py")
        if os.path.exists(src_gen):
            shutil.copy(src_gen, os.path.join(spoof_dir, "gen_identity.py"))
        
        # Create auto-spoof init script that runs on boot
        init_dir = os.path.join(self.copy_dir, "system", "etc", "init")
        os.makedirs(init_dir, exist_ok=True)
        
        spoof_rc = """
on property:sys.boot_completed=1
    exec u:r:su:s0 root root -- /system/bin/sh -c "python3 /data/local/tmp/spoofing/apply_spoof.sh"
"""
        # Create the apply script (shell-based, no python dependency on device)
        apply_script = """#!/system/bin/sh
# Auto-apply device spoof on boot
SPOOF_DIR=/data/local/tmp/spoofing
MAGISK=/sbin/magisk

if [ ! -x "$MAGISK" ]; then
    MAGISK=$(which magisk 2>/dev/null)
fi

if [ -z "$MAGISK" ] || [ ! -x "$MAGISK" ]; then
    exit 0
fi

RP="$MAGISK resetprop"

# Read last applied spoof or generate new
if [ -f "$SPOOF_DIR/current_spoof.sh" ]; then
    . "$SPOOF_DIR/current_spoof.sh"
fi
"""
        with open(os.path.join(spoof_dir, "apply_spoof.sh"), 'w') as f:
            f.write(apply_script)
        os.chmod(os.path.join(spoof_dir, "apply_spoof.sh"), 0o755)
        
        print_color("Device spoofing database and scripts added", bcolors.GREEN)
