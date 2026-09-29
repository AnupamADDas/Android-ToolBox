import io
import os
import shutil
import subprocess
from typing import Optional, Tuple
from PIL import Image
from core.adb_wrapper import adb_wrapper
from core.device_manager import device_manager

class ScreenTools:
    def __init__(self):
        self.adb = adb_wrapper

    def capture_screenshot(self, serial: Optional[str] = None) -> Tuple[Optional[Image.Image], str]:
        """Captures device screen and returns a PIL Image."""
        dev_serial = serial or (device_manager.selected_device.serial if device_manager.selected_device else None)
        if not dev_serial:
            return None, "No device connected."

        try:
            adb_bin = self.adb.locator.get_adb()
            cmd = [adb_bin]
            if dev_serial:
                cmd.extend(["-s", dev_serial])
            cmd.extend(["exec-out", "screencap", "-p"])

            res = subprocess.run(
                cmd,
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                timeout=15
            )

            if res.returncode == 0 and res.stdout:
                # Replace Windows CRLF translation in binary stream if needed
                png_data = res.stdout.replace(b'\r\n', b'\n')
                try:
                    img = Image.open(io.BytesIO(png_data))
                    return img, "Success"
                except Exception:
                    # Fallback to direct raw bytes
                    img = Image.open(io.BytesIO(res.stdout))
                    return img, "Success"

            return None, f"Screenshot failed with code {res.returncode}"
        except Exception as e:
            return None, f"Screenshot error: {str(e)}"

    def is_scrcpy_available(self) -> bool:
        return shutil.which("scrcpy") is not None

    def launch_scrcpy(self, serial: Optional[str] = None, stay_awake: bool = True, turn_screen_off: bool = False) -> Tuple[int, str]:
        if not self.is_scrcpy_available():
            return -1, "scrcpy not found in PATH. Please install scrcpy for screen mirroring."

        dev_serial = serial or (device_manager.selected_device.serial if device_manager.selected_device else None)
        cmd = ["scrcpy"]
        if dev_serial:
            cmd.extend(["-s", dev_serial])
        if stay_awake:
            cmd.append("--stay-awake")
        if turn_screen_off:
            cmd.append("--turn-screen-off")

        try:
            subprocess.Popen(cmd)
            return 0, "Launched scrcpy."
        except Exception as e:
            return -1, str(e)

screen_tools = ScreenTools()
