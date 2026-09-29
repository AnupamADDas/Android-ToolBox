import os
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import Optional, List
from core.device_manager import device_manager
from core.package_manager import package_manager, AppPackage
from utils.constants import (
    MODE_DEVICE, THEME_CARD_DARK, THEME_TEXT_SECONDARY_DARK,
    COLOR_SUCCESS, COLOR_DANGER
)

class AppsView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.device = None
        self.all_packages: List[AppPackage] = []
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # 1. Install APK Bar
        self.install_card = ctk.CTkFrame(self, corner_radius=8, fg_color=THEME_CARD_DARK)
        self.install_card.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 8))
        self.install_card.grid_columnconfigure(0, weight=1)

        install_top = ctk.CTkFrame(self.install_card, fg_color="transparent")
        install_top.grid(row=0, column=0, padx=15, pady=(10, 5), sticky="ew")
        install_top.grid_columnconfigure(0, weight=1)

        self.entry_apk = ctk.CTkEntry(install_top, placeholder_text="Select or drop .apk file to install...")
        self.entry_apk.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        self.btn_browse_apk = ctk.CTkButton(
            install_top, text="Browse APK", width=110, command=self._browse_apk
        )
        self.btn_browse_apk.grid(row=0, column=1, padx=(0, 8), sticky="e")

        self.btn_install_apk = ctk.CTkButton(
            install_top, text="Install APK", width=120, command=self._install_apk
        )
        self.btn_install_apk.grid(row=0, column=2, sticky="e")

        # Options checkboxes
        opts_frame = ctk.CTkFrame(self.install_card, fg_color="transparent")
        opts_frame.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="w")

        self.chk_reinstall = ctk.CTkCheckBox(opts_frame, text="Reinstall (-r)", height=20, checkbox_width=18, checkbox_height=18)
        self.chk_reinstall.grid(row=0, column=0, padx=(0, 15))
        self.chk_reinstall.select()

        self.chk_grant_perms = ctk.CTkCheckBox(opts_frame, text="Grant Permissions (-g)", height=20, checkbox_width=18, checkbox_height=18)
        self.chk_grant_perms.grid(row=0, column=1, padx=(0, 15))
        self.chk_grant_perms.select()

        self.chk_downgrade = ctk.CTkCheckBox(opts_frame, text="Allow Downgrade (-d)", height=20, checkbox_width=18, checkbox_height=18)
        self.chk_downgrade.grid(row=0, column=2, padx=(0, 15))

        # 2. Package List Controls (Filter & Search)
        self.filter_card = ctk.CTkFrame(self, corner_radius=8, fg_color=THEME_CARD_DARK)
        self.filter_card.grid(row=1, column=0, sticky="ew", padx=15, pady=4)
        self.filter_card.grid_columnconfigure(1, weight=1)

        self.seg_filter = ctk.CTkSegmentedButton(
            self.filter_card,
            values=["3rd Party", "All", "System", "Disabled"],
            command=self._on_filter_changed
        )
        self.seg_filter.grid(row=0, column=0, padx=15, pady=8, sticky="w")
        self.seg_filter.set("3rd Party")

        self.entry_search = ctk.CTkEntry(self.filter_card, placeholder_text="Search package ID...")
        self.entry_search.grid(row=0, column=1, padx=(8, 8), pady=8, sticky="ew")
        self.entry_search.bind("<KeyRelease>", lambda e: self._filter_and_render_list())

        self.btn_refresh = ctk.CTkButton(
            self.filter_card, text="Refresh", width=80, command=self.load_packages
        )
        self.btn_refresh.grid(row=0, column=2, padx=(0, 15), pady=8, sticky="e")

        # 3. Scrollable List of Packages
        self.scroll_frame = ctk.CTkScrollableFrame(self, corner_radius=8, fg_color=THEME_CARD_DARK)
        self.scroll_frame.grid(row=2, column=0, sticky="nsew", padx=15, pady=(4, 15))
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        self._show_message("No packages loaded.")

    def _clear_list(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

    def _show_message(self, message: str):
        self._clear_list()
        lbl = ctk.CTkLabel(
            self.scroll_frame, text=message, text_color=THEME_TEXT_SECONDARY_DARK
        )
        lbl.grid(row=0, column=0, padx=20, pady=30)

    def update_device(self, device):
        self.device = device
        if not device or device.mode != MODE_DEVICE:
            self.all_packages.clear()
            msg = "Connect a device booted in Android OS to manage applications."
            if device and device.mode != MODE_DEVICE:
                msg = f"Device is in {device.mode.upper()} mode. Package Manager requires booted Android OS."
            self._show_message(msg)
            return

        self.load_packages()

    def _on_filter_changed(self, value):
        self.load_packages()

    def load_packages(self):
        if not self.device or self.device.mode != MODE_DEVICE:
            return

        filter_val = self.seg_filter.get()
        f_map = {
            "3rd Party": "3rd_party",
            "All": "all",
            "System": "system",
            "Disabled": "disabled"
        }
        f_type = f_map.get(filter_val, "3rd_party")

        self.btn_refresh.configure(state="disabled", text="Loading...")

        def _worker():
            pkgs = package_manager.list_packages(filter_type=f_type, serial=self.device.serial)
            self.all_packages = pkgs
            self.after(0, self._render_packages)

        threading.Thread(target=_worker, daemon=True).start()

    def _render_packages(self):
        self.btn_refresh.configure(state="normal", text="Refresh")
        self._filter_and_render_list()

    def _filter_and_render_list(self):
        query = self.entry_search.get().strip().lower()

        filtered = [
            p for p in self.all_packages
            if query in p.package_id.lower() or query in p.display_name.lower()
        ]

        if not filtered:
            self._show_message("No packages match your search." if query else "No packages found in this category.")
            return

        self._clear_list()
        for idx, pkg in enumerate(filtered[:150]):  # Cap rendering to 150 for high performance
            row_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent", height=38)
            row_frame.grid(row=idx, column=0, sticky="ew", padx=8, pady=2)
            row_frame.grid_columnconfigure(0, weight=1)

            # Package label
            pkg_text = pkg.package_id
            if pkg.is_system:
                pkg_text += " [System]"
            lbl = ctk.CTkLabel(
                row_frame, text=pkg_text, anchor="w", font=ctk.CTkFont(size=12)
            )
            lbl.grid(row=0, column=0, padx=5, sticky="w")

            # Actions
            btn_actions = ctk.CTkFrame(row_frame, fg_color="transparent")
            btn_actions.grid(row=0, column=1, sticky="e")

            btn_run = ctk.CTkButton(
                btn_actions, text="Launch", width=60, height=26, font=ctk.CTkFont(size=11),
                command=lambda p=pkg.package_id: self._launch_app(p)
            )
            btn_run.grid(row=0, column=0, padx=2)

            btn_clear = ctk.CTkButton(
                btn_actions, text="Clear", width=55, height=26, font=ctk.CTkFont(size=11),
                fg_color="#374151", command=lambda p=pkg.package_id: self._clear_app(p)
            )
            btn_clear.grid(row=0, column=1, padx=2)

            btn_pull = ctk.CTkButton(
                btn_actions, text="Extract", width=60, height=26, font=ctk.CTkFont(size=11),
                fg_color="#374151", command=lambda p=pkg.package_id: self._extract_app(p)
            )
            btn_pull.grid(row=0, column=2, padx=2)

            btn_uninst = ctk.CTkButton(
                btn_actions, text="Uninstall", width=70, height=26, font=ctk.CTkFont(size=11),
                fg_color=COLOR_DANGER, hover_color="#dc2626",
                command=lambda p=pkg.package_id, sys=pkg.is_system: self._uninstall_app(p, sys)
            )
            btn_uninst.grid(row=0, column=3, padx=2)

    def _browse_apk(self):
        f = filedialog.askopenfilename(title="Select APK File", filetypes=[("APK Files", "*.apk")])
        if f:
            self.entry_apk.delete(0, "end")
            self.entry_apk.insert(0, f)

    def _install_apk(self):
        apk_path = self.entry_apk.get().strip()
        if not apk_path or not os.path.isfile(apk_path):
            messagebox.showwarning("Install APK", "Please select a valid APK file first.")
            return

        if not self.device or self.device.mode != MODE_DEVICE:
            messagebox.showwarning("Install APK", "No Android OS device connected.")
            return

        self.btn_install_apk.configure(state="disabled", text="Installing...")

        reinstall = bool(self.chk_reinstall.get())
        grant_perms = bool(self.chk_grant_perms.get())
        downgrade = bool(self.chk_downgrade.get())

        def _worker():
            code, out = package_manager.install_apk(
                apk_path=apk_path,
                reinstall=reinstall,
                grant_permissions=grant_perms,
                downgrade=downgrade,
                serial=self.device.serial
            )
            def _done():
                self.btn_install_apk.configure(state="normal", text="Install APK")
                if code == 0 and "Success" in out:
                    messagebox.showinfo("Install APK", f"App installed successfully!\n{os.path.basename(apk_path)}")
                    self.load_packages()
                else:
                    messagebox.showerror("Installation Failed", out)
            self.after(0, _done)

        threading.Thread(target=_worker, daemon=True).start()

    def _launch_app(self, package_id: str):
        threading.Thread(target=lambda: package_manager.launch(package_id, self.device.serial), daemon=True).start()

    def _clear_app(self, package_id: str):
        if not messagebox.askyesno("Clear Data", f"Clear all cache and user data for:\n{package_id}?"):
            return
        threading.Thread(target=lambda: package_manager.clear_data(package_id, self.device.serial), daemon=True).start()

    def _extract_app(self, package_id: str):
        dest = filedialog.askdirectory(title=f"Select destination folder for {package_id}.apk")
        if not dest:
            return

        def _worker():
            code, out = package_manager.extract_apk(package_id, dest, self.device.serial)
            if code == 0:
                self.after(0, lambda: messagebox.showinfo("APK Extracted", out))
            else:
                self.after(0, lambda: messagebox.showerror("Extraction Failed", out))

        threading.Thread(target=_worker, daemon=True).start()

    def _uninstall_app(self, package_id: str, is_system: bool):
        msg = f"Are you sure you want to uninstall:\n{package_id}?"
        if is_system:
            msg += "\n\n(This is a system package. It will be uninstalled for User 0 debloat without data loss)."

        if not messagebox.askyesno("Confirm Uninstall", msg):
            return

        def _worker():
            code, out = package_manager.uninstall(package_id, keep_data_debloat=is_system, serial=self.device.serial)
            def _done():
                if code == 0 and "Success" in out:
                    messagebox.showinfo("Uninstall", f"Uninstalled {package_id}")
                    self.load_packages()
                else:
                    messagebox.showerror("Uninstall Failed", out)
            self.after(0, _done)

        threading.Thread(target=_worker, daemon=True).start()
