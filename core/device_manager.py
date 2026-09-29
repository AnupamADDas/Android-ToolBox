import re
import threading
import time
from typing import Dict, List, Optional, Callable, Any, Tuple
from core.adb_wrapper import adb_wrapper
from core.fastboot_wrapper import fastboot_wrapper
from utils.constants import (
    MODE_DEVICE, MODE_RECOVERY, MODE_SIDELOAD, MODE_FASTBOOT,
    MODE_UNAUTHORIZED, MODE_OFFLINE, MODE_UNKNOWN
)

class AndroidDevice:
    def __init__(self, serial: str, mode: str, model: str = "", product: str = ""):
        self.serial = serial
        self.mode = mode  # device, recovery, sideload, fastboot, unauthorized, offline
        self.model = model or serial
        self.product = product
        self.is_root = False
        self.details: Dict[str, Any] = {}

    @property
    def display_name(self) -> str:
        tag = {
            MODE_DEVICE: "🟢 [Device]",
            MODE_RECOVERY: "🟠 [Recovery]",
            MODE_SIDELOAD: "⚡ [Sideload]",
            MODE_FASTBOOT: "🔵 [Fastboot]",
            MODE_UNAUTHORIZED: "🔴 [Unauthorized]",
            MODE_OFFLINE: "⚪ [Offline]"
        }.get(self.mode, "⚪")

        name = self.model if self.model != self.serial else self.serial
        return f"{tag} {name} ({self.serial})"

    def __repr__(self):
        return f"<Device {self.serial} ({self.mode})>"


