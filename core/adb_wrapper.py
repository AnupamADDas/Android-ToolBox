import os
import subprocess
import threading
from typing import List, Optional, Tuple, Callable
from core.adb_locator import locator

class ADBWrapper:
    def __init__(self):
        self.locator = locator

    def _get_adb(self) -> str:
        adb_path = self.locator.get_adb()
        if not adb_path:
            raise FileNotFoundError("ADB executable not found. Please install Android Platform Tools.")
        return adb_path

    def run(self, args: List[str], device_serial: Optional[str] = None, timeout: Optional[int] = 60) -> Tuple[int, str, str]:
        """Run an adb command synchronously."""
        adb = self._get_adb()
        cmd = [adb]
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
            return res.returncode, res.stdout, res.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"Command timed out after {timeout} seconds."
        except Exception as e:
            return -1, "", str(e)

    def shell(self, command: str, device_serial: Optional[str] = None, timeout: Optional[int] = 60) -> Tuple[int, str, str]:
        """Execute a shell command on the target device."""
        return self.run(["shell", command], device_serial=device_serial, timeout=timeout)

    def raw_stream(self, args: List[str], device_serial: Optional[str], on_chunk: Callable[[str], None], on_finish: Optional[Callable[[int], None]] = None):
        """
        Stream command output line by line in a background thread.
        Returns a callable to terminate the stream.
        """
        adb = self._get_adb()
        cmd = [adb]
        if device_serial:
            cmd.extend(["-s", device_serial])
        cmd.extend(args)

        process = None
        stop_event = threading.Event()

        def _worker():
            nonlocal process
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

                while not stop_event.is_set():
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        on_chunk(line)

                returncode = process.wait() if process else 0
                if on_finish:
                    on_finish(returncode)
            except Exception as e:
                on_chunk(f"[Error: {e}]\n")
                if on_finish:
                    on_finish(-1)

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

        def stop():
            stop_event.set()
            if process and process.poll() is None:
                try:
                    process.terminate()
                except Exception:
                    pass

        return stop

    def start_server(self) -> Tuple[int, str, str]:
        return self.run(["start-server"])

    def kill_server(self) -> Tuple[int, str, str]:
        return self.run(["kill-server"])

    def restart_server(self) -> Tuple[int, str, str]:
        self.kill_server()
        return self.start_server()

adb_wrapper = ADBWrapper()
