import os
import sys
import shutil
import subprocess
import json
import urllib.request
import zipfile
from typing import Optional, Tuple, Callable

SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".adb_toolbox_settings.json")
GOOGLE_PLATFORM_TOOLS_URL = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"

class BinaryLocator:
    def __init__(self):
        self.adb_path: Optional[str] = None
        self.fastboot_path: Optional[str] = None
        self.load_settings()
        self.auto_detect()

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    custom_adb = data.get("custom_adb_path")
                    if custom_adb and os.path.isfile(custom_adb):
                        self.adb_path = custom_adb
                    custom_fastboot = data.get("custom_fastboot_path")
                    if custom_fastboot and os.path.isfile(custom_fastboot):
                        self.fastboot_path = custom_fastboot
            except Exception:
                pass

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "custom_adb_path": self.adb_path,
                    "custom_fastboot_path": self.fastboot_path
                }, f, indent=2)
        except Exception:
            pass

    def auto_detect(self):
        """Locates adb and fastboot binaries, prioritizing bundled tools."""
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        android_home = os.environ.get("ANDROID_HOME", "")
        android_sdk_root = os.environ.get("ANDROID_SDK_ROOT", "")

        # Potential search locations in order of priority:
        search_dirs = []

        # 1. PyInstaller bundled temporary directory (when running packaged .exe)
        if hasattr(sys, "_MEIPASS"):
            search_dirs.append(os.path.join(sys._MEIPASS, "bin", "platform-tools"))

        # 2. Local app bin directory (when running directly from source/repo)
        app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        search_dirs.append(os.path.join(app_root, "bin", "platform-tools"))

        # 3. LocalAppData auto-downloaded cache
        if local_app_data:
            search_dirs.append(os.path.join(local_app_data, "AndroidToolbox", "platform-tools"))

        # 4. Standard Android SDK platform-tools locations
        if local_app_data:
            search_dirs.append(os.path.join(local_app_data, "Android", "Sdk", "platform-tools"))
        if android_home:
            search_dirs.append(os.path.join(android_home, "platform-tools"))
        if android_sdk_root:
            search_dirs.append(os.path.join(android_sdk_root, "platform-tools"))
        search_dirs.append(os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "Android", "platform-tools"))

        # Search prioritized folders
        for s_dir in search_dirs:
            if not s_dir or not os.path.isdir(s_dir):
                continue

            cand_adb = os.path.join(s_dir, "adb.exe" if os.name == "nt" else "adb")
            if not self.adb_path and os.path.isfile(cand_adb):
                self.adb_path = cand_adb

            cand_fastboot = os.path.join(s_dir, "fastboot.exe" if os.name == "nt" else "fastboot")
            if not self.fastboot_path and os.path.isfile(cand_fastboot):
                self.fastboot_path = cand_fastboot

            if self.adb_path and self.fastboot_path:
                return

        # 5. Fallback: Search in system PATH
        if not self.adb_path:
            which_adb = shutil.which("adb")
            if which_adb and os.path.isfile(which_adb):
                self.adb_path = which_adb

        if not self.fastboot_path:
            which_fastboot = shutil.which("fastboot")
            if which_fastboot and os.path.isfile(which_fastboot):
                self.fastboot_path = which_fastboot

    def download_platform_tools(self, on_progress: Optional[Callable[[float, str], None]] = None) -> Tuple[bool, str]:
        """Downloads official Google platform-tools if not found anywhere."""
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if not local_app_data:
            local_app_data = os.path.expanduser("~")

        dest_dir = os.path.join(local_app_data, "AndroidToolbox")
        os.makedirs(dest_dir, exist_ok=True)
        zip_path = os.path.join(dest_dir, "platform-tools.zip")

        try:
            if on_progress:
                on_progress(0.1, "Downloading official Google platform-tools...")

            def _reporthook(block_num, block_size, total_size):
                if total_size > 0 and on_progress:
                    pct = min(0.8, (block_num * block_size) / total_size * 0.8)
                    on_progress(pct, f"Downloading: {int(pct * 100)}%")

            urllib.request.urlretrieve(GOOGLE_PLATFORM_TOOLS_URL, zip_path, reporthook=_reporthook)

            if on_progress:
                on_progress(0.85, "Extracting binaries...")

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(dest_dir)

            try:
                os.remove(zip_path)
            except Exception:
                pass

            # Auto detect newly extracted tools
            self.auto_detect()
            if self.is_adb_ready():
                if on_progress:
                    on_progress(1.0, "Platform tools ready!")
                return True, "Platform tools downloaded successfully."
            else:
                return False, "Extraction completed but binaries were not found."

        except Exception as e:
            return False, f"Failed to download platform-tools: {str(e)}"

    def get_adb(self) -> Optional[str]:
        return self.adb_path

    def get_fastboot(self) -> Optional[str]:
        return self.fastboot_path

    def is_adb_ready(self) -> bool:
        return bool(self.adb_path and os.path.isfile(self.adb_path))

    def is_fastboot_ready(self) -> bool:
        return bool(self.fastboot_path and os.path.isfile(self.fastboot_path))

    def get_versions(self) -> Tuple[str, str]:
        adb_ver = "Not Found"
        fb_ver = "Not Found"

        if self.is_adb_ready():
            try:
                res = subprocess.run(
                    [self.adb_path, "version"],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                    timeout=5
                )
                if res.returncode == 0:
                    adb_ver = res.stdout.strip().splitlines()[0]
            except Exception:
                adb_ver = "Error checking"

        if self.is_fastboot_ready():
            try:
                res = subprocess.run(
                    [self.fastboot_path, "--version"],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                    timeout=5
                )
                if res.returncode == 0:
                    fb_ver = res.stdout.strip().splitlines()[0]
            except Exception:
                fb_ver = "Error checking"

        return adb_ver, fb_ver

locator = BinaryLocator()
