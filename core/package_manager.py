import os
import re
from typing import List, Dict, Optional, Tuple, Any
from core.adb_wrapper import adb_wrapper
from core.device_manager import device_manager

class AppPackage:
    def __init__(self, package_id: str, apk_path: str = "", is_system: bool = False, is_enabled: bool = True):
        self.package_id = package_id
        self.apk_path = apk_path
        self.is_system = is_system
        self.is_enabled = is_enabled

    @property
    def display_name(self) -> str:
        # Generate friendly name from package ID if possible
        parts = self.package_id.split(".")
        return parts[-1].capitalize() if parts else self.package_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "package_id": self.package_id,
            "apk_path": self.apk_path,
            "is_system": self.is_system,
            "is_enabled": self.is_enabled,
            "name": self.display_name
        }


class PackageManager:
    def __init__(self):
        self.adb = adb_wrapper

    def _get_serial(self, serial: Optional[str] = None) -> Optional[str]:
        if serial:
            return serial
        if device_manager.selected_device:
            return device_manager.selected_device.serial
        return None

    def list_packages(self, filter_type: str = "3rd_party", serial: Optional[str] = None) -> List[AppPackage]:
        """
        filter_type: 'all', '3rd_party', 'system', 'disabled'
        """
        dev_serial = self._get_serial(serial)
        if not dev_serial:
            return []

        # Flags:
        # -3: 3rd party
        # -s: system
        # -d: disabled
        flag = "-3"
        if filter_type == "all":
            flag = ""
        elif filter_type == "system":
            flag = "-s"
        elif filter_type == "disabled":
            flag = "-d"

        cmd = f"pm list packages -f {flag}".strip()
        code, out, _ = self.adb.shell(cmd, device_serial=dev_serial)
        if code != 0:
            return []

        results: List[AppPackage] = []
        for line in out.splitlines():
            line = line.strip()
            if not line.startswith("package:"):
                continue
            # Format is package:/path/to/apk=com.example.id
            content = line[8:]
            if "=" in content:
                apk_path, pkg_id = content.rsplit("=", 1)
                is_sys = apk_path.startswith("/system") or apk_path.startswith("/product") or apk_path.startswith("/vendor")
                results.append(AppPackage(package_id=pkg_id, apk_path=apk_path, is_system=is_sys))

        # Sort alphabetically by package_id
        results.sort(key=lambda x: x.package_id.lower())
        return results

    def install_apk(self, apk_path: str, reinstall: bool = True, grant_permissions: bool = True,
                    downgrade: bool = False, serial: Optional[str] = None) -> Tuple[int, str]:
        dev_serial = self._get_serial(serial)
        if not dev_serial:
            return -1, "No device connected."
        if not os.path.isfile(apk_path):
            return -1, f"APK file not found: {apk_path}"

        args = ["install"]
        if reinstall:
            args.append("-r")
        if grant_permissions:
            args.append("-g")
        if downgrade:
            args.append("-d")
        args.append(apk_path)

        code, out, err = self.adb.run(args, device_serial=dev_serial, timeout=180)
        output = (out + "\n" + err).strip()
        return code, output

    def uninstall(self, package_id: str, keep_data_debloat: bool = False, serial: Optional[str] = None) -> Tuple[int, str]:
        dev_serial = self._get_serial(serial)
        if not dev_serial:
            return -1, "No device connected."

        if keep_data_debloat:
            # Debloat system app for user 0
            code, out, err = self.adb.shell(f"pm uninstall -k --user 0 {package_id}", device_serial=dev_serial)
        else:
            code, out, err = self.adb.shell(f"pm uninstall {package_id}", device_serial=dev_serial)

        output = (out + "\n" + err).strip()
        return code, output

    def set_enabled(self, package_id: str, enable: bool = True, serial: Optional[str] = None) -> Tuple[int, str]:
        dev_serial = self._get_serial(serial)
        if not dev_serial:
            return -1, "No device connected."

        action = "enable" if enable else "disable-user --user 0"
        code, out, err = self.adb.shell(f"pm {action} {package_id}", device_serial=dev_serial)
        return code, (out + "\n" + err).strip()

    def clear_data(self, package_id: str, serial: Optional[str] = None) -> Tuple[int, str]:
        dev_serial = self._get_serial(serial)
        if not dev_serial:
            return -1, "No device connected."
        code, out, err = self.adb.shell(f"pm clear {package_id}", device_serial=dev_serial)
        return code, (out + "\n" + err).strip()

    def force_stop(self, package_id: str, serial: Optional[str] = None) -> Tuple[int, str]:
        dev_serial = self._get_serial(serial)
        if not dev_serial:
            return -1, "No device connected."
        code, out, err = self.adb.shell(f"am force-stop {package_id}", device_serial=dev_serial)
        return code, (out + "\n" + err).strip()

    def launch(self, package_id: str, serial: Optional[str] = None) -> Tuple[int, str]:
        dev_serial = self._get_serial(serial)
        if not dev_serial:
            return -1, "No device connected."
        code, out, err = self.adb.shell(f"monkey -p {package_id} -c android.intent.category.LAUNCHER 1", device_serial=dev_serial)
        return code, (out + "\n" + err).strip()

    def extract_apk(self, package_id: str, destination_dir: str, serial: Optional[str] = None) -> Tuple[int, str]:
        dev_serial = self._get_serial(serial)
        if not dev_serial:
            return -1, "No device connected."

        code, out, _ = self.adb.shell(f"pm path {package_id}", device_serial=dev_serial)
        if code != 0 or not out.strip():
            return -1, f"Failed to locate APK path for {package_id}"

        remote_apk = out.strip().splitlines()[0].replace("package:", "").strip()
        dest_file = os.path.join(destination_dir, f"{package_id}.apk")

        c_pull, o_pull, e_pull = self.adb.run(["pull", remote_apk, dest_file], device_serial=dev_serial, timeout=120)
        if c_pull == 0 and os.path.isfile(dest_file):
            return 0, f"Saved to: {dest_file}"
        return c_pull, (o_pull + "\n" + e_pull).strip()

package_manager = PackageManager()
