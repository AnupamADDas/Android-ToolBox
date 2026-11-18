"""Build the portable executable or the directory payload used by Setup."""
import argparse
from pathlib import Path
import struct
import subprocess
import sys

from utils.constants import APP_NAME, APP_VERSION

ROOT = Path(__file__).resolve().parent


def build(onedir=False):
    if sys.platform != "win32" or struct.calcsize("P") != 8:
        raise RuntimeError("Build this Windows release with 64-bit Python on Windows.")
    for path in ("assets/icon.ico", "bin/platform-tools/adb.exe", "bin/platform-tools/fastboot.exe"):
        if not (ROOT / path).is_file():
            raise FileNotFoundError(f"Required build asset not found: {path}")

    output = ROOT / "dist" / "windows" if onedir else ROOT / "dist"
    work = ROOT / "build" / ("installer-payload" if onedir else "portable")
    work.mkdir(parents=True, exist_ok=True)
    version = tuple(int(part) for part in APP_VERSION.split("."))
    version = (version + (0, 0, 0, 0))[:4]
    version_file = work / "version-info.txt"
    version_file.write_text(
        f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers={version!r}, prodvers={version!r},
    mask=0x3f, flags=0, OS=0x40004, fileType=0x1, subtype=0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('FileDescription', {APP_NAME!r}),
      StringStruct('FileVersion', {APP_VERSION!r}),
      StringStruct('InternalName', 'Android_Toolbox'),
      StringStruct('OriginalFilename', 'Android_Toolbox.exe'),
      StringStruct('ProductName', {APP_NAME!r}),
      StringStruct('ProductVersion', {APP_VERSION!r})
    ])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ])
""",
        encoding="utf-8",
    )
    cmd = [
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
        "--noconsole", "--onedir" if onedir else "--onefile",
        "--name=Android_Toolbox", f"--icon={ROOT / 'assets' / 'icon.ico'}",
        f"--version-file={version_file}",
        f"--add-data={ROOT / 'assets'};assets",
        f"--add-data={ROOT / 'bin' / 'platform-tools'};bin/platform-tools",
        "--collect-all=customtkinter",
        f"--distpath={output}", f"--workpath={work}", f"--specpath={work}",
        str(ROOT / "main.py"),
    ]
    subprocess.run(cmd, cwd=ROOT, check=True)
    executable = output / "Android_Toolbox" / "Android_Toolbox.exe" if onedir else output / "Android_Toolbox.exe"
    print(f"\nExecutable: {executable}")
    return executable


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--onedir", action="store_true", help="Build a directory for the Windows installer")
    args = parser.parse_args()
    build(onedir=args.onedir)
