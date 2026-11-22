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
import hashlib
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"
INSTALLER_DIR = ROOT_DIR / "installer"
RELEASES_DIR = ROOT_DIR / "Releases"
SCRIPTS_DIR = ROOT_DIR / "scripts"
ASSETS_DIR = ROOT_DIR / "assets"
ICON_PATH = ASSETS_DIR / "icons" / "netvision.ico"
VERSION_INFO = SCRIPTS_DIR / "windows_version_info.txt"


def sha256_file(path: Path) -> str:
    """Calculates SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


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
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtWidgets",
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
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtWidgets",
        str(installer_script)
    ]
    run_cmd(cmd_installer)

    final_setup = INSTALLER_DIR / "NetVision_Setup.exe"
    if not final_setup.exists():
        raise RuntimeError("NetVision_Setup.exe build failed!")

    setup_size_mb = final_setup.stat().st_size / (1024 * 1024)

    # -------------------------------------------------------------
    # Step 4: Package Releases/ deliverables
    # -------------------------------------------------------------
    step("Packaging Releases deliverables")
    RELEASES_DIR.mkdir(parents=True, exist_ok=True)

    # 4a. Copy installer to Releases/NetVision-Setup.exe
    releases_setup = RELEASES_DIR / "NetVision-Setup.exe"
    shutil.copy2(final_setup, releases_setup)
    print(f"Copied installer to: {releases_setup} ({releases_setup.stat().st_size / (1024*1024):.1f} MB)")

    # 4b. Create Releases/NetVision-Portable.zip
    step("Creating Releases/NetVision-Portable.zip")
    portable_zip_path = RELEASES_DIR / "NetVision-Portable.zip"
    if portable_zip_path.exists():
        portable_zip_path.unlink()

    # Create optional launcher batch script in app_onedir
    launcher_bat = app_onedir / "Launch NetVision.bat"
    launcher_bat.write_text('@echo off\r\nstart "" "%~dp0NetVision.exe"\r\n', encoding="utf-8")

    readme_release = RELEASES_DIR / "README.txt"

    with zipfile.ZipFile(portable_zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        # Include README.txt inside the root folder
        if readme_release.exists():
            zf.write(readme_release, "NetVision-Portable/README.txt")

        for root, dirs, files in os.walk(app_onedir):
            for file in files:
                # Do not include installer-only uninstaller in portable package
                if file.lower() == "uninstall.exe":
                    continue
                file_path = Path(root) / file
                rel_path = file_path.relative_to(app_onedir)
                arcname = Path("NetVision-Portable") / rel_path
                zf.write(file_path, arcname)

    # Clean temporary launcher batch from dist folder
    if launcher_bat.exists():
        launcher_bat.unlink()

    portable_size_mb = portable_zip_path.stat().st_size / (1024 * 1024)
    print(f"Created portable zip: {portable_zip_path} ({portable_size_mb:.1f} MB)")

    elapsed = time.time() - start_time

    # -------------------------------------------------------------
    # Step 5: Verification and Checksums
    # -------------------------------------------------------------
    step("DISTRIBUTION PACKAGING COMPLETED SUCCESSFULLY")
    print(f"Total time elapsed: {elapsed:.1f}s\n")
    print("Release Deliverables Summary:")
    print("-" * 80)
    for p in (releases_setup, portable_zip_path, readme_release):
        if p.exists():
            size_mb = p.stat().st_size / (1024 * 1024)
            sha = sha256_file(p)
            print(f"File   : {p.name}")
            print(f"Path   : {p}")
            print(f"Size   : {size_mb:.2f} MB ({p.stat().st_size:,} bytes)")
            print(f"SHA-256: {sha}")
            print("-" * 80)


if __name__ == "__main__":
    main()
