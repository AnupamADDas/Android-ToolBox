# Android Toolbox (Windows Native)

A modern, lightweight, native Windows desktop application for managing and interacting with connected Android devices over USB and Wireless ADB, with full support for **Normal Android OS**, **Custom Recovery (TWRP / OrangeFox)**, and **Fastboot (Bootloader)** modes.

---

## ✨ Features

### 1. Multi-Mode Device Detection & Management

- **Modes Detected:**
  - 🟢 **Android OS (`device`):** Full app management, specs, live battery, screen mirroring.
  - 🟠 **Custom Recovery (`recovery`):** Full unrestricted root shell, direct partition file access, recovery logs.
  - ⚡ **Sideload (`sideload`):** Flash Custom ROMs, Kernels, Magisk, and OTAs with real-time percentage progress.
  - 🔵 **Fastboot (`fastboot`):** Bootloader partition flasher and bootloader commands.
  - 🔴 **Unauthorized (`unauthorized`):** Alerts user to accept RSA key prompt on phone screen.
- **Auto-Discovery:** Automatically locates `adb.exe` and `fastboot.exe` from your local Android SDK (`%LOCALAPPDATA%\Android\Sdk\platform-tools`).

### 2. 📱 Dashboard & Specs Overview

- **System Specs:** Brand, Model, Android Version, SDK API Level, Security Patch, CPU Architecture, Screen Resolution & DPI, Wi-Fi IP address, and Root check (`su`).
- **Live Battery Stats:** Percentage, Charging State (Charging / Discharging / Full), Temperature (°C), Voltage (V).
- **Power / Reboot Controls:** Reboot to System, Recovery, Bootloader (Fastboot), FastbootD, EDL, or soft-restart SystemUI.

### 3. 📦 Package Manager & APK Installer

- **Categorized App Views:** Filter by `3rd Party (User)`, `All`, `System`, and `Disabled/Frozen`.
- **Instant Search:** Dynamic filter by package ID or app name.
- **App Actions:** Launch, Clear Data/Cache, Extract APK to PC, and Uninstall (with User 0 debloat option for system apps).
- **APK Installer:** Browse and install `.apk` files with optional flags (`-r` reinstall, `-g` grant permissions, `-d` allow downgrade).

### 4. 📁 Remote File Explorer

- **Directory Browser:** Navigate Android filesystem (Internal storage `/sdcard/`, `Downloads`, `DCIM`, or root `/`).
- **File Operations:** Push files to phone, Pull files to PC, New Folder, Delete.
- **Custom Recovery Support:** In TWRP/OrangeFox, provides raw root access to internal storage and partitions.

### 5. ⚡ Flashing & Sideload (Clean & Minimalist)

- **ADB Sideload:** Select any `.zip` file (ROM, Kernel, Magisk, OTA) and monitor live percentage transfer (`serving: 42%`).
- **Fastboot Partition Flasher:** Flash `.img` files directly to `boot`, `recovery`, `vendor_boot`, `vbmeta`, `system`, or custom partitions.
- **Recovery Log Fetcher:** 1-click fetch of `/tmp/recovery.log` to diagnose failed flashes.

### 6. 💻 Interactive Shell Terminal

- Real-time command execution with stdout/stderr streaming.
- Command history recall using **Up** and **Down** arrow keys.
- Quick preset shortcuts (`df -h`, `dumpsys meminfo`, `top -n 1`, `ip addr`).
- Automatic root access in Recovery mode, or optional `su -c` in Android OS.

### 7. 📋 Live Logcat Viewer

- Buffered real-time logcat stream without UI stutter.
- Log level color tagging: **V**erbose (Gray), **D**ebug (Blue), **I**nfo (Green), **W**arn (Amber), **E**rror (Red).
- Live tag and message search filter.
- Pause, Resume, Clear, and Export to `.log` file.

### 8. 📶 Wireless ADB & Screen Tools

- **One-Click TCPIP:** Switch USB device to wireless mode on port `5555`.
- **Wireless Connect:** Direct IP:Port connect/disconnect.
- **Android 11+ Pairing:** Pair using 6-digit Wi-Fi pairing code and port.
- **Instant Screenshot:** Capture phone screen with preview, save, or copy to clipboard.
- **Screen Mirroring:** 1-click launch of `scrcpy` for low-latency screen mirror and control.

---

## 🚀 How to Run

### Development Mode

```powershell
python main.py
```

### Build Standalone `.exe`

```powershell
python build_exe.py
```

The compiled, standalone executable will be in the `dist\ADB_Android_Toolbox.exe` directory.
