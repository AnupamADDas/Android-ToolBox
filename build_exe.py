import os
import subprocess
import sys

def build():
    print("Building standalone Windows executable for Android Toolbox...")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconsole",
        "--onefile",
        "--name=Android_Toolbox",
        "--icon=assets/icon.ico",
        "--add-data=assets;assets",
        "--add-data=bin/platform-tools;bin/platform-tools",
        "--collect-all=customtkinter",
        "main.py"
    ]

    print("Running command:", " ".join(cmd))
    res = subprocess.run(cmd)
    if res.returncode == 0:
        print("\nBuild completed successfully!")
        print("Your executable is located in: dist\\Android_Toolbox.exe")
    else:
        print(f"\nBuild failed with exit code: {res.returncode}")

if __name__ == "__main__":
    build()
