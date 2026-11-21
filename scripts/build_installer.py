"""NetVision Installer Builder Script.

Automates the end-to-end installer generation:
1. Builds uninstall.exe from scripts/uninstaller_gui.py
2. Copies uninstall.exe and icon into dist/NetVision/
3. Zips dist/NetVision into installer/payload.zip
4. Builds installer/NetVision_Setup.exe from scripts/installer_gui.py with PyInstaller
"""

import os
import sys
import shutil
import zipfile
import subprocess
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"
INSTALLER_DIR = ROOT_DIR / "installer"
SCRIPTS_DIR = ROOT_DIR / "scripts"
ASSETS_DIR = ROOT_DIR / "assets"
ICON_PATH = ASSETS_DIR / "icons" / "netvision.ico"
VERSION_INFO = SCRIPTS_DIR / "windows_version_info.txt"


def step(msg: str):
    print(f"\n{'='*70}\n[STEP] {msg}\n{'='*70}")


def run_cmd(cmd, cwd=ROOT_DIR):
    print(f"Running: {' '.join(str(c) for c in cmd)}")
    res = subprocess.run(cmd, cwd=cwd, check=True)
    return res


def main():
    start_time = time.time()
    step("Validating prerequisites")

    app_onedir = DIST_DIR / "NetVision"
    if not (app_onedir / "NetVision.exe").exists():
        print(f"dist/NetVision/NetVision.exe not found. Building it first...")
        run_cmd([sys.executable, str(SCRIPTS_DIR / "build_exe.py")])

    INSTALLER_DIR.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------
    # Step 1: Build uninstaller executable
    # -------------------------------------------------------------
    step("Building standalone uninstaller (uninstall.exe)")
    uninst_script = SCRIPTS_DIR / "uninstaller_gui.py"
    uninst_work = BUILD_DIR / "uninst_build"
    uninst_dist = BUILD_DIR / "uninst_dist"
    
    cmd_uninst = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        f"--name=uninstall",
        f"--icon={ICON_PATH}",
        f"--workpath={uninst_work}",
        f"--distpath={uninst_dist}",
        str(uninst_script)
    ]
    run_cmd(cmd_uninst)

    built_uninst = uninst_dist / "uninstall.exe"
    if not built_uninst.exists():
        raise RuntimeError("Failed to build uninstall.exe")

    # Copy uninstaller and icon into onedir bundle
    shutil.copy2(built_uninst, app_onedir / "uninstall.exe")
    shutil.copy2(ICON_PATH, app_onedir / "netvision.ico")
    print(f"Copied uninstall.exe and netvision.ico into {app_onedir}")

    # -------------------------------------------------------------
    # Step 2: Create payload.zip
    # -------------------------------------------------------------
    step("Compressing application distribution into installer payload.zip")
    payload_zip = INSTALLER_DIR / "payload.zip"
    if payload_zip.exists():
        payload_zip.unlink()

    with zipfile.ZipFile(payload_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for root, dirs, files in os.walk(app_onedir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(app_onedir)
                zf.write(file_path, arcname)

    payload_size_mb = payload_zip.stat().st_size / (1024 * 1024)
    print(f"Created payload.zip: {payload_size_mb:.1f} MB")

    # -------------------------------------------------------------
    # Step 3: Build NetVision_Setup.exe
    # -------------------------------------------------------------
    step("Compiling NetVision_Setup.exe wizard")
    installer_script = SCRIPTS_DIR / "installer_gui.py"
    installer_work = BUILD_DIR / "installer_build"

    cmd_installer = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        f"--name=NetVision_Setup",
        f"--icon={ICON_PATH}",
        f"--version-file={VERSION_INFO}",
        f"--add-data={payload_zip};.",
        f"--add-data={ICON_PATH};assets/icons",
        f"--workpath={installer_work}",
        f"--distpath={INSTALLER_DIR}",
        str(installer_script)
    ]
    run_cmd(cmd_installer)

    final_setup = INSTALLER_DIR / "NetVision_Setup.exe"
    if not final_setup.exists():
        raise RuntimeError("NetVision_Setup.exe build failed!")

    setup_size_mb = final_setup.stat().st_size / (1024 * 1024)
    elapsed = time.time() - start_time

    step("BUILD COMPLETED SUCCESSFULLY")
    print(f"Installer built at: {final_setup}")
    print(f"Size: {setup_size_mb:.1f} MB")
    print(f"Total time elapsed: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
