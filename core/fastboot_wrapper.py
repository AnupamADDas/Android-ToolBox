import os
import subprocess
import threading
from typing import List, Optional, Tuple, Callable
from core.adb_locator import locator

class FastbootWrapper:
    def __init__(self):
        self.locator = locator

    def _get_fastboot(self) -> str:
        fb_path = self.locator.get_fastboot()
        if not fb_path:
            raise FileNotFoundError("Fastboot executable not found.")
        return fb_path

    def run(self, args: List[str], device_serial: Optional[str] = None, timeout: Optional[int] = 120) -> Tuple[int, str, str]:
        fb = self._get_fastboot()
        cmd = [fb]
        if device_serial:
            cmd.extend(["-s", device_serial])
        cmd.extend(args)

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                timeout=timeout
            )
            # Fastboot often writes standard output to stderr
            return res.returncode, res.stdout, res.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"Fastboot timed out after {timeout} seconds."
        except Exception as e:
            return -1, "", str(e)

    def flash(self, partition: str, image_path: str, device_serial: Optional[str] = None, on_output: Optional[Callable[[str], None]] = None) -> Tuple[int, str]:
        """Flash a partition image with non-blocking execution or output streaming."""
        if not os.path.isfile(image_path):
            return -1, f"Image file not found: {image_path}"

        fb = self._get_fastboot()
        cmd = [fb]
        if device_serial:
            cmd.extend(["-s", device_serial])
        cmd.extend(["flash", partition, image_path])

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )

            full_log = []
            for line in iter(process.stdout.readline, ''):
                full_log.append(line)
                if on_output:
                    on_output(line)

            process.wait()
            return process.returncode, "".join(full_log)
        except Exception as e:
            return -1, str(e)

    def reboot(self, target: str = "system", device_serial: Optional[str] = None) -> Tuple[int, str, str]:
        if target == "bootloader":
            return self.run(["reboot", "bootloader"], device_serial=device_serial)
        elif target == "recovery":
            return self.run(["reboot", "recovery"], device_serial=device_serial)
        elif target == "fastboot":
            return self.run(["reboot", "fastboot"], device_serial=device_serial)
        else:
            return self.run(["reboot"], device_serial=device_serial)

    def get_var(self, variable: str = "all", device_serial: Optional[str] = None) -> Tuple[int, str]:
        code, out, err = self.run(["getvar", variable], device_serial=device_serial)
        # Fastboot outputs getvar to stderr usually
        combined = (out + "\n" + err).strip()
        return code, combined

fastboot_wrapper = FastbootWrapper()
