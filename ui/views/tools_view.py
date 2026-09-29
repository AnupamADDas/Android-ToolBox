import os
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import Optional
from PIL import ImageTk
from core.device_manager import device_manager
from core.wireless_manager import wireless_manager
from core.screen_tools import screen_tools
from utils.constants import (
    MODE_DEVICE, THEME_CARD_DARK, THEME_TEXT_SECONDARY_DARK,
    COLOR_SUCCESS, COLOR_DANGER
)

class ToolsView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.device = None
        self.current_screenshot = None
        self.screenshot_photo = None
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Left Card: Wireless ADB & Android 11+ Pairing
        self.wire_card = ctk.CTkFrame(self, corner_radius=8, fg_color=THEME_CARD_DARK)
        self.wire_card.grid(row=0, column=0, sticky="nsew", padx=(15, 8), pady=15)
        self.wire_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.wire_card, text="Wireless ADB Connection", font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=0, padx=15, pady=(15, 4), sticky="w"
        )
        ctk.CTkLabel(self.wire_card, text="Connect to your Android device over Wi-Fi without cables.",
                     text_color=THEME_TEXT_SECONDARY_DARK, font=ctk.CTkFont(size=12)).grid(
            row=1, column=0, padx=15, pady=(0, 12), sticky="w"
        )

        # One-Click USB to TCPIP Switch
        ctk.CTkButton(
            self.wire_card, text="Switch USB Device to TCPIP (Port 5555)", height=34,
            command=self._enable_tcpip
        ).grid(row=2, column=0, padx=15, pady=6, sticky="ew")

        # Direct IP Connect
        ctk.CTkLabel(self.wire_card, text="Connect via IP Address:", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=3, column=0, padx=15, pady=(12, 4), sticky="w"
        )

        ip_box = ctk.CTkFrame(self.wire_card, fg_color="transparent")
        ip_box.grid(row=4, column=0, padx=15, pady=4, sticky="ew")
        ip_box.grid_columnconfigure(0, weight=3)
        ip_box.grid_columnconfigure(1, weight=1)

        self.entry_ip = ctk.CTkEntry(ip_box, placeholder_text="192.168.1.X")
        self.entry_ip.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        self.entry_port = ctk.CTkEntry(ip_box, placeholder_text="5555", width=70)
        self.entry_port.grid(row=0, column=1, padx=(0, 6))
        self.entry_port.insert(0, "5555")

        self.btn_connect = ctk.CTkButton(ip_box, text="Connect", width=85, command=self._connect_wireless)
        self.btn_connect.grid(row=0, column=2)

        # Android 11+ Pairing
        ctk.CTkLabel(self.wire_card, text="Android 11+ Wireless Pairing:", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=5, column=0, padx=15, pady=(16, 4), sticky="w"
        )

        pair_box = ctk.CTkFrame(self.wire_card, fg_color="transparent")
        pair_box.grid(row=6, column=0, padx=15, pady=4, sticky="ew")
        pair_box.grid_columnconfigure(0, weight=2)
        pair_box.grid_columnconfigure(1, weight=1)
        pair_box.grid_columnconfigure(2, weight=1)

        self.entry_pair_ip = ctk.CTkEntry(pair_box, placeholder_text="Pairing IP")
        self.entry_pair_ip.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        self.entry_pair_port = ctk.CTkEntry(pair_box, placeholder_text="Port", width=65)
        self.entry_pair_port.grid(row=0, column=1, padx=(0, 4))

        self.entry_pair_code = ctk.CTkEntry(pair_box, placeholder_text="6-digit Code", width=95)
        self.entry_pair_code.grid(row=0, column=2, padx=(0, 6))

        self.btn_pair = ctk.CTkButton(self.wire_card, text="Pair Device", height=32, fg_color="#374151", command=self._pair_wireless)
        self.btn_pair.grid(row=7, column=0, padx=15, pady=(6, 15), sticky="ew")

        # Status text
        self.lbl_wire_status = ctk.CTkLabel(self.wire_card, text="", font=ctk.CTkFont(size=12), text_color=THEME_TEXT_SECONDARY_DARK)
        self.lbl_wire_status.grid(row=8, column=0, padx=15, pady=(0, 15), sticky="w")

        # 2. Right Card: Screen Capture & Mirroring
        self.screen_card = ctk.CTkFrame(self, corner_radius=8, fg_color=THEME_CARD_DARK)
        self.screen_card.grid(row=0, column=1, sticky="nsew", padx=(8, 15), pady=15)
        self.screen_card.grid_columnconfigure(0, weight=1)
        self.screen_card.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self.screen_card, text="Screen Capture & Mirror", font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=0, padx=15, pady=(15, 4), sticky="w"
        )

        screen_actions = ctk.CTkFrame(self.screen_card, fg_color="transparent")
        screen_actions.grid(row=1, column=0, padx=15, pady=4, sticky="ew")

        self.btn_shot = ctk.CTkButton(screen_actions, text="Take Screenshot", width=125, command=self._take_screenshot)
        self.btn_shot.grid(row=0, column=0, padx=(0, 6))

        self.btn_save_shot = ctk.CTkButton(screen_actions, text="Save As...", width=80, fg_color="#374151", command=self._save_screenshot)
        self.btn_save_shot.grid(row=0, column=1, padx=(0, 6))

        # Preview Container
        self.preview_box = ctk.CTkFrame(self.screen_card, fg_color="#18181b", corner_radius=6)
        self.preview_box.grid(row=2, column=0, padx=15, pady=8, sticky="nsew")
        self.preview_box.grid_columnconfigure(0, weight=1)
        self.preview_box.grid_rowconfigure(0, weight=1)

        self.lbl_preview = ctk.CTkLabel(
            self.preview_box, text="Screenshot preview will appear here.",
            text_color=THEME_TEXT_SECONDARY_DARK, font=ctk.CTkFont(size=12)
        )
        self.lbl_preview.grid(row=0, column=0)

        # Scrcpy Mirroring bottom section
        scrcpy_box = ctk.CTkFrame(self.screen_card, fg_color="transparent")
        scrcpy_box.grid(row=3, column=0, padx=15, pady=(8, 15), sticky="ew")
        scrcpy_box.grid_columnconfigure(0, weight=1)

        scrcpy_status = "Available in PATH" if screen_tools.is_scrcpy_available() else "Not detected (optional)"
        ctk.CTkLabel(
            scrcpy_box, text=f"Scrcpy Mirroring: {scrcpy_status}",
            font=ctk.CTkFont(size=11), text_color=THEME_TEXT_SECONDARY_DARK
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))

        self.btn_mirror = ctk.CTkButton(
            scrcpy_box, text="Launch Screen Mirror (scrcpy)", height=32,
            command=self._launch_mirror
        )
        self.btn_mirror.grid(row=1, column=0, sticky="ew")

    def update_device(self, device):
        self.device = device
        if device and device.details.get("wifi_ip") and device.details["wifi_ip"] != "Disconnected":
            self.entry_ip.delete(0, "end")
            self.entry_ip.insert(0, device.details["wifi_ip"])

    def _enable_tcpip(self):
        if not self.device:
            messagebox.showwarning("Wireless ADB", "Please connect a device via USB first.")
            return

        def _worker():
            c, out = wireless_manager.enable_tcpip(5555, self.device.serial)
            def _done():
                if c == 0:
                    self.lbl_wire_status.configure(
                        text="Switched to TCPIP mode! You can now disconnect the USB cable and click 'Connect'.",
                        text_color=COLOR_SUCCESS
                    )
                else:
                    self.lbl_wire_status.configure(text=out, text_color=COLOR_DANGER)
            self.after(0, _done)

        threading.Thread(target=_worker, daemon=True).start()

    def _connect_wireless(self):
        ip = self.entry_ip.get().strip()
        try:
            port = int(self.entry_port.get().strip())
        except ValueError:
            port = 5555

        if not ip:
            messagebox.showwarning("Connect", "Enter a valid IP address.")
            return

        self.btn_connect.configure(state="disabled", text="Connecting...")

        def _worker():
            c, out = wireless_manager.connect(ip, port)
            def _done():
                self.btn_connect.configure(state="normal", text="Connect")
                self.lbl_wire_status.configure(text=out)
                device_manager.refresh_devices()
            self.after(0, _done)

        threading.Thread(target=_worker, daemon=True).start()

    def _pair_wireless(self):
        ip = self.entry_pair_ip.get().strip()
        code = self.entry_pair_code.get().strip()
        try:
            port = int(self.entry_pair_port.get().strip())
        except ValueError:
            port = 0

        if not ip or not code or not port:
            messagebox.showwarning("Pair Device", "Please fill in IP, Pairing Port, and 6-digit Code.")
            return

        self.btn_pair.configure(state="disabled", text="Pairing...")

        def _worker():
            c, out = wireless_manager.pair(ip, port, code)
            def _done():
                self.btn_pair.configure(state="normal", text="Pair Device")
                self.lbl_wire_status.configure(text=out)
                if c == 0:
                    messagebox.showinfo("Paired", f"Device paired successfully! Now connect via normal ADB port.")
            self.after(0, _done)

        threading.Thread(target=_worker, daemon=True).start()

    def _take_screenshot(self):
        if not self.device or self.device.mode != MODE_DEVICE:
            messagebox.showwarning("Screenshot", "Device must be booted in Android OS.")
            return

        self.btn_shot.configure(state="disabled", text="Capturing...")

        def _worker():
            img, msg = screen_tools.capture_screenshot(self.device.serial)
            def _done():
                self.btn_shot.configure(state="normal", text="Take Screenshot")
                if img:
                    self.current_screenshot = img
                    # Create thumbnail preserving aspect ratio
                    thumb = img.copy()
                    thumb.thumbnail((260, 260))
                    self.screenshot_photo = ImageTk.PhotoImage(thumb)
                    self.lbl_preview.configure(image=self.screenshot_photo, text="")
                else:
                    messagebox.showerror("Screenshot Error", msg)
            self.after(0, _done)

        threading.Thread(target=_worker, daemon=True).start()

    def _save_screenshot(self):
        if not self.current_screenshot:
            messagebox.showwarning("Save Screenshot", "Capture a screenshot first.")
            return

        f = filedialog.asksaveasfilename(title="Save Screenshot", defaultextension=".png", filetypes=[("PNG Files", "*.png")])
        if f:
            self.current_screenshot.save(f)
            messagebox.showinfo("Saved", f"Screenshot saved to:\n{f}")

    def _launch_mirror(self):
        if not self.device:
            messagebox.showwarning("Mirror", "No device connected.")
            return

        c, msg = screen_tools.launch_scrcpy(self.device.serial)
        if c != 0:
            messagebox.showwarning("Screen Mirroring", msg)
