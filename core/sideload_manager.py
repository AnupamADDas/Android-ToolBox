import os
import re
import subprocess
import threading
from typing import Optional, Callable, Tuple
from core.adb_wrapper import adb_wrapper
from core.device_manager import device_manager
from utils.constants import MODE_SIDELOAD, MODE_RECOVERY

class SideloadManager:
    def __init__(self):
        self.adb = adb_wrapper
        self.is_flashing = False
        self._current_process: Optional[subprocess.Popen] = None

    def start_sideload(
        self,
        zip_path: str,
        on_progress: Callable[[float, str], None],
        on_finish: Callable[[int, str], None],
        serial: Optional[str] = None
    ):
        """
        Runs `adb sideload <zip_path>` in a background thread and streams progress.
        """
        if self.is_flashing:
            on_finish(-1, "A sideload operation is already in progress.")
            return

        if not os.path.isfile(zip_path):
            on_finish(-1, f"ZIP file does not exist: {zip_path}")
            return

        dev_serial = serial or (device_manager.selected_device.serial if device_manager.selected_device else None)
        if not dev_serial:
            on_finish(-1, "No device connected.")
            return

        self.is_flashing = True

        def _worker():
            try:
                adb_bin = self.adb.locator.get_adb()
                cmd = [adb_bin]
                if dev_serial:
                    cmd.extend(["-s", dev_serial])
                cmd.extend(["sideload", zip_path])

                self._current_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
                )

                full_output = []
                regex_percent = re.compile(r'\(~?(\d+)%\)')

                for line in iter(self._current_process.stdout.readline, ''):
                    full_output.append(line)
                    match = regex_percent.search(line)
                    if match:
                        pct = float(match.group(1)) / 100.0
                        on_progress(pct, line.strip())
                    elif "serving:" in line.lower():
                        on_progress(0.1, line.strip())
                    elif "Total xfer:" in line:
                        on_progress(1.0, line.strip())
                    else:
                        on_progress(-1.0, line.strip())

                self._current_process.wait()
                rc = self._current_process.returncode
                self.is_flashing = False
                self._current_process = None

                out_str = "".join(full_output)
                if rc == 0:
                    on_finish(0, "Sideload completed successfully.")
                else:
                    on_finish(rc, f"Sideload ended with status {rc}.\n{out_str}")

            except Exception as e:
                self.is_flashing = False
                self._current_process = None
                on_finish(-1, f"Error during sideload: {str(e)}")

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def cancel_sideload(self):
        if self._current_process and self._current_process.poll() is None:
            try:
                self._current_process.terminate()
            except Exception:
                pass
            self.is_flashing = False

    def pull_recovery_log(self, destination_dir: str, serial: Optional[str] = None) -> Tuple[int, str]:
        """Pulls /tmp/recovery.log from custom recovery."""
        dev_serial = serial or (device_manager.selected_device.serial if device_manager.selected_device else None)
        if not dev_serial:
            return -1, "No device connected."

        dest_file = os.path.join(destination_dir, "recovery.log")
        c, o, e = self.adb.run(["pull", "/tmp/recovery.log", dest_file], device_serial=dev_serial)
        if c == 0 and os.path.isfile(dest_file):
            return 0, f"Recovery log saved to: {dest_file}"
        return c, (o + "\n" + e).strip()

sideload_manager = SideloadManager()
