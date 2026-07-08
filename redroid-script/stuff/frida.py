import os
import shutil
import platform
from stuff.general import General
from tools.helper import bcolors, get_download_dir, print_color, run

class Frida(General):
    FRIDA_VERSION = "17.15.3"
    download_loc = get_download_dir()
    copy_dir = "./frida"
    
    arch_map = {"x86_64": "x86_64", "x86": "x86", "arm64": "arm64", "arm": "arm"}
    machine = platform.machine()
    if machine == "x86_64":
        arch = "x86_64"
    elif machine == "aarch64":
        arch = "arm64"
    else:
        arch = "x86_64"
    
    dl_link = f"https://github.com/frida/frida/releases/download/{FRIDA_VERSION}/frida-server-{FRIDA_VERSION}-android-{arch}.xz"
    dl_file_name = os.path.join(download_loc, "frida-server.xz")
    extract_to = "/tmp/frida_extract"
    act_md5 = ""  # Skip MD5 check for frida

    def download(self):
        print_color(f"Downloading frida-server {self.FRIDA_VERSION} ({self.arch})...", bcolors.GREEN)
        import urllib.request
        os.makedirs(self.download_loc, exist_ok=True)
        if not os.path.exists(self.dl_file_name):
            urllib.request.urlretrieve(self.dl_link, self.dl_file_name)
    
    def extract(self):
        print_color("Extracting frida-server...", bcolors.GREEN)
        import lzma
        os.makedirs(self.extract_to, exist_ok=True)
        out_path = os.path.join(self.extract_to, "frida-server")
        with lzma.open(self.dl_file_name) as f_in:
            with open(out_path, 'wb') as f_out:
                f_out.write(f_in.read())
        os.chmod(out_path, 0o755)

    def copy(self):
        if os.path.exists(self.copy_dir):
            shutil.rmtree(self.copy_dir)
        os.makedirs(os.path.join(self.copy_dir, "data", "local", "tmp"), exist_ok=True)
        # Rename to 'fs' to avoid Play Integrity detection
        shutil.copy(
            os.path.join(self.extract_to, "frida-server"),
            os.path.join(self.copy_dir, "data", "local", "tmp", "fs")
        )
        os.chmod(os.path.join(self.copy_dir, "data", "local", "tmp", "fs"), 0o755)
        print_color("Frida server will be at /data/local/tmp/fs", bcolors.GREEN)
