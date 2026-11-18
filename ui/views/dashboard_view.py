from ui.components import widgets as ctk
from ui.components.icons import icon
import threading
from tkinter import filedialog, messagebox
from typing import Optional
from core.device_manager import device_manager
from utils.constants import (
    MODE_DEVICE, MODE_RECOVERY, MODE_SIDELOAD, MODE_FASTBOOT,
    MODE_UNAUTHORIZED, THEME_CARD_DARK, THEME_TEXT_SECONDARY_DARK,
    COLOR_SUCCESS, COLOR_WARNING, COLOR_INFO, COLOR_DANGER,
    THEME_ACCENT, THEME_SURFACE, THEME_CARD_BORDER_DARK
)
from core.sideload_manager import sideload_manager

class DashboardView(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.device = None
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure((0, 1), weight=1, uniform="panels")
        self.status_card = ctk.CTkFrame(
            self, fg_color="#152536", border_color="#2b495b",
        )
        self.status_card.grid(row=0, column=0, columnspan=2, sticky="ew", padx=(0, 4), pady=(0, 12))
        self.status_card.grid_columnconfigure(0, weight=1)
        self.lbl_mode_badge = ctk.CTkLabel(
            self.status_card, text="●  Waiting for connection", height=22,
            font=ctk.CTkFont(size=12), text_color=THEME_ACCENT,
        )
        self.lbl_mode_badge.grid(row=0, column=0, padx=24, pady=(18, 0), sticky="w")
        self.lbl_title = ctk.CTkLabel(
            self.status_card, text="Your Android workspace",
            font=ctk.CTkFont(size=23, weight="bold"), anchor="w",
        )
        self.lbl_title.grid(row=1, column=0, padx=24, pady=(4, 0), sticky="ew")
        self.lbl_subtitle = ctk.CTkLabel(
            self.status_card, text="Connect with USB or pair over Wi-Fi.",
            text_color=THEME_TEXT_SECONDARY_DARK, anchor="w",
        )
        self.lbl_subtitle.grid(row=2, column=0, padx=24, pady=(0, 18), sticky="ew")
        self.glow = ctk.GlowArt(self.status_card)
        self.glow.grid(row=0, column=1, rowspan=3, padx=(0, 16), pady=4)
        self.status_card.bind("<Configure>", self._fit_banner)
        self.specs_card = ctk.CTkFrame(self, fg_color=THEME_CARD_DARK)
        self.specs_card.grid(row=1, column=0, sticky="nsew", padx=(0, 6), pady=0)
        self.specs_card.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            self.specs_card, text="  System & hardware", image=icon("cpu", COLOR_INFO),
            compound="left", font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, columnspan=2, padx=20, pady=(18, 12), sticky="w")
        self.spec_labels = {}
        fields = [
            ("Brand / model", "model"), ("Android version", "android"),
            ("SDK level", "sdk"), ("Security patch", "patch"),
            ("Architecture", "cpu"), ("Display / DPI", "display"),
            ("Wi-Fi address", "ip"), ("Root access", "root"),
        ]
        for idx, (label_text, key) in enumerate(fields, start=1):
            ctk.CTkLabel(
                self.specs_card, text=label_text, text_color=THEME_TEXT_SECONDARY_DARK,
                font=ctk.CTkFont(size=12),
            ).grid(row=idx, column=0, padx=(20, 8), pady=2, sticky="w")
            val_lbl = ctk.CTkLabel(
                self.specs_card, text="—", font=ctk.CTkFont(size=12),
                anchor="e", wraplength=170,
            )
            val_lbl.grid(row=idx, column=1, padx=(0, 20), pady=2, sticky="e")
            self.spec_labels[key] = val_lbl
        ctk.CTkLabel(self.specs_card, text="", height=12).grid(row=9, column=0)
        self.power_card = ctk.CTkFrame(self, fg_color=THEME_CARD_DARK)
        self.power_card.grid(row=1, column=1, sticky="nsew", padx=(6, 4))
        self.power_card.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkLabel(
            self.power_card, text="  Battery & power", image=icon("battery", COLOR_SUCCESS),
            compound="left", font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, columnspan=2, padx=20, pady=(18, 8), sticky="w")
        self.bat_labels = {}
        self.bat_labels["level"] = ctk.CTkLabel(
            self.power_card, text="—", text_color=COLOR_SUCCESS,
            font=ctk.CTkFont(size=32, weight="bold"),
        )
        self.bat_labels["level"].grid(row=1, column=0, padx=20, sticky="w")
        self.bat_labels["status"] = ctk.CTkLabel(
            self.power_card, text="No battery data", text_color=THEME_TEXT_SECONDARY_DARK,
        )
        self.bat_labels["status"].grid(row=1, column=1, padx=20, sticky="e")
        self.battery_progress = ctk.CTkProgressBar(self.power_card, height=6, progress_color=COLOR_SUCCESS)
        self.battery_progress.grid(row=2, column=0, columnspan=2, padx=20, pady=(8, 12), sticky="ew")
        self.battery_progress.set(0)
        for column, (label, key) in enumerate((("Temperature", "temp"), ("Voltage", "voltage"))):
            box = ctk.CTkFrame(self.power_card, fg_color="transparent")
            box.grid(row=3, column=column, padx=20, sticky="w")
            ctk.CTkLabel(box, text=label, height=20, text_color=THEME_TEXT_SECONDARY_DARK,
                         font=ctk.CTkFont(size=12)).pack(anchor="w")
            self.bat_labels[key] = ctk.CTkLabel(box, text="—", height=24)
            self.bat_labels[key].pack(anchor="w")
        ctk.CTkLabel(
            self.power_card, text="Reboot controls", font=ctk.CTkFont(size=12),
            text_color=THEME_TEXT_SECONDARY_DARK,
        ).grid(row=4, column=0, columnspan=2, padx=20, pady=(12, 4), sticky="w")
        btn_grid = ctk.CTkFrame(self.power_card, fg_color="transparent")
        btn_grid.grid(row=5, column=0, columnspan=2, padx=16, pady=(0, 16), sticky="ew")
        btn_grid.grid_columnconfigure((0, 1), weight=1, uniform="reboot")
        actions = [
            ("btn_reboot_sys", "System", "system"), ("btn_reboot_rec", "Recovery", "recovery"),
            ("btn_reboot_bl", "Bootloader", "bootloader"), ("btn_reboot_fb", "FastbootD", "fastbootd"),
            ("btn_reboot_sysui", "Restart UI", "systemui"),
        ]
        for index, (attr, text, target) in enumerate(actions):
            button = ctk.CTkButton(btn_grid, text=text, width=100, height=34,
                                   command=lambda t=target: self._trigger_reboot(t))
            button.grid(row=index // 2, column=index % 2, padx=4, pady=3, sticky="ew")
            setattr(self, attr, button)
        self.btn_pull_rec_log = ctk.CTkButton(btn_grid, text="Recovery log", width=100, height=34,
                                             command=self._pull_recovery_log)
        self.btn_pull_rec_log.grid(row=2, column=1, padx=4, pady=3, sticky="ew")
        self.device_buttons = [getattr(self, attr) for attr, _, _ in actions] + [self.btn_pull_rec_log]
        quick = ctk.CTkFrame(self, fg_color="transparent")
        quick.grid(row=2, column=0, columnspan=2, sticky="ew", padx=(0, 4), pady=(16, 0))
        quick.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="quick")
        ctk.CTkLabel(quick, text="Quick access", font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 8),
        )
        for column, (text, view, glyph, color) in enumerate([
            ("Install APK", "packages", "package", COLOR_INFO),
            ("Browse files", "files", "folder", COLOR_WARNING),
            ("Open shell", "terminal", "terminal", COLOR_SUCCESS),
            ("Pair device", "tools", "wifi", THEME_ACCENT),
        ]):
            ctk.CTkButton(
                quick, text=text, image=icon(glyph, color, 18), height=46, width=100,
                fg_color=THEME_CARD_DARK, command=lambda v=view: self.winfo_toplevel().select_view(v),
            ).grid(row=1, column=column, sticky="ew", padx=(0 if column == 0 else 4, 0 if column == 3 else 4))
        self.notice_card = ctk.CTkFrame(self, fg_color="transparent")
        self.notice_card.grid(row=3, column=0, columnspan=2, sticky="ew", padx=(0, 4), pady=(12, 16))
        self.notice_card.grid_columnconfigure(0, weight=1)
        self.lbl_notice = ctk.CTkLabel(
            self.notice_card, text="", font=ctk.CTkFont(size=12),
            text_color=THEME_TEXT_SECONDARY_DARK, anchor="w", justify="left", wraplength=640,
        )
        self.lbl_notice.grid(row=0, column=0, sticky="ew")
        self.notice_card.bind("<Configure>", lambda event: self.lbl_notice.configure(wraplength=max(240, event.width - 16)))

    def _fit_banner(self, event):
        show = event.width >= 820
        if show:
            self.glow.grid()
        else:
            self.glow.grid_remove()
        self.lbl_title.configure(wraplength=max(260, event.width - (320 if show else 48)))
        self.lbl_subtitle.configure(wraplength=max(260, event.width - (320 if show else 48)))

    def update_device(self, device):
        self.device = device
        for button in self.device_buttons:
            button.configure(state="normal" if device else "disabled")
        if not device:
            self.lbl_title.configure(text="Your Android workspace")
            self.lbl_subtitle.configure(text="Connect with USB or pair over Wi-Fi.")
            self.lbl_mode_badge.configure(text="●  Waiting for connection", text_color=THEME_ACCENT)
            for lbl in self.spec_labels.values():
                lbl.configure(text="—")
            for lbl in self.bat_labels.values():
                lbl.configure(text="—")
            self.bat_labels["status"].configure(text="No battery data")
            self.battery_progress.set(0)
            self.lbl_notice.configure(
                text="To connect by USB, enable USB debugging in Developer options and approve this computer on your phone."
            )
            return

        # Running info query in background thread
        threading.Thread(target=self._fetch_info_worker, args=(device,), daemon=True).start()

    def _fetch_info_worker(self, device):
        info = device_manager.get_device_info(device)
        self.after(0, lambda: self._apply_info_ui(device, info))

    def _apply_info_ui(self, device, info):
        if not self.device or (self.device.serial, self.device.mode) != (device.serial, device.mode):
            return
        for lbl in (*self.spec_labels.values(), *self.bat_labels.values()):
            lbl.configure(text="—")
        self.battery_progress.set(0)
        mode_text = {
            MODE_DEVICE: "●  Connected · Android",
            MODE_RECOVERY: "●  Custom recovery",
            MODE_SIDELOAD: "●  Sideload mode",
            MODE_FASTBOOT: "●  Fastboot mode",
            MODE_UNAUTHORIZED: "●  Authorization needed",
        }.get(device.mode, f"●  {device.mode}")

        color = {
            MODE_DEVICE: COLOR_SUCCESS,
            MODE_RECOVERY: COLOR_WARNING,
            MODE_SIDELOAD: COLOR_WARNING,
            MODE_FASTBOOT: COLOR_INFO,
            MODE_UNAUTHORIZED: COLOR_DANGER
        }.get(device.mode, COLOR_INFO)

        self.lbl_title.configure(text=device.model)
        self.lbl_subtitle.configure(text=f"Serial  /  {device.serial}")
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
            try:
                level = float(str(bat.get("level", "0")).rstrip("%"))
                self.battery_progress.set(max(0, min(1, level / 100)))
            except ValueError:
                self.battery_progress.set(0)

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
        elif device.mode == MODE_SIDELOAD:
            self.lbl_notice.configure(text="Device is ready for a ZIP package. Open Flash & sideload to begin.")
        else:
            self.lbl_notice.configure(text=f"Device state: {device.mode}. Check the USB connection and device screen.")

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
