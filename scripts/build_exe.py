"""
NetVision - Executable Packaging Script
Builds standalone Windows executables (onedir and optional onefile) using PyInstaller.
Embeds Qt plugins, Matplotlib, ReportLab, and Windows file metadata.
"""

import sys
import os
import shutil
import subprocess
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
ASSETS_DIR = PROJECT_ROOT / "assets"
ICON_ICO = ASSETS_DIR / "icons" / "netvision.ico"
DATA_DIR = PROJECT_ROOT / "data"
BUILD_DIR = PROJECT_ROOT / "build"
DIST_DIR = PROJECT_ROOT / "dist"
VERSION_FILE = PROJECT_ROOT / "scripts" / "windows_version_info.txt"


VERSION_INFO_TEMPLATE = """# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(2, 0, 0, 0),
    prodvers=(2, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        '040904B0',
        [StringStruct('CompanyName', 'BTech CSE Academic Projects'),
        StringStruct('FileDescription', 'NetVision - Smart Network Quality & Wi-Fi Coverage Analyzer'),
        StringStruct('FileVersion', '2.0.0.0'),
        StringStruct('InternalName', 'NetVision'),
        StringStruct('LegalCopyright', 'Copyright (C) 2026 NetVision Contributors'),
        StringStruct('OriginalFilename', 'NetVision.exe'),
        StringStruct('ProductName', 'NetVision'),
        StringStruct('ProductVersion', '2.0.0.0')])
      ]), 
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""


def generate_version_file():
    """Writes Windows PE file version information."""
    VERSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        f.write(VERSION_INFO_TEMPLATE.strip())
    print(f"[BUILD] Generated version metadata: {VERSION_FILE}")


def _get_python_ssl_binary_args():
    """Returns PyInstaller --add-binary args for Python's exact matching OpenSSL DLLs."""
    args = []
    try:
        import _ssl
        dll_dir = Path(_ssl.__file__).resolve().parent
        for dll_name in ("libssl-3-x64.dll", "libcrypto-3-x64.dll"):
            dll_path = dll_dir / dll_name
            if dll_path.exists():
                args.append(f"--add-binary={dll_path};.")
    except Exception as e:
        print(f"[WARNING] Could not locate Python OpenSSL DLLs: {e}")
    return args


def build_onedir():
    """Builds PyInstaller onedir distribution (dist/NetVision/NetVision.exe)."""
    print("=" * 70)
    print("  BUILDING NETVISION ONEDIR EXECUTABLE (dist/NetVision/)")
    print("=" * 70)

    import PyInstaller.__main__

    args = [
        str(PROJECT_ROOT / "main.py"),
        "--name=NetVision",
        "--noconsole",
        "--onedir",
        f"--icon={ICON_ICO}",
        f"--version-file={VERSION_FILE}",
        f"--paths={SRC_DIR}",
        f"--add-data={ASSETS_DIR};assets",
        f"--add-data={DATA_DIR};data",
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR / 'onedir'}",
        "--specpath={}".format(PROJECT_ROOT / "build"),
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=PySide6.QtSvg",
        "--hidden-import=psutil",
        "--hidden-import=matplotlib.backends.backend_qtagg",
        "--hidden-import=reportlab",
        "--hidden-import=reportlab.platypus",
        "--hidden-import=reportlab.lib.pagesizes",
        "--hidden-import=reportlab.lib.colors",
        "--hidden-import=reportlab.lib.styles",
        "--hidden-import=requests",
        "--hidden-import=urllib3",
        "--hidden-import=sqlite3",
        "--hidden-import=ssl",
        "--hidden-import=certifi",
        "--hidden-import=xml.sax.saxutils",
        *_get_python_ssl_binary_args(),
        "--clean",
        "-y"
    ]

    PyInstaller.__main__.run(args)
    exe_path = DIST_DIR / "NetVision" / "NetVision.exe"
    if exe_path.exists():
        print(f"\n[SUCCESS] Onedir executable built: {exe_path} ({exe_path.stat().st_size:,} bytes)")
        return exe_path
    else:
        raise RuntimeError("Build finished but NetVision.exe was not found!")


def build_onefile():
    """Builds optional standalone single-file executable (dist/NetVision_Portable.exe)."""
    print("\n" + "=" * 70)
    print("  BUILDING NETVISION PORTABLE ONEFILE (dist/NetVision_Portable.exe)")
    print("=" * 70)

    import PyInstaller.__main__

    args = [
        str(PROJECT_ROOT / "main.py"),
        "--name=NetVision_Portable",
        "--noconsole",
        "--onefile",
        f"--icon={ICON_ICO}",
        f"--version-file={VERSION_FILE}",
        f"--paths={SRC_DIR}",
        f"--add-data={ASSETS_DIR};assets",
        f"--add-data={DATA_DIR};data",
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR / 'onefile'}",
        "--specpath={}".format(PROJECT_ROOT / "build"),
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=PySide6.QtSvg",
        "--hidden-import=psutil",
        "--hidden-import=matplotlib.backends.backend_qtagg",
        "--hidden-import=reportlab",
        "--hidden-import=reportlab.platypus",
        "--hidden-import=reportlab.lib.pagesizes",
        "--hidden-import=reportlab.lib.colors",
        "--hidden-import=reportlab.lib.styles",
        "--hidden-import=requests",
        "--hidden-import=urllib3",
        "--hidden-import=sqlite3",
        "--hidden-import=ssl",
        "--hidden-import=certifi",
        "--hidden-import=xml.sax.saxutils",
        *_get_python_ssl_binary_args(),
        "--clean",
        "-y"
    ]

    PyInstaller.__main__.run(args)
    onefile_path = DIST_DIR / "NetVision_Portable.exe"
    if onefile_path.exists():
        print(f"\n[SUCCESS] Onefile executable built: {onefile_path} ({onefile_path.stat().st_size:,} bytes)")
        return onefile_path
    else:
        raise RuntimeError("Onefile build finished but NetVision_Portable.exe was not found!")


if __name__ == "__main__":
    generate_version_file()
    if "--onefile" in sys.argv:
        build_onefile()
    elif "--all" in sys.argv:
        onedir_exe = build_onedir()
        try:
            onefile_exe = build_onefile()
        except Exception as e:
            print(f"[WARNING] Onefile build encountered error: {e}")
    else:
        onedir_exe = build_onedir()
