import os
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox, simpledialog
from typing import Optional, List
from core.device_manager import device_manager
from core.file_manager import file_manager, RemoteFile
from utils.constants import (
    MODE_DEVICE, MODE_RECOVERY, THEME_CARD_DARK, THEME_TEXT_SECONDARY_DARK,
    COLOR_SUCCESS, COLOR_DANGER
)

class FilesView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.device = None
        self.current_path = "/sdcard"
        self.files: List[RemoteFile] = []
        self.selected_file: Optional[RemoteFile] = None
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # 1. Navigation & Path Bar
        self.nav_card = ctk.CTkFrame(self, corner_radius=8, fg_color=THEME_CARD_DARK)
        self.nav_card.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 6))
        self.nav_card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.nav_card, text="Path:", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=0, column=0, padx=(15, 6), pady=10, sticky="w"
        )

        self.entry_path = ctk.CTkEntry(self.nav_card, placeholder_text="/sdcard")
        self.entry_path.grid(row=0, column=1, padx=4, pady=10, sticky="ew")
        self.entry_path.insert(0, self.current_path)
        self.entry_path.bind("<Return>", lambda e: self._navigate_to_entry())

        self.btn_go = ctk.CTkButton(self.nav_card, text="Go", width=60, command=self._navigate_to_entry)
        self.btn_go.grid(row=0, column=2, padx=4, pady=10)

        self.btn_up = ctk.CTkButton(self.nav_card, text="Up", width=55, fg_color="#374151", command=self._go_up)
        self.btn_up.grid(row=0, column=3, padx=(4, 15), pady=10)

        # Quick Jumps Row
        quick_row = ctk.CTkFrame(self.nav_card, fg_color="transparent")
        quick_row.grid(row=1, column=0, columnspan=4, padx=15, pady=(0, 10), sticky="w")

        ctk.CTkButton(quick_row, text="Internal (/sdcard)", height=24, width=110, font=ctk.CTkFont(size=11),
                      fg_color="#374151", command=lambda: self._set_path("/sdcard")).grid(row=0, column=0, padx=2)
        ctk.CTkButton(quick_row, text="Downloads", height=24, width=80, font=ctk.CTkFont(size=11),
                      fg_color="#374151", command=lambda: self._set_path("/sdcard/Download")).grid(row=0, column=1, padx=2)
        ctk.CTkButton(quick_row, text="DCIM", height=24, width=60, font=ctk.CTkFont(size=11),
                      fg_color="#374151", command=lambda: self._set_path("/sdcard/DCIM")).grid(row=0, column=2, padx=2)
        ctk.CTkButton(quick_row, text="Root (/)", height=24, width=65, font=ctk.CTkFont(size=11),
                      fg_color="#374151", command=lambda: self._set_path("/")).grid(row=0, column=3, padx=2)

        # 2. Action Toolbar
        self.action_card = ctk.CTkFrame(self, corner_radius=8, fg_color=THEME_CARD_DARK)
        self.action_card.grid(row=1, column=0, sticky="ew", padx=15, pady=4)
        self.action_card.grid_columnconfigure(5, weight=1)

        self.btn_push = ctk.CTkButton(self.action_card, text="Push File to Phone", width=130, command=self._push_file)
        self.btn_push.grid(row=0, column=0, padx=(15, 6), pady=8)

        self.btn_pull = ctk.CTkButton(self.action_card, text="Pull Selected", width=110, fg_color="#374151", command=self._pull_file)
        self.btn_pull.grid(row=0, column=1, padx=6, pady=8)

        self.btn_mkdir = ctk.CTkButton(self.action_card, text="New Folder", width=95, fg_color="#374151", command=self._new_folder)
        self.btn_mkdir.grid(row=0, column=2, padx=6, pady=8)

        self.btn_delete = ctk.CTkButton(self.action_card, text="Delete", width=80, fg_color=COLOR_DANGER, command=self._delete_selected)
        self.btn_delete.grid(row=0, column=3, padx=6, pady=8)

        self.btn_refresh = ctk.CTkButton(self.action_card, text="Refresh", width=75, fg_color="#374151", command=self.load_directory)
        self.btn_refresh.grid(row=0, column=4, padx=6, pady=8)

        self.lbl_status = ctk.CTkLabel(self.action_card, text="", font=ctk.CTkFont(size=11), text_color=THEME_TEXT_SECONDARY_DARK)
        self.lbl_status.grid(row=0, column=5, padx=15, pady=8, sticky="e")

        # 3. File Listing Container
        self.scroll_files = ctk.CTkScrollableFrame(self, corner_radius=8, fg_color=THEME_CARD_DARK)
        self.scroll_files.grid(row=2, column=0, sticky="nsew", padx=15, pady=(4, 15))
        self.scroll_files.grid_columnconfigure(0, weight=1)

        self._show_message("No device connected.")

    def _clear_list(self):
        for widget in self.scroll_files.winfo_children():
            widget.destroy()

    def _show_message(self, message: str):
        self._clear_list()
        lbl = ctk.CTkLabel(self.scroll_files, text=message, text_color=THEME_TEXT_SECONDARY_DARK)
        lbl.grid(row=0, column=0, padx=20, pady=30)

    def update_device(self, device):
        self.device = device
        if not device or device.mode not in [MODE_DEVICE, MODE_RECOVERY]:
            self.files.clear()
            msg = "Connect a device in Android OS or Recovery Mode to browse files."
            if device and device.mode not in [MODE_DEVICE, MODE_RECOVERY]:
                msg = f"File Explorer is not supported in {device.mode.upper()} mode."
            self._show_message(msg)
            return

        self.load_directory()

    def _set_path(self, path: str):
        self.current_path = path
        self.entry_path.delete(0, "end")
        self.entry_path.insert(0, path)
        self.load_directory()

    def _navigate_to_entry(self):
        p = self.entry_path.get().strip()
        if p:
            self._set_path(p)

    def _go_up(self):
        parent = os.path.dirname(self.current_path.rstrip("/"))
        if not parent:
            parent = "/"
        self._set_path(parent)

    def load_directory(self):
        if not self.device or self.device.mode not in [MODE_DEVICE, MODE_RECOVERY]:
            return

        self.lbl_status.configure(text="Loading...")

        def _worker():
            files = file_manager.list_directory(self.current_path, self.device.serial)
            self.files = files
            self.after(0, self._render_files)

        threading.Thread(target=_worker, daemon=True).start()

    def _render_files(self):
        self.selected_file = None
        self.lbl_status.configure(text=f"{len(self.files)} items")

        if not self.files:
            self._show_message("Folder is empty or permission denied.")
            return

        self._clear_list()

        for idx, f in enumerate(self.files):
            row = ctk.CTkFrame(self.scroll_files, fg_color="transparent", height=32)
            row.grid(row=idx, column=0, sticky="ew", padx=6, pady=1)
            row.grid_columnconfigure(1, weight=1)

            icon = "📁" if f.is_dir else "📄"
            lbl_icon = ctk.CTkLabel(row, text=icon, width=24)
            lbl_icon.grid(row=0, column=0, padx=(4, 2), sticky="w")

            lbl_name = ctk.CTkLabel(row, text=f.name, anchor="w", font=ctk.CTkFont(size=12))
            lbl_name.grid(row=0, column=1, sticky="w")

            lbl_size = ctk.CTkLabel(row, text=f.formatted_size, width=80, anchor="e", font=ctk.CTkFont(size=11), text_color=THEME_TEXT_SECONDARY_DARK)
            lbl_size.grid(row=0, column=2, padx=8, sticky="e")

            # Selection and double click navigation
            row.bind("<Button-1>", lambda e, item=f: self._select_file(item))
            lbl_name.bind("<Button-1>", lambda e, item=f: self._select_file(item))

            if f.is_dir:
                row.bind("<Double-Button-1>", lambda e, p=f.path: self._set_path(p))
                lbl_name.bind("<Double-Button-1>", lambda e, p=f.path: self._set_path(p))

    def _select_file(self, item: RemoteFile):
        self.selected_file = item
        self.lbl_status.configure(text=f"Selected: {item.name} ({item.formatted_size})")

    def _push_file(self):
        if not self.device:
            return
        local_file = filedialog.askopenfilename(title="Select File to Push to Phone")
        if not local_file:
            return

        self.lbl_status.configure(text=f"Pushing {os.path.basename(local_file)}...")

        def _worker():
            code, out = file_manager.push(local_file, self.current_path, self.device.serial)
            def _done():
                if code == 0:
                    self.lbl_status.configure(text="Pushed successfully.")
                    self.load_directory()
                else:
                    messagebox.showerror("Push Failed", out)
            self.after(0, _done)

        threading.Thread(target=_worker, daemon=True).start()

    def _pull_file(self):
        if not self.selected_file:
            messagebox.showwarning("Pull File", "Please select a file to pull first.")
            return

        dest_dir = filedialog.askdirectory(title="Select Local Destination Folder")
        if not dest_dir:
            return

        self.lbl_status.configure(text=f"Pulling {self.selected_file.name}...")

        def _worker():
            dest_file = os.path.join(dest_dir, self.selected_file.name)
            code, out = file_manager.pull(self.selected_file.path, dest_file, self.device.serial)
            def _done():
                if code == 0:
                    self.lbl_status.configure(text="Pulled successfully.")
                    messagebox.showinfo("File Pulled", f"File saved to:\n{dest_file}")
                else:
                    messagebox.showerror("Pull Failed", out)
            self.after(0, _done)

        threading.Thread(target=_worker, daemon=True).start()

    def _new_folder(self):
        if not self.device:
            return
        name = simpledialog.askstring("New Folder", "Enter new folder name:")
        if not name:
            return

        new_path = self.current_path.rstrip("/") + "/" + name.strip()

        def _worker():
            code, out = file_manager.mkdir(new_path, self.device.serial)
            self.after(0, self.load_directory)

        threading.Thread(target=_worker, daemon=True).start()

    def _delete_selected(self):
        if not self.selected_file:
            messagebox.showwarning("Delete", "Please select an item to delete first.")
            return

        confirm = messagebox.askyesno("Confirm Delete", f"Delete '{self.selected_file.name}'?")
        if not confirm:
            return

        def _worker():
            code, out = file_manager.delete(self.selected_file.path, is_dir=self.selected_file.is_dir, serial=self.device.serial)
            self.after(0, self.load_directory)

        threading.Thread(target=_worker, daemon=True).start()
