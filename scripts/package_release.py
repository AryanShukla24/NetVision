"""Release packager for NetVision.

Creates clean distributables:
1. NetVision_Setup.zip (contains NetVision_Setup.exe + User Guide)
2. NetVision_Portable.zip (contains NetVision_Portable.exe + User Guide)
3. NetVision_Full_Project.zip (contains the full repository with src, tests, docs, assets, scripts, excluding venv and build caches)
"""

import os
import zipfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
PARENT_DIR = ROOT_DIR.parent

INSTALLER_EXE = ROOT_DIR / "installer" / "NetVision_Setup.exe"
PORTABLE_EXE = ROOT_DIR / "dist" / "NetVision_Portable.exe"
SETUP_GUIDE = ROOT_DIR / "docs" / "SETUP_INSTRUCTIONS.md"
README_FILE = ROOT_DIR / "README.md"


def make_installer_zip():
    zip_path = PARENT_DIR / "NetVision_Installer_Bundle.zip"
    print(f"Creating {zip_path.name}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        if INSTALLER_EXE.exists():
            zf.write(INSTALLER_EXE, "NetVision_Setup.exe")
        if SETUP_GUIDE.exists():
            zf.write(SETUP_GUIDE, "HOW_TO_INSTALL.md")
        if README_FILE.exists():
            zf.write(README_FILE, "README.md")
    print(f"-> Created {zip_path.name}: {zip_path.stat().st_size / (1024*1024):.1f} MB")


def make_portable_zip():
    zip_path = PARENT_DIR / "NetVision_Portable_Bundle.zip"
    print(f"Creating {zip_path.name}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        if PORTABLE_EXE.exists():
            zf.write(PORTABLE_EXE, "NetVision_Portable.exe")
        if SETUP_GUIDE.exists():
            zf.write(SETUP_GUIDE, "HOW_TO_RUN.md")
        if README_FILE.exists():
            zf.write(README_FILE, "README.md")
    print(f"-> Created {zip_path.name}: {zip_path.stat().st_size / (1024*1024):.1f} MB")


def make_full_project_zip():
    zip_path = PARENT_DIR / "NetVision_Complete_Source_and_Binaries.zip"
    legacy_zip = PARENT_DIR / "NetVision.zip"
    print(f"Creating {zip_path.name}...")

    excluded_dirs = {
        "venv", ".venv", "build", ".pytest_cache", "__pycache__", "reports_output"
    }
    excluded_files = {
        "uninstall.spec", "NetVision_Setup.spec", "payload.zip"
    }

    def should_include(path: Path) -> bool:
        rel = path.relative_to(ROOT_DIR)
        parts = rel.parts
        for p in parts:
            if p in excluded_dirs or p.endswith(".egg-info") or p.endswith(".pyc"):
                return False
        if path.name in excluded_files:
            return False
        return True

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for root, dirs, files in os.walk(ROOT_DIR):
            for file in files:
                file_path = Path(root) / file
                if should_include(file_path):
                    arcname = Path("NetVision") / file_path.relative_to(ROOT_DIR)
                    zf.write(file_path, arcname)

    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"-> Created {zip_path.name}: {size_mb:.1f} MB")

    # Also update legacy NetVision.zip
    import shutil
    shutil.copy2(zip_path, legacy_zip)
    print(f"-> Updated {legacy_zip.name}: {legacy_zip.stat().st_size / (1024*1024):.1f} MB")


def main():
    make_installer_zip()
    make_portable_zip()
    make_full_project_zip()
    print("\nAll distribution packages created successfully!")


if __name__ == "__main__":
    main()
