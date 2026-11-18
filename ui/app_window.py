import os
from ui.components import widgets as ctk
from ui.components.icons import icon
from ui.components.style import configure_theme, style_window
from typing import Dict, List, Optional
from tkinter import messagebox
from PIL import Image, ImageTk
from core.device_manager import device_manager, AndroidDevice
from core.adb_locator import locator
from utils.constants import (
    APP_NAME, APP_VERSION, THEME_ACCENT, THEME_BG_DARK, THEME_CARD_DARK,
    THEME_TEXT_SECONDARY_DARK, COLOR_SUCCESS, COLOR_WARNING, COLOR_INFO, COLOR_DANGER,
    MODE_DEVICE, MODE_RECOVERY, MODE_SIDELOAD, MODE_FASTBOOT, MODE_UNAUTHORIZED,
    THEME_SIDEBAR, THEME_SURFACE, THEME_CARD_BORDER_DARK
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
        configure_theme()
        super().__init__()

        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("1240x860")
        self.minsize(1024, 720)
        self.after(100, lambda: style_window(self))

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
        self._update_device_ui()

    def _build_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color=THEME_SIDEBAR)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(12, 0), pady=12)
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(12, weight=1)
        self.sidebar.grid_propagate(False)
        title_box = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        title_box.grid(row=0, column=0, padx=20, pady=(26, 24), sticky="ew")
        ctk.CTkLabel(
            title_box, text="", image=icon("smartphone", THEME_ACCENT, 26),
            width=40, height=42, fg_color="#1c383f", corner_radius=12,
        ).pack(side="left", padx=(0, 10))
        wordmark = ctk.CTkFrame(title_box, fg_color="transparent")
        wordmark.pack(side="left")
        ctk.CTkLabel(
            wordmark, text="Android", height=24, anchor="w",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            wordmark, text="Toolbox", height=18,
            font=ctk.CTkFont(size=13), text_color=THEME_TEXT_SECONDARY_DARK,
        ).pack(anchor="w")
        ctk.CTkLabel(
            self.sidebar, text="Workspace", text_color=THEME_TEXT_SECONDARY_DARK,
            font=ctk.CTkFont(size=12), anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 8))
        self.nav_buttons = {}
        self.nav_items = [
            ("dashboard", "Overview", "layout-dashboard", THEME_ACCENT),
            ("packages", "Packages", "package", COLOR_INFO),
            ("files", "File explorer", "folder", COLOR_WARNING),
            ("flashing", "Flash & sideload", "zap", "#ff9e80"),
            ("terminal", "Terminal", "terminal", COLOR_SUCCESS),
            ("logcat", "Logcat", "scroll-text", "#f390af"),
            ("tools", "Wireless & screen", "wifi", "#83c9ef"),
        ]
        for idx, (key, label, glyph, color) in enumerate(self.nav_items, start=2):
            btn = ctk.CTkButton(
                self.sidebar, text=f"  {label}", image=icon(glyph, color),
                anchor="w", height=46, corner_radius=12, fg_color="transparent",
                text_color=THEME_TEXT_SECONDARY_DARK, hover_color=THEME_SURFACE,
                font=ctk.CTkFont(size=13), command=lambda k=key: self.select_view(k),
            )
            btn.grid(row=idx, column=0, padx=12, pady=3, sticky="ew")
            self.nav_buttons[key] = btn
        footer_box = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer_box.grid(row=13, column=0, padx=14, pady=16, sticky="ew")
        self.lbl_connection = ctk.CTkLabel(
            footer_box, text="●  Waiting for a device", anchor="w",
            text_color=THEME_TEXT_SECONDARY_DARK, font=ctk.CTkFont(size=12),
        )
        self.lbl_connection.pack(fill="x", padx=8, pady=(0, 12))
        self.btn_restart_adb = ctk.CTkButton(
            footer_box, text="  Restart ADB", image=icon("refresh-cw", size=16),
            anchor="w", height=36, fg_color="transparent", command=self._restart_adb,
        )
        self.btn_restart_adb.pack(fill="x", pady=4)
        ctk.CTkLabel(
            footer_box, text=f"Desktop edition  /  v{APP_VERSION}", anchor="w",
            text_color=THEME_TEXT_SECONDARY_DARK, font=ctk.CTkFont(size=12),
        ).pack(fill="x", padx=8, pady=(12, 0))
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=8, pady=12)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(2, weight=1)
        self.top_bar = ctk.CTkFrame(self.main_container, fg_color=THEME_CARD_DARK)
        self.top_bar.grid(row=0, column=0, sticky="ew", padx=16)
        self.top_bar.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self.top_bar, text="", image=icon("usb", THEME_ACCENT)).grid(
            row=0, column=0, padx=(16, 10), pady=12,
        )
        self.cmb_devices = ctk.CTkOptionMenu(
            self.top_bar, values=["Scanning devices..."], width=260,
            dynamic_resizing=False, command=self._on_device_selected,
        )
        self.cmb_devices.grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=12)
        self.btn_refresh = ctk.CTkButton(
            self.top_bar, text="Refresh", image=icon("refresh-cw", size=16),
            width=100, command=self._manual_refresh,
        )
        self.btn_refresh.grid(row=0, column=2, padx=(0, 16), pady=12)
        adb_status_text = "ADB ready" if locator.is_adb_ready() else "ADB missing"
        fb_status_text = "Fastboot ready" if locator.is_fastboot_ready() else "Fastboot missing"
        self.lbl_binary_status = ctk.CTkLabel(
            self.top_bar, text=f"{adb_status_text}  ·  {fb_status_text}",
            font=ctk.CTkFont(size=12), text_color=THEME_TEXT_SECONDARY_DARK,
        )
        self.lbl_binary_status.grid(row=0, column=3, padx=(0, 16))
        heading = ctk.CTkFrame(self.main_container, fg_color="transparent")
        heading.grid(row=1, column=0, sticky="ew", padx=16, pady=(20, 0))
        self.lbl_page_title = ctk.CTkLabel(
            heading, text="Device overview", font=ctk.CTkFont(size=28, weight="bold"),
        )
        self.lbl_page_title.pack(anchor="w")
        self.lbl_page_description = ctk.CTkLabel(
            heading, text="", text_color=THEME_TEXT_SECONDARY_DARK,
            font=ctk.CTkFont(size=13),
        )
        self.lbl_page_description.pack(anchor="w", pady=(2, 0))
        self.view_host = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.view_host.grid(row=2, column=0, sticky="nsew")
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
        titles = {
            "dashboard": ("Device overview", "Your device, its vitals, and the tools you use most."),
            "packages": ("Packages", "Install, inspect, and manage the apps on your device."),
            "files": ("File explorer", "Browse device storage and move files between Android and your PC."),
            "flashing": ("Flash & sideload", "Install recovery packages and write Fastboot partition images."),
            "terminal": ("Terminal", "Run shell commands with presets and command history."),
            "logcat": ("Logcat", "Follow device logs, filter messages, and export a session."),
            "tools": ("Wireless & screen", "Connect over Wi-Fi, capture the screen, or start mirroring."),
        }
        title, description = titles[name]
        self.lbl_page_title.configure(text=title)
        self.lbl_page_description.configure(text=description)
        # Update button highlights
        for key, btn in self.nav_buttons.items():
            if key == name:
                btn.configure(fg_color="#203a47", text_color=THEME_ACCENT)
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
        count = len(self.devices)
        self.lbl_connection.configure(
            text=f"●  {count} device{'s' if count != 1 else ''} detected" if count else "●  Waiting for a device",
            text_color=COLOR_SUCCESS if count else THEME_TEXT_SECONDARY_DARK,
        )
        if not self.devices:
            self.cmb_devices.configure(values=["No devices connected"])
            self.cmb_devices.set("No devices connected")
        else:
            options = [self._device_label(d) for d in self.devices]
            self.cmb_devices.configure(values=options)

            if device_manager.selected_device:
                self.cmb_devices.set(self._device_label(device_manager.selected_device))
            else:
                self.cmb_devices.set(options[0])

        # Notify active view
        current_view = self.views.get(self.active_view_name)
        if current_view and hasattr(current_view, "update_device"):
            current_view.update_device(device_manager.selected_device)

    @staticmethod
    def _device_label(device):
        return f"{device.model}  ·  {device.mode}  ·  {device.serial}"

    def _on_device_selected(self, choice_text: str):
        for d in self.devices:
            if self._device_label(d) == choice_text:
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
                self.btn_refresh.configure(state="normal", text="Refresh")
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

    def on_closing(self):
        from core.logcat_streamer import logcat_streamer
        logcat_streamer.stop()
        device_manager.stop_monitoring()
        self.destroy()
