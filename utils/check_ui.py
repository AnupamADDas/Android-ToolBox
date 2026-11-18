"""Native UI smoke review, without ADB commands or a connected phone.

Run: python -m utils.check_ui --shots <output-directory>
"""
import argparse
import ctypes
import inspect
import os
from pathlib import Path
import tkinter
from unittest.mock import patch

import customtkinter
from PIL import ImageGrab

from core.device_manager import AndroidDevice, device_manager
from core.file_manager import RemoteFile
from core.package_manager import AppPackage
from ui.app_window import AppWindow
from ui.components import widgets as ctk


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--shots", type=Path)
    args = parser.parse_args()
    if args.shots:
        args.shots.mkdir(parents=True, exist_ok=True)

    errors = []
    # Review sizes are physical pixels; apply the explicit 125% case below
    # without also multiplying by the host monitor's DPI setting.
    customtkinter.deactivate_automatic_dpi_awareness()
    with patch.object(device_manager, "start_monitoring"):
        app = AppWindow()
    app.report_callback_exception = lambda kind, value, trace: errors.append(str(value))
    app.update()
    # Predictable logical dimensions independent of the review PC's DPI setting.
    customtkinter.set_widget_scaling(1)
    customtkinter.set_window_scaling(1)

    def settle_scaling():
        # CTk temporarily locks min/max sizes for 1000 ms after scaling changes.
        ready = tkinter.BooleanVar(master=app, value=False)
        app.after(1100, lambda: ready.set(True))
        app.wait_variable(ready)

    settle_scaling()

    def check_bounds(name):
        def check(widget):
            if not widget.winfo_viewable():
                return
            if isinstance(widget, (ctk.CTkButton, ctk.CTkEntry, ctk.CTkComboBox)):
                left = widget.winfo_rootx() - app.winfo_rootx()
                right = left + widget.winfo_width()
                if left < 0 or right > app.winfo_width():
                    errors.append(f"{name}: {type(widget).__name__} outside {app.winfo_width()}px window ({left}, {right})")
                # A child may be inside the window yet clipped by its panel.
                parent = widget.master
                parent_right = parent.winfo_rootx() + parent.winfo_width()
                if widget.winfo_rootx() + widget.winfo_width() > parent_right + 2:
                    errors.append(f"{name}: {type(widget).__name__} clipped by panel")
            for child in widget.winfo_children():
                check(child)
        check(app)

    def capture(name):
        app.update_idletasks()
        app.update()
        if args.shots:
            if os.name == "nt" and "window" in inspect.signature(ImageGrab.grab).parameters:
                # Capture this window, even if the user has another app in front.
                hwnd = ctypes.windll.user32.GetParent(app.winfo_id())
                shot = ImageGrab.grab(window=hwnd)
            else:
                app.attributes("-topmost", True)
                app.lift()
                app.update()
                x, y = app.winfo_rootx(), app.winfo_rooty()
                shot = ImageGrab.grab(bbox=(x, y, x + app.winfo_width(), y + app.winfo_height()))
                app.attributes("-topmost", False)
            shot.save(args.shots / f"{name}.png")

    try:
        for width, height in ((1240, 860), (1024, 720)):
            app.geometry(f"{width}x{height}+0+0")
            app.update()
            for name in app.views:
                app.select_view(name)
                app.update()
                capture(f"{width}-{name}")
                check_bounds(f"{width}/{name}")
            print(f"Rendered all seven views at {width}x{height}")

        app.select_view("packages")
        packages = app.views["packages"]
        packages.all_packages = [
            AppPackage("com.example.notes"),
            AppPackage("com.example.a.long.package.identifier.for.layout.verification", is_system=True),
        ]
        packages._render_packages()
        capture("1024-packages-populated-fixture")
        check_bounds("1024/packages-populated")
        packages.entry_search.insert(0, "notes")
        packages._filter_and_render_list()
        assert len(packages.scroll_frame.winfo_children()) == 1
        app.select_view("files")
        files = app.views["files"]
        files.files = [
            RemoteFile("Download", "/sdcard/Download", is_dir=True),
            RemoteFile("A long filename used to verify wrapping in the file list.txt",
                       "/sdcard/review.txt", size=2048),
        ]
        files._render_files()
        files._select_file(files.files[1])
        capture("1024-files-populated-fixture")
        check_bounds("1024/files-populated")
        assert files.file_rows["/sdcard/review.txt"].cget("fg_color") == "#203a47"
        print("Populated package/file lists, search, and selection passed")

        # Exercise keyboard activation without starting any device operation.
        button = app.nav_buttons["terminal"]
        button._canvas.focus_force()
        app.update()
        assert button.cget("border_width") == 2
        button._canvas.event_generate("<Return>")
        app.update()
        assert app.active_view_name == "terminal"
        print("Keyboard navigation and focus ring passed")

        # Device transitions use explicit fixtures, never live device operations.
        app.geometry("1240x860+0+0")
        app.select_view("dashboard")
        dashboard = app.views["dashboard"]
        phone = AndroidDevice("review-device", "device", "Android device")
        info = {
            "brand": "Android", "model": "Review device", "android_version": "15",
            "sdk_level": "35", "security_patch": "2026-10-01", "cpu_abi": "arm64-v8a",
            "resolution": "1080x2400", "density": "420", "wifi_ip": "192.168.1.10",
            "is_root": False, "build_id": "UI verification fixture",
            "battery": {"level": "76%", "status": "Charging", "temperature": "31 °C", "voltage": "4.1 V"},
        }
        app.devices = [phone]
        device_manager.selected_device = phone
        with patch("ui.views.dashboard_view.threading.Thread"):
            app._update_device_ui()
        dashboard._apply_info_ui(phone, info)
        assert dashboard.battery_progress.get() == 0.76
        capture("connected-dashboard-fixture")
        for mode in ("recovery", "fastboot", "sideload", "unauthorized", "offline"):
            phone = AndroidDevice("review-device", mode, "Android device")
            dashboard.device = phone
            dashboard._apply_info_ui(phone, {})
            assert dashboard.battery_progress.get() == 0
        dashboard.update_device(None)
        assert all(button.cget("state") == "disabled" for button in dashboard.device_buttons)
        print("Device states, battery reset, and disconnected controls passed")
        device_manager.selected_device = None
        app.devices = []
        app._update_device_ui()
        customtkinter.set_widget_scaling(1.25)
        customtkinter.set_window_scaling(1.25)
        settle_scaling()
        app.geometry("1024x720+0+0")
        for name in app.views:
            app.select_view(name)
            app.update()
            check_bounds(f"125-percent/{name}")
        print("All seven views at 125% scaling passed")
        if errors:
            raise AssertionError("\n".join(errors))
        print("UI REVIEW: PASS")
    finally:
        app.on_closing()


if __name__ == "__main__":
    main()