class DeviceManager:
    def __init__(self):
        self.adb = adb_wrapper
        self.fastboot = fastboot_wrapper
        self.devices: List[AndroidDevice] = []
        self.selected_device: Optional[AndroidDevice] = None
        self._listeners: List[Callable[[List[AndroidDevice]], None]] = []
        self._polling_thread: Optional[threading.Thread] = None
        self._stop_polling = threading.Event()

    def add_listener(self, listener: Callable[[List[AndroidDevice]], None]):
        self._listeners.append(listener)

    def start_monitoring(self, interval: float = 3.0):
        if self._polling_thread and self._polling_thread.is_alive():
            return
        self._stop_polling.clear()

        def _poll():
            while not self._stop_polling.is_set():
                self.refresh_devices()
                time.sleep(interval)

        self._polling_thread = threading.Thread(target=_poll, daemon=True)
        self._polling_thread.start()

    def stop_monitoring(self):
        self._stop_polling.set()

    def refresh_devices(self) -> List[AndroidDevice]:
        discovered: List[AndroidDevice] = []

        # 1. Check ADB devices
        if self.adb.locator.is_adb_ready():
            code, out, _ = self.adb.run(["devices", "-l"])
            if code == 0:
                lines = out.strip().splitlines()
                for line in lines[1:]:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split()
                    if len(parts) >= 2:
                        serial = parts[0]
                        mode = parts[1]
                        model = serial
                        product = ""
                        
                        # Extract model:xxx product:xxx
                        for part in parts[2:]:
                            if part.startswith("model:"):
                                model = part.split(":", 1)[1].replace("_", " ")
                            elif part.startswith("product:"):
                                product = part.split(":", 1)[1]

                        # Standardize mode
                        if mode == "device":
                            m = MODE_DEVICE
                        elif mode == "recovery":
                            m = MODE_RECOVERY
                        elif mode == "sideload":
                            m = MODE_SIDELOAD
                        elif mode == "unauthorized":
                            m = MODE_UNAUTHORIZED
                        elif mode == "offline":
                            m = MODE_OFFLINE
                        else:
                            m = MODE_UNKNOWN

                        discovered.append(AndroidDevice(serial=serial, mode=m, model=model, product=product))

        # 2. Check Fastboot devices
        if self.fastboot.locator.is_fastboot_ready():
            code, out, err = self.fastboot.run(["devices"])
            raw = (out + "\n" + err).strip()
            for line in raw.splitlines():
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) >= 2 and "fastboot" in parts[1].lower():
                    serial = parts[0]
                    # Check if already in list
                    if not any(d.serial == serial for d in discovered):
                        discovered.append(AndroidDevice(serial=serial, mode=MODE_FASTBOOT, model="Fastboot Device"))

        # Check if list changed
        old_serials = [f"{d.serial}:{d.mode}" for d in self.devices]
        new_serials = [f"{d.serial}:{d.mode}" for d in discovered]

        self.devices = discovered

        # Auto-update selected device
        if self.selected_device:
            match = next((d for d in discovered if d.serial == self.selected_device.serial), None)
            if match:
                self.selected_device = match
            else:
                self.selected_device = discovered[0] if discovered else None
        else:
            self.selected_device = discovered[0] if discovered else None

        if old_serials != new_serials:
            for listener in self._listeners:
                try:
                    listener(self.devices)
                except Exception:
                    pass

        return self.devices

    def select_device(self, serial: str) -> Optional[AndroidDevice]:
        for d in self.devices:
            if d.serial == serial:
                self.selected_device = d
                return d
        return None

    def get_device_info(self, device: Optional[AndroidDevice] = None) -> Dict[str, Any]:
        dev = device or self.selected_device
        if not dev:
            return {"error": "No device selected"}

        info: Dict[str, Any] = {
            "serial": dev.serial,
            "mode": dev.mode,
            "model": dev.model
        }

        if dev.mode == MODE_DEVICE:
            # Query getprop
            code, out, _ = self.adb.shell("getprop", device_serial=dev.serial)
            props = {}
            if code == 0:
                for match in re.finditer(r'\[(.*?)\]:\s*\[(.*?)\]', out):
                    props[match.group(1)] = match.group(2)

            info["brand"] = props.get("ro.product.brand", "Unknown")
            info["model"] = props.get("ro.product.model", dev.model)
            info["device_name"] = props.get("ro.product.device", "")
            info["android_version"] = props.get("ro.build.version.release", "Unknown")
            info["sdk_level"] = props.get("ro.build.version.sdk", "Unknown")
            info["security_patch"] = props.get("ro.build.version.security_patch", "Unknown")
            info["build_id"] = props.get("ro.build.display.id", props.get("ro.build.id", "Unknown"))
            info["cpu_abi"] = props.get("ro.product.cpu.abi", "Unknown")

            # Check screen resolution & density
            c_wm, out_wm, _ = self.adb.shell("wm size", device_serial=dev.serial)
            if c_wm == 0 and "Physical size:" in out_wm:
                info["resolution"] = out_wm.split("Physical size:")[-1].strip()
            else:
                info["resolution"] = "N/A"

            c_den, out_den, _ = self.adb.shell("wm density", device_serial=dev.serial)
            if c_den == 0 and "Physical density:" in out_den:
                info["density"] = out_den.split("Physical density:")[-1].strip() + " dpi"
            else:
                info["density"] = "N/A"

            # Battery info
            c_bat, out_bat, _ = self.adb.shell("dumpsys battery", device_serial=dev.serial)
            battery = {"level": "N/A", "status": "Unknown", "temperature": "N/A", "voltage": "N/A", "health": "Good"}
            if c_bat == 0:
                for line in out_bat.splitlines():
                    line = line.strip()
                    if line.startswith("level:"):
                        battery["level"] = line.split(":", 1)[1].strip() + "%"
                    elif line.startswith("status:"):
                        st_code = line.split(":", 1)[1].strip()
                        battery["status"] = {"2": "Charging", "3": "Discharging", "4": "Not charging", "5": "Full"}.get(st_code, st_code)
                    elif line.startswith("temperature:"):
                        try:
                            temp_val = float(line.split(":", 1)[1].strip()) / 10.0
                            battery["temperature"] = f"{temp_val:.1f} °C"
                        except Exception:
                            pass
                    elif line.startswith("voltage:"):
                        try:
                            volt_val = float(line.split(":", 1)[1].strip()) / 1000.0
                            battery["voltage"] = f"{volt_val:.2f} V"
                        except Exception:
                            pass
            info["battery"] = battery

            # Root check
            c_root, out_root, _ = self.adb.shell("su -c id", device_serial=dev.serial, timeout=3)
            dev.is_root = (c_root == 0 and "uid=0(root)" in out_root)
            info["is_root"] = dev.is_root

            # Wi-Fi IP
            c_ip, out_ip, _ = self.adb.shell("ip -f inet addr show wlan0", device_serial=dev.serial)
            ip_match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', out_ip)
            info["wifi_ip"] = ip_match.group(1) if ip_match else "Disconnected"

        elif dev.mode == MODE_RECOVERY:
            info["root_access"] = "Full Root (Recovery Default)"
            dev.is_root = True
            c_uname, out_uname, _ = self.adb.shell("uname -r", device_serial=dev.serial)
            info["kernel"] = out_uname.strip() if c_uname == 0 else "Unknown"
            
            # Check TWRP presence
            c_twrp, _, _ = self.adb.shell("test -f /sbin/twrp", device_serial=dev.serial)
            info["recovery_type"] = "TWRP / Custom Recovery" if c_twrp == 0 else "Custom Recovery"

        elif dev.mode == MODE_FASTBOOT:
            c_prod, out_prod = self.fastboot.get_var("product", device_serial=dev.serial)
            info["product"] = out_prod.split()[-1] if c_prod == 0 else "Fastboot"
            c_unlock, out_unlock = self.fastboot.get_var("unlocked", device_serial=dev.serial)
            info["unlocked"] = out_unlock.split()[-1] if c_unlock == 0 else "Unknown"

        dev.details = info
        return info

    def reboot(self, target: str = "system") -> Tuple[int, str]:
        dev = self.selected_device
        if not dev:
            return -1, "No device connected."

        if dev.mode == MODE_FASTBOOT:
            if target == "system":
                c, o, e = self.fastboot.reboot("system", dev.serial)
            elif target == "bootloader":
                c, o, e = self.fastboot.reboot("bootloader", dev.serial)
            elif target == "recovery":
                c, o, e = self.fastboot.reboot("recovery", dev.serial)
            elif target == "fastbootd":
                c, o, e = self.fastboot.reboot("fastboot", dev.serial)
            else:
                c, o, e = self.fastboot.reboot("system", dev.serial)
            return c, (o + "\n" + e).strip()

        # Normal or recovery mode
        if target == "system":
            c, o, e = self.adb.run(["reboot"], device_serial=dev.serial)
        elif target == "recovery":
            c, o, e = self.adb.run(["reboot", "recovery"], device_serial=dev.serial)
        elif target == "bootloader":
            c, o, e = self.adb.run(["reboot", "bootloader"], device_serial=dev.serial)
        elif target == "fastbootd":
            c, o, e = self.adb.run(["reboot", "fastboot"], device_serial=dev.serial)
        elif target == "edl":
            c, o, e = self.adb.run(["reboot", "edl"], device_serial=dev.serial)
        elif target == "sideload":
            c, o, e = self.adb.run(["reboot", "sideload"], device_serial=dev.serial)
        elif target == "systemui":
            c, o, e = self.adb.shell("pkill -f com.android.systemui", device_serial=dev.serial)
        else:
            c, o, e = self.adb.run(["reboot"], device_serial=dev.serial)

        return c, (o + "\n" + e).strip()

device_manager = DeviceManager()
