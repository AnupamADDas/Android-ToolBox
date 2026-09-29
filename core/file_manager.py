import re
import os
from typing import List, Optional, Tuple
from core.adb_wrapper import adb_wrapper
from core.device_manager import device_manager
from utils.file_utils import sanitize_remote_path, format_size

class RemoteFile:
    def __init__(self, name: str, path: str, is_dir: bool = False, size: int = 0, permissions: str = "", date_str: str = ""):
        self.name = name
        self.path = path
        self.is_dir = is_dir
        self.size = size
        self.permissions = permissions
        self.date_str = date_str

    @property
    def formatted_size(self) -> str:
        if self.is_dir:
            return "<DIR>"
        return format_size(self.size)

    def __repr__(self):
        return f"<RemoteFile {self.name} is_dir={self.is_dir} size={self.size}>"


class FileManager:
    def __init__(self):
        self.adb = adb_wrapper

    def _get_serial(self, serial: Optional[str] = None) -> Optional[str]:
        if serial:
            return serial
        if device_manager.selected_device:
            return device_manager.selected_device.serial
        return None

    def list_directory(self, remote_path: str = "/sdcard", serial: Optional[str] = None) -> List[RemoteFile]:
        dev_serial = self._get_serial(serial)
        if not dev_serial:
            return []

        clean_path = sanitize_remote_path(remote_path)
        # ls -la gives permissions, owner, group, size, date, time, name
        cmd = f"ls -la \"{clean_path}\""
        code, out, _ = self.adb.shell(cmd, device_serial=dev_serial)
        if code != 0:
            return []

        files: List[RemoteFile] = []
        for line in out.splitlines():
            line = line.strip()
            if not line or line.startswith("total "):
                continue

            parts = line.split(maxsplit=7)
            if len(parts) >= 8:
                perms, _, _, _, size_str, date_part, time_part, name = parts
            elif len(parts) >= 6:
                # Some busybox / recovery versions have fewer columns
                perms = parts[0]
                size_str = parts[3] if len(parts) > 3 and parts[3].isdigit() else "0"
                name = parts[-1]
                date_part = ""
                time_part = ""
            else:
                continue

            # Handle symlinks e.g. "sdcard -> /storage/emulated/0"
            if " -> " in name:
                name = name.split(" -> ")[0].strip()

            if name in [".", ".."]:
                continue

            is_dir = perms.startswith("d") or perms.startswith("l")
            try:
                size_int = int(size_str)
            except Exception:
                size_int = 0

            item_path = clean_path.rstrip("/") + "/" + name
            dt = f"{date_part} {time_part}".strip()
            files.append(RemoteFile(name=name, path=item_path, is_dir=is_dir, size=size_int, permissions=perms, date_str=dt))

        # Sort: directories first, then alphabetically
        files.sort(key=lambda f: (not f.is_dir, f.name.lower()))
        return files

    def push(self, local_path: str, remote_path: str, serial: Optional[str] = None) -> Tuple[int, str]:
        dev_serial = self._get_serial(serial)
        if not dev_serial:
            return -1, "No device connected."
        if not os.path.exists(local_path):
            return -1, f"Local path not found: {local_path}"

        clean_remote = sanitize_remote_path(remote_path)
        c, o, e = self.adb.run(["push", local_path, clean_remote], device_serial=dev_serial, timeout=600)
        return c, (o + "\n" + e).strip()

    def pull(self, remote_path: str, local_destination: str, serial: Optional[str] = None) -> Tuple[int, str]:
        dev_serial = self._get_serial(serial)
        if not dev_serial:
            return -1, "No device connected."

        clean_remote = sanitize_remote_path(remote_path)
        c, o, e = self.adb.run(["pull", clean_remote, local_destination], device_serial=dev_serial, timeout=600)
        return c, (o + "\n" + e).strip()

    def delete(self, remote_path: str, is_dir: bool = False, serial: Optional[str] = None) -> Tuple[int, str]:
        dev_serial = self._get_serial(serial)
        if not dev_serial:
            return -1, "No device connected."

        clean_remote = sanitize_remote_path(remote_path)
        cmd = f"rm -rf \"{clean_remote}\"" if is_dir else f"rm -f \"{clean_remote}\""
        c, o, e = self.adb.shell(cmd, device_serial=dev_serial)
        return c, (o + "\n" + e).strip()

    def mkdir(self, remote_path: str, serial: Optional[str] = None) -> Tuple[int, str]:
        dev_serial = self._get_serial(serial)
        if not dev_serial:
            return -1, "No device connected."

        clean_remote = sanitize_remote_path(remote_path)
        c, o, e = self.adb.shell(f"mkdir -p \"{clean_remote}\"", device_serial=dev_serial)
        return c, (o + "\n" + e).strip()

file_manager = FileManager()
