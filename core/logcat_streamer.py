import re
import threading
from typing import List, Optional, Callable
from collections import deque
from core.adb_wrapper import adb_wrapper
from core.device_manager import device_manager

LOG_LEVELS = {"V": 1, "D": 2, "I": 3, "W": 4, "E": 5, "F": 6}

class LogEntry:
    def __init__(self, raw: str, level: str = "I", tag: str = "", pid: str = "", message: str = "", timestamp: str = ""):
        self.raw = raw
        self.level = level
        self.tag = tag
        self.pid = pid
        self.message = message
        self.timestamp = timestamp

    @property
    def level_name(self) -> str:
        return {"V": "Verbose", "D": "Debug", "I": "Info", "W": "Warn", "E": "Error", "F": "Fatal"}.get(self.level, "Info")


class LogcatStreamer:
    def __init__(self, max_entries: int = 2500):
        self.adb = adb_wrapper
        self.max_entries = max_entries
        self.logs: deque = deque(maxlen=max_entries)
        self.is_running = False
        self.is_paused = False
        self._stop_fn: Optional[Callable[[], None]] = None
        self._on_entry_callbacks: List[Callable[[LogEntry], None]] = []

        # Standard logcat time format regex: "09-29 16:30:12.345 I/ActivityManager( 1234): message"
        self._regex_log = re.compile(r'^(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})\s+([VDIWEF])/([^(\s]+)(?:\(\s*(\d+)\))?:\s*(.*)$')

    def add_listener(self, callback: Callable[[LogEntry], None]):
        self._on_entry_callbacks.append(callback)

    def remove_listener(self, callback: Callable[[LogEntry], None]):
        if callback in self._on_entry_callbacks:
            self._on_entry_callbacks.remove(callback)

    def start(self, serial: Optional[str] = None):
        if self.is_running:
            return

        dev_serial = serial or (device_manager.selected_device.serial if device_manager.selected_device else None)
        if not dev_serial:
            return

        self.is_running = True
        self.is_paused = False

        def _on_line(line: str):
            if self.is_paused:
                return

            line = line.strip()
            if not line or line.startswith("--------- beginning of"):
                return

            match = self._regex_log.match(line)
            if match:
                ts, lvl, tag, pid, msg = match.groups()
                entry = LogEntry(raw=line, level=lvl, tag=tag.strip(), pid=pid or "", message=msg, timestamp=ts)
            else:
                entry = LogEntry(raw=line, level="I", tag="System", pid="", message=line, timestamp="")

            self.logs.append(entry)
            for cb in self._on_entry_callbacks:
                try:
                    cb(entry)
                except Exception:
                    pass

        def _on_finish(code: int):
            self.is_running = False
            self._stop_fn = None

        self._stop_fn = self.adb.raw_stream(
            args=["logcat", "-v", "time"],
            device_serial=dev_serial,
            on_chunk=_on_line,
            on_finish=_on_finish
        )

    def stop(self):
        if self._stop_fn:
            self._stop_fn()
            self._stop_fn = None
        self.is_running = False

    def toggle_pause(self) -> bool:
        self.is_paused = not self.is_paused
        return self.is_paused

    def clear(self, serial: Optional[str] = None):
        self.logs.clear()
        dev_serial = serial or (device_manager.selected_device.serial if device_manager.selected_device else None)
        if dev_serial:
            self.adb.run(["logcat", "-c"], device_serial=dev_serial)

    def export(self, filepath: str) -> bool:
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                for entry in self.logs:
                    f.write(entry.raw + "\n")
            return True
        except Exception:
            return False

logcat_streamer = LogcatStreamer()
