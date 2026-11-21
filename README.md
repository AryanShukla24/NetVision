# NetVision – Smart Network Quality & Wi-Fi Coverage Analyzer

[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-blue.svg)](https://microsoft.com/windows)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-brightgreen.svg)](https://python.org)
[![Framework](https://img.shields.io/badge/Framework-PySide6%20%28Qt%206%29-green.svg)](https://doc.qt.io/qtforpython/)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-46%20Passed-success.svg)](#running-automated-tests)

**NetVision** is an advanced, production-grade Windows desktop application for network performance diagnostics, Wi-Fi coverage visualization, and automated technical reporting. Designed for network administrators, IT engineers, and academic defense, NetVision performs non-destructive, genuine real-time network measurements using native Windows subsystems, multi-threaded background workers, and persistent SQLite storage.

---

## Key Features

- **Genuine ICMP Latency & Jitter Probes:**
  Direct execution of Windows native ICMP ping with millisecond-resolution regex parsing, variance/jitter calculation, and dual-probe packet loss tracking. Never synthesizes or approximates loss.
- **Dedicated TCP Fallback Probes:**
  Explicit, separate TCP three-way handshake socket latency checks (`socket.connect_ex`) for ICMP-restricted corporate networks, clearly labeled and kept isolated from ICMP RTT datasets.
- **Wi-Fi Scanner & Signal Quality Analyzer:**
  Real-time scanning via `netsh wlan show networks mode=bssid`, mapping SSIDs, BSSIDs, Signal %, dBm equivalents, PHY radio types (802.11ax/ac/n), and channel frequency assignments.
- **Interactive RF Wi-Fi Heatmap:**
  Multi-room Wi-Fi signal coverage mapping featuring Gaussian Radial Basis Function (RBF) spatial interpolation, interactive sample plotting, and image export.
- **Multi-Stream Throughput Testing:**
  Genuine HTTP chunked payload stream testing across single and parallel streams, measuring true downstream transfer rates and throughput variance.
- **Persistent SQLite Telemetry with WAL Mode:**
  Multi-table relational schema tracking latency samples, loss events, and Wi-Fi audits with zero database locking (`PRAGMA journal_mode=WAL`).
- **Automated PDF & CSV Reporting:**
  One-click generation of professional Executive Summary and Technical Audit PDF reports via ReportLab with embedded telemetry tables and Matplotlib trend charts.
- **Clean Enterprise Architecture & User-Data Isolation:**
  Zero administrative rights required for ordinary execution. Application binaries install into `%LOCALAPPDATA%\Programs\NetVision`, while databases, logs, reports, and caches reside cleanly in `%LOCALAPPDATA%\NetVision\`.

---

## Installation & Distribution

NetVision offers two distribution formats for Windows 10 and 11:

### 1. Windows Setup Wizard (Recommended)
Download and launch `NetVision_Setup.exe`:
- **Path:** `installer/NetVision_Setup.exe`
- **Installation Directory:** `%LOCALAPPDATA%\Programs\NetVision` (Per-user, no UAC elevation required)
- **Features:** Installs application files, creates Desktop and Start Menu shortcuts with high-resolution icons, and registers cleanly in Windows "Installed apps" Control Panel.
- **Uninstaller:** Includes `uninstall.exe` with safe user-data preservation prompts.

### 2. Standalone Portable Executable
Run directly without installation from any folder or USB drive:
- **Path:** `dist/NetVision_Portable.exe`
- Automatically manages runtime data and stores persistent databases under `%LOCALAPPDATA%\NetVision`.
- Requires zero Python or external dependencies.

---

## Developer Quick Start

For software engineers modifying the codebase or running inside VS Code:

### Prerequisites
- Windows 10 or Windows 11 (64-bit)
- Python 3.10, 3.11, or 3.12 (with `py` launcher or added to `PATH`)

### One-Click Development Launch
Simply double-click `run_netvision.bat` in the project root. The launcher will:
1. Detect Python 3.10+.
2. Automatically create a local virtual environment (`venv/`) if absent.
3. Install or update dependencies from `requirements.txt`.
4. Launch the application.

### Manual Setup
```powershell
# Clone or navigate to repository root
cd NetVision

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install runtime and testing dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Launch NetVision
python main.py
```

---

## Project Structure

The project adheres to the standard Python `src/` layout for clean packaging and dependency isolation:

```text
NetVision/
├── src/
│   └── netvision/               # Main application package
│       ├── __init__.py          # Package metadata and version info
│       ├── config.py            # LocalAppData path resolver and directory setup
│       ├── core/                # Core measurement services (non-GUI)
│       │   ├── latency_monitor.py      # ICMP ping & TCP latency probes
│       │   ├── wifi_scanner.py         # netsh wlan scanner & parsing
│       │   ├── speed_test.py           # Multi-stream HTTP throughput engine
│       │   ├── report_generator.py     # ReportLab PDF report builder
│       │   └── export_manager.py       # CSV and JSON telemetry exporter
│       ├── database/            # Persistent SQLite database layer
│       │   ├── db_manager.py           # SQLite connection pool & migrations
│       │   └── schema.py               # Table definitions & DDL scripts
│       └── ui/                  # PySide6 desktop GUI
│           ├── main_window.py          # Shell window, sidebar, and status bar
│           ├── components/             # Reusable UI widgets & live charts
│           │   ├── chart_widget.py     # Matplotlib live canvas
│           │   └── ...
│           └── pages/                  # Navigation pages
│               ├── dashboard_page.py   # System overview & live telemetry
│               ├── latency_page.py     # Latency graphs & packet loss tracking
│               ├── wifi_page.py        # Wi-Fi network inspector
│               ├── heatmap_page.py     # Interactive RF signal heatmap
│               ├── speedtest_page.py   # Bandwidth test controls & gauge
│               ├── reports_page.py     # PDF report generation & export
│               ├── settings_page.py    # Target hosts & threshold options
│               └── about_page.py       # System diagnostics & telemetry
├── assets/                      # Application icons and visual assets
│   ├── icons/                   # Multi-resolution .ico (16px to 256px) and .png
│   └── images/                  # Architecture diagrams and UI screenshots
├── data/                        # Template SQLite database (seeded on first run)
├── docs/                        # Comprehensive documentation
│   ├── PROJECT_ARCHITECTURE.md  # Detailed technical design & subsystem diagrams
│   ├── SETUP_INSTRUCTIONS.md    # End-user and developer deployment guide
│   └── VIVA_QUESTIONS_AND_ANSWERS.md # BTech viva defense guide (60+ Q&A)
├── installer/                   # Installer builds and scripts
│   ├── NetVision_Setup.exe      # Standalone Windows GUI installer
│   ├── NetVision_Setup.iss      # Inno Setup 6 compiler script
│   └── payload.zip              # Compressed distribution bundle
├── scripts/                     # Build automation and helper scripts
│   ├── build_exe.py             # PyInstaller onedir and onefile compiler
│   ├── build_exe.bat            # One-click batch runner for build_exe.py
│   ├── build_installer.py       # Compiles uninstaller, payload, and setup wizard
│   ├── build_installer.bat      # One-click batch runner for build_installer.py
│   ├── compile_inno_setup.bat   # Helper script to compile .iss via ISCC
│   ├── installer_gui.py         # PySide6 Setup Wizard source code
│   └── uninstaller_gui.py       # PySide6 Uninstaller source code
├── tests/                       # Automated test suite (pytest)
│   ├── test_latency_monitor.py
│   ├── test_wifi_scanner.py
│   ├── test_speed_test.py
│   ├── test_database.py
│   ├── test_report_generator.py
│   └── test_user_data_and_config.py
├── CHANGELOG.md                 # Complete development history
├── FINAL_VERIFICATION_REPORT.md # Verification logs and benchmark results
├── pyproject.toml               # Build system and pytest configuration
├── requirements.txt             # Pinned runtime dependencies
├── requirements-dev.txt         # Development & testing dependencies
├── run_netvision.bat            # Portable Windows launcher for development
└── run_tests.bat                # Automated test runner batch script
```

---

## User Data & Directory Isolation

NetVision strictly decouples program files from persistent user data. The application requires **zero write permissions** in `Program Files` or the PyInstaller temporary extraction directory:

| Component | Filesystem Location | Description |
| :--- | :--- | :--- |
| **User Database** | `%LOCALAPPDATA%\NetVision\database\netvision.db` | Persistent SQLite database in WAL mode |
| **Application Logs** | `%LOCALAPPDATA%\NetVision\logs\netvision.log` | Rotating diagnostic logs |
| **Generated Reports** | `%LOCALAPPDATA%\NetVision\reports\` | Generated PDF audit and executive reports |
| **CSV/JSON Exports** | `%LOCALAPPDATA%\NetVision\exports\` | Exported measurement tables |
| **User Configuration** | `%LOCALAPPDATA%\NetVision\config\settings.json` | Persistent user preferences & probe targets |
| **Cache & Heatmaps** | `%LOCALAPPDATA%\NetVision\cache\` | Cached interpolation rasters and temporary files |

---

## Building Executables & Installers

Build scripts are fully automated and self-contained:

### 1. Build Windows EXEs (PyInstaller)
```cmd
scripts\build_exe.bat
```
Generates:
- `dist/NetVision/NetVision.exe`: Onedir distribution folder with bundled Qt DLLs and uninstaller.
- `dist/NetVision_Portable.exe`: Standalone single-file portable executable.

### 2. Build Windows Setup Wizard
```cmd
scripts\build_installer.bat
```
Generates:
- `installer/NetVision_Setup.exe`: Standalone GUI setup wizard that installs NetVision to `%LOCALAPPDATA%\Programs\NetVision`, creates Start Menu and Desktop shortcuts, and registers in Windows Control Panel.

### 3. Optional: Compile Inno Setup Script
If you have Inno Setup 6 installed on your computer:
```cmd
scripts\compile_inno_setup.bat
```
Compiles `installer/NetVision_Setup.iss` into `installer/NetVision_Setup_Inno.exe`.

---

## Running Automated Tests

Run the complete test suite using `pytest`:

```powershell
# Using the batch runner
.\run_tests.bat

# Or directly with pytest
.\venv\Scripts\pytest -v
```

All 46 unit and integration tests validate:
- ICMP latency probe parsing & RTT bounds
- Packet loss calculation & missing probe handling
- Wi-Fi BSSID regex parsing & dBm signal conversion
- Multi-stream bandwidth calculation and timeout behavior
- SQLite WAL transactions, migrations, and concurrency
- User data directory isolation and template database seeding

---

## Technical Documentation

- **[Project Architecture Guide](docs/PROJECT_ARCHITECTURE.md):** Detailed module breakdowns, sequence diagrams, and concurrency design.
- **[Setup & Deployment Guide](docs/SETUP_INSTRUCTIONS.md):** Complete end-user installation, portable execution, and developer troubleshooting.
- **[Viva Questions & Answers](docs/VIVA_QUESTIONS_AND_ANSWERS.md):** Comprehensive academic defense preparation with 60+ questions covering networking protocols, Qt thread pools, SQLite WAL internals, and RF math.
- **[Final Verification Report](FINAL_VERIFICATION_REPORT.md):** Complete validation logs across all system modules and compiled executables.

---

## Academic & Engineering Credits
Built as an advanced BTech Computer Networks engineering project demonstrating enterprise-grade Python application design, asynchronous Qt threading, and reliable network telemetry on Microsoft Windows.
