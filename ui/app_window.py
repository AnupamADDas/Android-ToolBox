import os
import customtkinter as ctk
from typing import Dict, List, Optional
from tkinter import messagebox
from PIL import Image, ImageTk
from core.device_manager import device_manager, AndroidDevice
from core.adb_locator import locator
from utils.constants import (
    APP_NAME, APP_VERSION, THEME_ACCENT, THEME_BG_DARK, THEME_CARD_DARK,
    THEME_TEXT_SECONDARY_DARK, COLOR_SUCCESS, COLOR_WARNING, COLOR_INFO, COLOR_DANGER,
    MODE_DEVICE, MODE_RECOVERY, MODE_SIDELOAD, MODE_FASTBOOT, MODE_UNAUTHORIZED
)

# Import Views
from ui.views.dashboard_view import DashboardView
from ui.views.apps_view import AppsView
from ui.views.files_view import FilesView
from ui.views.flashing_view import FlashingView
from ui.views.shell_view import ShellView
from ui.views.logcat_view import LogcatView
from ui.views.tools_view import ToolsView

class AppWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("1060x700")
        self.minsize(920, 600)

        # Set Window Icon
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ico_path = os.path.join(base_dir, "assets", "icon.ico")
        png_path = os.path.join(base_dir, "assets", "icon.png")
        if os.path.isfile(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception:
                pass
        if os.path.isfile(png_path):
            try:
                self._icon_img = ImageTk.PhotoImage(file=png_path)
                self.iconphoto(False, self._icon_img)
            except Exception:
                pass

        self.devices: List[AndroidDevice] = []
        self.active_view_name = "dashboard"
        self.views: Dict[str, ctk.CTkFrame] = {}

        self._build_layout()
        self._init_views()
        self._setup_device_listener()

    def _build_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Left Sidebar
        self.sidebar = ctk.CTkFrame(self, width=210, corner_radius=0, fg_color=THEME_CARD_DARK)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(8, weight=1)

        # Logo / Title
        title_box = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        title_box.grid(row=0, column=0, padx=15, pady=(18, 15), sticky="w")

        ctk.CTkLabel(
            title_box, text="ANDROID TOOLBOX",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box, text="Android Native Utility",
            font=ctk.CTkFont(size=11), text_color=THEME_TEXT_SECONDARY_DARK
        ).pack(anchor="w")

        # Navigation Buttons
        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "📱  Dashboard"),
            ("packages", "📦  Packages"),
            ("files", "📁  File Explorer"),
            ("flashing", "⚡  Flashing & Sideload"),
            ("terminal", "💻  Terminal"),
            ("logcat", "📋  Logcat"),
            ("tools", "📶  Wireless & Screen")
        ]

        for idx, (key, label) in enumerate(nav_items, start=1):
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                anchor="w",
                height=36,
                fg_color="transparent",
                text_color=THEME_TEXT_SECONDARY_DARK,
                hover_color="#374151",
                font=ctk.CTkFont(size=13),
                command=lambda k=key: self.select_view(k)
            )
            btn.grid(row=idx, column=0, padx=10, pady=3, sticky="ew")
            self.nav_buttons[key] = btn

        # Sidebar Footer
        footer_box = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer_box.grid(row=9, column=0, padx=12, pady=12, sticky="ew")

        self.btn_restart_adb = ctk.CTkButton(
            footer_box, text="Restart ADB Server", height=28, font=ctk.CTkFont(size=11),
            fg_color="#374151", command=self._restart_adb
        )
        self.btn_restart_adb.pack(fill="x", pady=4)

        self.btn_theme = ctk.CTkButton(
            footer_box, text="Toggle Theme", height=28, font=ctk.CTkFont(size=11),
            fg_color="#374151", command=self._toggle_theme
        )
        self.btn_theme.pack(fill="x", pady=4)

        # 2. Main Content Container
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew")
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(1, weight=1)

        # Top Bar (Device Switcher & Live Status)
        self.top_bar = ctk.CTkFrame(self.main_container, height=48, corner_radius=0, fg_color=THEME_CARD_DARK)
        self.top_bar.grid(row=0, column=0, sticky="ew")
        self.top_bar.grid_columnconfigure(0, weight=1)

        top_inner = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        top_inner.pack(fill="both", expand=True, padx=15, pady=8)

        # Left side of topbar: Selected Device
        self.cmb_devices = ctk.CTkOptionMenu(
            top_inner, values=["Scanning devices..."], width=320,
            command=self._on_device_selected
        )
        self.cmb_devices.pack(side="left", padx=(0, 8))

        self.btn_refresh = ctk.CTkButton(
            top_inner, text="⟳ Refresh", width=90, fg_color="#374151", command=self._manual_refresh
        )
        self.btn_refresh.pack(side="left")

        # Right side: Binary Status Badge
        adb_status_text = "ADB: Ready" if locator.is_adb_ready() else "ADB: Missing"
        fb_status_text = "Fastboot: Ready" if locator.is_fastboot_ready() else "Fastboot: Missing"
        self.lbl_binary_status = ctk.CTkLabel(
            top_inner, text=f"{adb_status_text}  •  {fb_status_text}",
            font=ctk.CTkFont(size=11), text_color=THEME_TEXT_SECONDARY_DARK
        )
        self.lbl_binary_status.pack(side="right")

        # View Host Frame
        self.view_host = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.view_host.grid(row=1, column=0, sticky="nsew")
        self.view_host.grid_columnconfigure(0, weight=1)
        self.view_host.grid_rowconfigure(0, weight=1)

    def _init_views(self):
        self.views["dashboard"] = DashboardView(self.view_host)
        self.views["packages"] = AppsView(self.view_host)
        self.views["files"] = FilesView(self.view_host)
        self.views["flashing"] = FlashingView(self.view_host)
        self.views["terminal"] = ShellView(self.view_host)
        self.views["logcat"] = LogcatView(self.view_host)
        self.views["tools"] = ToolsView(self.view_host)

        self.select_view("dashboard")

    def select_view(self, name: str):
        self.active_view_name = name

        # Update button highlights
        for key, btn in self.nav_buttons.items():
            if key == name:
                btn.configure(fg_color=THEME_ACCENT, text_color="#ffffff")
            else:
                btn.configure(fg_color="transparent", text_color=THEME_TEXT_SECONDARY_DARK)

        # Show active view frame
        for key, view in self.views.items():
            if key == name:
                view.grid(row=0, column=0, sticky="nsew")
                if hasattr(view, "update_device"):
                    view.update_device(device_manager.selected_device)
            else:
                view.grid_forget()

    def _setup_device_listener(self):
        device_manager.add_listener(self._on_devices_updated)
        device_manager.start_monitoring(interval=2.5)

    def _on_devices_updated(self, devices: List[AndroidDevice]):
        self.devices = devices
        self.after(0, self._update_device_ui)

    def _update_device_ui(self):
        if not self.devices:
            self.cmb_devices.configure(values=["No devices connected"])
            self.cmb_devices.set("No devices connected")
        else:
            options = [d.display_name for d in self.devices]
            self.cmb_devices.configure(values=options)

            if device_manager.selected_device:
                self.cmb_devices.set(device_manager.selected_device.display_name)
            else:
                self.cmb_devices.set(options[0])

        # Notify active view
        current_view = self.views.get(self.active_view_name)
        if current_view and hasattr(current_view, "update_device"):
            current_view.update_device(device_manager.selected_device)

    def _on_device_selected(self, choice_text: str):
        for d in self.devices:
            if d.display_name == choice_text:
                device_manager.select_device(d.serial)
                break

        current_view = self.views.get(self.active_view_name)
        if current_view and hasattr(current_view, "update_device"):
            current_view.update_device(device_manager.selected_device)

    def _manual_refresh(self):
        self.btn_refresh.configure(state="disabled", text="Scanning...")
        def _worker():
            device_manager.refresh_devices()
            def _done():
                self.btn_refresh.configure(state="normal", text="⟳ Refresh")
                self._update_device_ui()
            self.after(0, _done)

        import threading
        threading.Thread(target=_worker, daemon=True).start()

    def _restart_adb(self):
        import threading
        def _worker():
            c, out, err = device_manager.adb.restart_server()
            self.after(0, self._manual_refresh)
        threading.Thread(target=_worker, daemon=True).start()

    def _toggle_theme(self):
        curr = ctk.get_appearance_mode()
        ctk.set_appearance_mode("light" if curr == "Dark" else "dark")

    def on_closing(self):
        device_manager.stop_monitoring()
        self.destroy()
