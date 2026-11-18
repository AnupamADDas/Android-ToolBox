"""Build Windows Setup. Requires 64-bit Python, PyInstaller and Inno Setup 6.6+."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess

from build_exe import ROOT, build
from utils.constants import APP_VERSION


def find_compiler(explicit=None):
    candidates = [explicit, os.environ.get("ISCC"), shutil.which("ISCC.exe")]
    for base in (
        os.environ.get("ProgramFiles", ""),
        os.environ.get("ProgramFiles(x86)", ""),
        str(Path(os.environ.get("LOCALAPPDATA", "~")) / "Programs"),
    ):
        for version in ("7", "6"):
            candidates.append(str(Path(base) / f"Inno Setup {version}" / "ISCC.exe"))
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return Path(candidate).resolve()
    raise FileNotFoundError("Install Inno Setup 6.6+ or pass --iscc <path-to-ISCC.exe>.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iscc", help="Path to the Inno Setup command-line compiler")
    args = parser.parse_args()
    compiler = find_compiler(args.iscc)
    executable = build(onedir=True)
    output = ROOT / "dist" / "installer"
    subprocess.run([
        str(compiler), f"/DAppVersion={APP_VERSION}",
        f"/DAppSource={executable.parent}", f"/DOutputPath={output}",
        str(ROOT / "installer" / "windows.iss"),
    ], cwd=ROOT, check=True)
    setup = output / f"Android-Toolbox-Setup-{APP_VERSION}-x64.exe"
    digest = hashlib.sha256(setup.read_bytes()).hexdigest()
    setup.with_suffix(".exe.sha256").write_text(f"{digest}  {setup.name}\n", encoding="ascii")
    print(f"\nInstaller: {setup}\nSHA256: {digest}")


if __name__ == "__main__":
    main()
