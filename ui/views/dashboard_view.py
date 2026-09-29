import customtkinter as ctk
import threading
from tkinter import filedialog, messagebox
from typing import Optional
from core.device_manager import device_manager
from utils.constants import (
    MODE_DEVICE, MODE_RECOVERY, MODE_SIDELOAD, MODE_FASTBOOT,
    MODE_UNAUTHORIZED, THEME_CARD_DARK, THEME_TEXT_SECONDARY_DARK,
    COLOR_SUCCESS, COLOR_WARNING, COLOR_INFO, COLOR_DANGER
)
from core.sideload_manager import sideload_manager

class DashboardView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.device = None
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Status / Header Banner
        self.status_card = ctk.CTkFrame(self, corner_radius=8, fg_color=THEME_CARD_DARK)
        self.status_card.grid(row=0, column=0, columnspan=2, sticky="ew", padx=15, pady=(15, 10))
        self.status_card.grid_columnconfigure(1, weight=1)

        self.lbl_title = ctk.CTkLabel(
            self.status_card, text="Device Overview", font=ctk.CTkFont(size=18, weight="bold")
        )
        self.lbl_title.grid(row=0, column=0, padx=15, pady=12, sticky="w")

        self.lbl_mode_badge = ctk.CTkLabel(
            self.status_card, text="Disconnected", font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLOR_DANGER
        )
        self.lbl_mode_badge.grid(row=0, column=1, padx=15, pady=12, sticky="e")

        # Hardware & OS Specs Card (Left)
        self.specs_card = ctk.CTkFrame(self, corner_radius=8, fg_color=THEME_CARD_DARK)
        self.specs_card.grid(row=1, column=0, sticky="nsew", padx=(15, 8), pady=5)
        self.specs_card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self.specs_card, text="System & Hardware", font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=2, padx=15, pady=(12, 8), sticky="w")

        self.spec_labels = {}
        fields = [
            ("Brand / Model", "model"),
            ("Android Version", "android"),
            ("SDK Level", "sdk"),
            ("Security Patch", "patch"),
            ("CPU Architecture", "cpu"),
            ("Resolution / DPI", "display"),
            ("Wi-Fi IP Address", "ip"),
            ("Root Access", "root")
        ]
        for idx, (label_text, key) in enumerate(fields, start=1):
            ctk.CTkLabel(
                self.specs_card, text=label_text, text_color=THEME_TEXT_SECONDARY_DARK,
                font=ctk.CTkFont(size=12)
            ).grid(row=idx, column=0, padx=15, pady=4, sticky="w")

            val_lbl = ctk.CTkLabel(
                self.specs_card, text="-", font=ctk.CTkFont(size=12, weight="bold")
            )
            val_lbl.grid(row=idx, column=1, padx=15, pady=4, sticky="e")
            self.spec_labels[key] = val_lbl

        # Battery & Power Menu Card (Right)
        self.power_card = ctk.CTkFrame(self, corner_radius=8, fg_color=THEME_CARD_DARK)
        self.power_card.grid(row=1, column=1, sticky="nsew", padx=(8, 15), pady=5)
        self.power_card.grid_columnconfigure(0, weight=1)
        self.power_card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self.power_card, text="Battery & State", font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=2, padx=15, pady=(12, 8), sticky="w")

        self.bat_labels = {}
        bat_fields = [
            ("Battery Level", "level"),
            ("Status", "status"),
            ("Temperature", "temp"),
            ("Voltage", "voltage")
        ]
        for idx, (lbl_txt, key) in enumerate(bat_fields, start=1):
            ctk.CTkLabel(
                self.power_card, text=lbl_txt, text_color=THEME_TEXT_SECONDARY_DARK,
                font=ctk.CTkFont(size=12)
            ).grid(row=idx, column=0, padx=15, pady=4, sticky="w")

            v_lbl = ctk.CTkLabel(self.power_card, text="-", font=ctk.CTkFont(size=12, weight="bold"))
            v_lbl.grid(row=idx, column=1, padx=15, pady=4, sticky="e")
            self.bat_labels[key] = v_lbl

        # Reboot Controls inside power card
        ctk.CTkLabel(
            self.power_card, text="Power & Reboot", font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=5, column=0, columnspan=2, padx=15, pady=(16, 8), sticky="w")

        btn_grid = ctk.CTkFrame(self.power_card, fg_color="transparent")
        btn_grid.grid(row=6, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="ew")
        btn_grid.grid_columnconfigure((0, 1, 2), weight=1)

        self.btn_reboot_sys = ctk.CTkButton(
            btn_grid, text="Reboot System", height=32, command=lambda: self._trigger_reboot("system")
        )
        self.btn_reboot_sys.grid(row=0, column=0, padx=3, pady=3, sticky="ew")

        self.btn_reboot_rec = ctk.CTkButton(
            btn_grid, text="Recovery", height=32, command=lambda: self._trigger_reboot("recovery")
        )
        self.btn_reboot_rec.grid(row=0, column=1, padx=3, pady=3, sticky="ew")

        self.btn_reboot_bl = ctk.CTkButton(
            btn_grid, text="Bootloader", height=32, command=lambda: self._trigger_reboot("bootloader")
        )
        self.btn_reboot_bl.grid(row=0, column=2, padx=3, pady=3, sticky="ew")

        self.btn_reboot_fb = ctk.CTkButton(
            btn_grid, text="FastbootD", height=32, command=lambda: self._trigger_reboot("fastbootd")
        )
        self.btn_reboot_fb.grid(row=1, column=0, padx=3, pady=3, sticky="ew")

        self.btn_reboot_sysui = ctk.CTkButton(
            btn_grid, text="Restart UI", height=32, command=lambda: self._trigger_reboot("systemui")
        )
        self.btn_reboot_sysui.grid(row=1, column=1, padx=3, pady=3, sticky="ew")

        self.btn_pull_rec_log = ctk.CTkButton(
            btn_grid, text="Pull Recovery Log", height=32, fg_color="#374151",
            command=self._pull_recovery_log
        )
        self.btn_pull_rec_log.grid(row=1, column=2, padx=3, pady=3, sticky="ew")

        # Bottom Notice Area
        self.notice_card = ctk.CTkFrame(self, corner_radius=8, fg_color=THEME_CARD_DARK)
        self.notice_card.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=15, pady=10)
        self.notice_card.grid_columnconfigure(0, weight=1)

        self.lbl_notice = ctk.CTkLabel(
            self.notice_card,
            text="Connect your Android device via USB or Wireless ADB to begin.",
            font=ctk.CTkFont(size=13),
            text_color=THEME_TEXT_SECONDARY_DARK
        )
        self.lbl_notice.grid(row=0, column=0, padx=20, pady=25)

    def update_device(self, device):
        self.device = device
        if not device:
            self.lbl_title.configure(text="No Device Selected")
            self.lbl_mode_badge.configure(text="Disconnected", text_color=COLOR_DANGER)
            for lbl in self.spec_labels.values():
                lbl.configure(text="-")
            for lbl in self.bat_labels.values():
                lbl.configure(text="-")
            self.lbl_notice.configure(
                text="No Android device detected. Connect a device via USB with USB Debugging enabled, or via Wireless ADB."
            )
            return

        # Running info query in background thread
        threading.Thread(target=self._fetch_info_worker, args=(device,), daemon=True).start()

    def _fetch_info_worker(self, device):
        info = device_manager.get_device_info(device)
        self.after(0, lambda: self._apply_info_ui(device, info))

    def _apply_info_ui(self, device, info):
        mode_text = {
            MODE_DEVICE: "🟢 Connected (Android OS)",
            MODE_RECOVERY: "🟠 Recovery Mode (TWRP / Custom)",
            MODE_SIDELOAD: "⚡ Sideload Mode",
            MODE_FASTBOOT: "🔵 Fastboot Mode",
            MODE_UNAUTHORIZED: "🔴 Unauthorized (Check Phone Screen)"
        }.get(device.mode, f"⚪ {device.mode}")

        color = {
            MODE_DEVICE: COLOR_SUCCESS,
            MODE_RECOVERY: COLOR_WARNING,
            MODE_SIDELOAD: COLOR_WARNING,
            MODE_FASTBOOT: COLOR_INFO,
            MODE_UNAUTHORIZED: COLOR_DANGER
        }.get(device.mode, COLOR_INFO)

        self.lbl_title.configure(text=f"{device.model} ({device.serial})")
        self.lbl_mode_badge.configure(text=mode_text, text_color=color)

        if device.mode == MODE_DEVICE:
            self.spec_labels["model"].configure(text=f"{info.get('brand', '')} {info.get('model', '')}".strip())
            self.spec_labels["android"].configure(text=f"Android {info.get('android_version', '-')}")
            self.spec_labels["sdk"].configure(text=f"API {info.get('sdk_level', '-')}")
            self.spec_labels["patch"].configure(text=info.get("security_patch", "-"))
            self.spec_labels["cpu"].configure(text=info.get("cpu_abi", "-"))
            self.spec_labels["display"].configure(text=f"{info.get('resolution', '-')} ({info.get('density', '-')})")
            self.spec_labels["ip"].configure(text=info.get("wifi_ip", "-"))
            root_text = "Rooted (SU Available)" if info.get("is_root") else "Not Rooted"
            self.spec_labels["root"].configure(text=root_text)

            bat = info.get("battery", {})
            self.bat_labels["level"].configure(text=bat.get("level", "-"))
            self.bat_labels["status"].configure(text=bat.get("status", "-"))
            self.bat_labels["temp"].configure(text=bat.get("temperature", "-"))
            self.bat_labels["voltage"].configure(text=bat.get("voltage", "-"))

            self.lbl_notice.configure(
                text=f"Device ready. Build: {info.get('build_id', 'Unknown')}"
            )

        elif device.mode == MODE_RECOVERY:
            self.spec_labels["model"].configure(text=device.model)
            self.spec_labels["android"].configure(text="Custom Recovery")
            self.spec_labels["sdk"].configure(text="Recovery Mode")
            self.spec_labels["patch"].configure(text="-")
            self.spec_labels["cpu"].configure(text="-")
            self.spec_labels["display"].configure(text="-")
            self.spec_labels["ip"].configure(text="USB Recovery")
            self.spec_labels["root"].configure(text="Full Root (Recovery Default)")

            for lbl in self.bat_labels.values():
                lbl.configure(text="N/A (Recovery)")

            self.lbl_notice.configure(
                text="Device is in Custom Recovery mode. Root terminal, sideload, partition flashing, and file manager are accessible."
            )

        elif device.mode == MODE_FASTBOOT:
            self.spec_labels["model"].configure(text=info.get("product", "Fastboot Device"))
            self.spec_labels["android"].configure(text="Fastboot / Bootloader")
            self.spec_labels["sdk"].configure(text=f"Unlocked: {info.get('unlocked', 'Unknown')}")
            for k in ["patch", "cpu", "display", "ip", "root"]:
                self.spec_labels[k].configure(text="-")
            for lbl in self.bat_labels.values():
                lbl.configure(text="N/A (Fastboot)")

            self.lbl_notice.configure(
                text="Device is in Fastboot mode. Use the Flashing tab to flash partitions or reboot."
            )

        elif device.mode == MODE_UNAUTHORIZED:
            self.lbl_notice.configure(
                text="Device is unauthorized! Unlock your phone and tap 'Allow' on the USB debugging authorization dialog."
            )

    def _trigger_reboot(self, target: str):
        if not self.device:
            messagebox.showwarning("Reboot", "No device connected.")
            return

        def _worker():
            code, out = device_manager.reboot(target)
            if code != 0:
                self.after(0, lambda: messagebox.showerror("Reboot Error", out or "Reboot command failed."))

        threading.Thread(target=_worker, daemon=True).start()

    def _pull_recovery_log(self):
        if not self.device:
            messagebox.showwarning("Recovery Log", "No device connected.")
            return

        dest = filedialog.askdirectory(title="Select Folder to Save recovery.log")
        if not dest:
            return

        def _worker():
            code, msg = sideload_manager.pull_recovery_log(dest)
            if code == 0:
                self.after(0, lambda: messagebox.showinfo("Recovery Log", msg))
            else:
                self.after(0, lambda: messagebox.showerror("Recovery Log Error", msg))

        threading.Thread(target=_worker, daemon=True).start()
