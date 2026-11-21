"""
Build a single, clean, all-in-one submission ZIP archive containing:
  1. 01_Presentation_and_Report/  -> .pptx, .docx, .pdf
  2. 02_Windows_Executables/      -> NetVision_Setup.exe, NetVision_Portable.exe
  3. 03_NetVision_Source_Project/ -> Clean source code, tests, docs, screenshots, diagrams, scripts
  4. README_PACKAGE.txt           -> Quick-start guide for the archive

Output: <workspace_root>/NetVision_All_In_One.zip
"""

from __future__ import annotations

import os
import zipfile
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = PROJECT_DIR.parent
OUTPUT_ZIP = WORKSPACE_DIR / "NetVision_All_In_One.zip"

EXCLUDED_DIRS = {
    "venv",
    ".venv",
    "build",
    "dist",
    ".pytest_cache",
    "__pycache__",
    "reports_output",
    ".git",
    ".vscode",
}

EXCLUDED_FILES = {
    "NetVision_Project_Presentation.pptx",
    "NetVision_Project_Report.docx",
    "NetVision_Project_Report.pdf",
    "NetVision_Setup.exe",
    "payload.zip",
    "screenshot_demo.db",
    "uninstall.spec",
    "NetVision_Setup.spec",
}

EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".spec"}

PACKAGE_README = """\
========================================================================
NetVision – Smart Network Quality & Wi-Fi Coverage Analyzer (v2.0.0)
Complete All-in-One Project Submission Package
========================================================================

Submitted by:
  1. Aryan Shukla  — 09117702724
  2. Aaditya Rawat — 07917702724
  3. Kushal Shedha — 08817702724

Folder Structure Inside This Archive:
------------------------------------------------------------------------
1. 01_Presentation_and_Report/
   - NetVision_Project_Presentation.pptx  (17-slide widescreen deck)
   - NetVision_Project_Report.docx        (Editable Word project report)
   - NetVision_Project_Report.pdf         (Print-ready 62-page PDF report)

2. 02_Windows_Executables/
   - NetVision_Setup.exe                  (Windows Setup Wizard — installs
                                           with Desktop & Start Menu shortcuts)
   - NetVision_Portable.exe               (Standalone portable app — double-click
                                           to run directly without installation)

3. 03_NetVision_Source_Project/
   - Full Python / PySide6 source code (src/netvision/)
   - Automated pytest test suite (tests/) — 46 passing tests
   - Complete documentation, viva Q&A, architecture docs, 12 live
     application screenshots, and 4 engineering diagrams (docs/)
   - Icons & visual assets (assets/)
   - Build, packaging, screenshot, and report scripts (scripts/)
   - Inno Setup script (installer/NetVision_Setup.iss)
   - Portable Windows launchers (run_netvision.bat, run_tests.bat)

Quick Start:
------------------------------------------------------------------------
- To run immediately without Python:
    Open 02_Windows_Executables\\ and run NetVision_Portable.exe
    (or run NetVision_Setup.exe to install on Windows 10/11).

- To run from source code (Python 3.10+):
    Extract 03_NetVision_Source_Project\\ and double-click run_netvision.bat.
"""


def add_file(zf: zipfile.ZipFile, src: Path, arcname: str, store_only: bool = False) -> None:
    compress_type = zipfile.ZIP_STORED if store_only else zipfile.ZIP_DEFLATED
    zf.write(src, arcname=arcname, compress_type=compress_type)


def build_zip() -> None:
    if OUTPUT_ZIP.exists():
        OUTPUT_ZIP.unlink()

    counts = {
        "01_Presentation_and_Report": 0,
        "02_Windows_Executables": 0,
        "03_NetVision_Source_Project": 0,
    }

    with zipfile.ZipFile(
        OUTPUT_ZIP,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=6,
        allowZip64=True,
    ) as zf:
        # Top-level guide
        zf.writestr("README_PACKAGE.txt", PACKAGE_README)

        # 1. Presentation & Report deliverables
        deliverables = [
            PROJECT_DIR / "NetVision_Project_Presentation.pptx",
            PROJECT_DIR / "NetVision_Project_Report.docx",
            PROJECT_DIR / "NetVision_Project_Report.pdf",
        ]
        for path in deliverables:
            if not path.is_file():
                raise FileNotFoundError(f"Missing deliverable: {path}")
            add_file(zf, path, f"01_Presentation_and_Report/{path.name}", store_only=False)
            counts["01_Presentation_and_Report"] += 1

        # 2. Windows Executables (already compressed internally by PyInstaller)
        executables = [
            PROJECT_DIR / "installer" / "NetVision_Setup.exe",
            PROJECT_DIR / "dist" / "NetVision_Portable.exe",
        ]
        for path in executables:
            if not path.is_file():
                raise FileNotFoundError(f"Missing executable: {path}")
            add_file(zf, path, f"02_Windows_Executables/{path.name}", store_only=True)
            counts["02_Windows_Executables"] += 1

        # 3. Clean Source Project
        for root, dirs, files in os.walk(PROJECT_DIR):
            dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_DIRS)
            root_path = Path(root)
            for fname in sorted(files):
                if fname in EXCLUDED_FILES:
                    continue
                fpath = root_path / fname
                if fpath.suffix.lower() in EXCLUDED_SUFFIXES:
                    continue
                rel = fpath.relative_to(PROJECT_DIR).as_posix()
                arcname = f"03_NetVision_Source_Project/{rel}"
                store_only = fpath.suffix.lower() in {".png", ".jpg", ".jpeg", ".ico", ".zip"}
                add_file(zf, fpath, arcname, store_only=store_only)
                counts["03_NetVision_Source_Project"] += 1

    # Integrity verification
    with zipfile.ZipFile(OUTPUT_ZIP, mode="r") as zf:
        bad_member = zf.testzip()
        if bad_member is not None:
            raise RuntimeError(f"Corrupt ZIP member detected: {bad_member}")
        total_files = len(zf.namelist())

    size_mb = OUTPUT_ZIP.stat().st_size / (1024 * 1024)
    print(f"SUCCESS: Created {OUTPUT_ZIP}")
    print(f"Archive Size : {size_mb:.2f} MB ({OUTPUT_ZIP.stat().st_size:,} bytes)")
    print(f"Total Entries: {total_files}")
    for section, cnt in counts.items():
        print(f"  - {section}: {cnt} files")
    print("CRC Integrity: PASSED (testzip() returned None)")


if __name__ == "__main__":
    build_zip()
