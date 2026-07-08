import os
import shutil
from stuff.general import General
from tools.helper import bcolors, get_download_dir, print_color, run

class Ndk(General):
    download_loc = get_download_dir()
    copy_dir = "./ndk"
    dl_link = "https://github.com/nicololau/nicololau/releases/download/v0/vendor_google_proprietary_ndk_translation-prebuilt.zip"
    dl_file_name = os.path.join(download_loc, "libndktranslation.zip")
    extract_to = "/tmp/libndkunpack"
    act_md5 = "c9572672d1045594448068079b34c350"

    # Fallback URL if primary fails
    dl_link_fallback = "https://github.com/nicololau/nicololau/releases/download/v0/vendor_google_proprietary_ndk_translation-prebuilt.zip"

    def download(self):
        print_color("Downloading libndk translation...", bcolors.GREEN)
        # Try primary URL first, fallback if needed
        try:
            super().download()
        except Exception:
            self.dl_link = self.dl_link_fallback
            super().download()

    def copy(self):
        if os.path.exists(self.copy_dir):
            shutil.rmtree(self.copy_dir)
        run(["chmod", "+x", self.extract_to, "-R"])

        print_color("Copying libndk library files...", bcolors.GREEN)
        # Find the actual prebuilts dir (name varies by zip)
        for entry in os.listdir(self.extract_to):
            prebuilts = os.path.join(self.extract_to, entry, "prebuilts")
            if os.path.isdir(prebuilts):
                shutil.copytree(prebuilts, os.path.join(self.copy_dir, "system"), dirs_exist_ok=True)
                break
        else:
            # Direct prebuilts dir
            prebuilts = os.path.join(self.extract_to, "prebuilts")
            if os.path.isdir(prebuilts):
                shutil.copytree(prebuilts, os.path.join(self.copy_dir, "system"), dirs_exist_ok=True)

        init_path = os.path.join(self.copy_dir, "system", "etc", "init", "ndk_translation.rc")
        if os.path.exists(init_path):
            os.chmod(init_path, 0o644)
