import re
from typing import Tuple, Optional
from core.adb_wrapper import adb_wrapper
from core.device_manager import device_manager

class WirelessManager:
    def __init__(self):
        self.adb = adb_wrapper

    def enable_tcpip(self, port: int = 5555, serial: Optional[str] = None) -> Tuple[int, str]:
        """Switches device from USB to TCP/IP mode."""
        dev_serial = serial or (device_manager.selected_device.serial if device_manager.selected_device else None)
        if not dev_serial:
            return -1, "No device connected."

        c, o, e = self.adb.run(["tcpip", str(port)], device_serial=dev_serial)
        output = (o + "\n" + e).strip()
        return c, output

    def connect(self, host: str, port: int = 5555) -> Tuple[int, str]:
        """Connects to a wireless ADB target (e.g. 192.168.1.50:5555)."""
        target = f"{host.strip()}:{port}"
        c, o, e = self.adb.run(["connect", target], timeout=15)
        output = (o + "\n" + e).strip()
        return c, output

    def disconnect(self, host: str, port: int = 5555) -> Tuple[int, str]:
        """Disconnects a wireless ADB target."""
        target = f"{host.strip()}:{port}"
        c, o, e = self.adb.run(["disconnect", target], timeout=10)
        output = (o + "\n" + e).strip()
        return c, output

    def pair(self, host: str, port: int, code: str) -> Tuple[int, str]:
        """Pairs with Android 11+ device using pairing code."""
        target = f"{host.strip()}:{port}"
        # adb pair <host>:<port> <code>
        c, o, e = self.adb.run(["pair", target, code.strip()], timeout=20)
        output = (o + "\n" + e).strip()
        return c, output

wireless_manager = WirelessManager()
