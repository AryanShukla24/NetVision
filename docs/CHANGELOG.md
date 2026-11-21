# NetVision — Changelog & Engineering Audit Resolution

All notable technical fixes, architecture repairs, and submission readiness enhancements are documented in this changelog.

---

## [Version 2.0.0] — Comprehensive Repair, Restructure & Distribution Release

### 1. Professional Project Organization (`src/` Layout)
- Restructured development repository into standard Python `src/netvision` layout.
- Modularized architecture into `core/`, `database/`, `ui/`, `ui/components/`, `ui/pages/`.
- Isolated test suite into `tests/` with `pytest` configuration in `pyproject.toml`.
- Placed documentation into `docs/` and build automation into `scripts/`.
- Segregated visual assets into `assets/icons/` and `assets/images/`.

### 2. User-Data Separation (`%LOCALAPPDATA%\NetVision`)
- Decoupled application binaries from dynamic user telemetry:
  - Database: `%LOCALAPPDATA%\NetVision\database\netvision.db`
  - Logs: `%LOCALAPPDATA%\NetVision\logs\netvision.log`
  - Reports: `%LOCALAPPDATA%\NetVision\reports\`
  - Exports: `%LOCALAPPDATA%\NetVision\exports\`
  - Config: `%LOCALAPPDATA%\NetVision\config\settings.json`
  - Cache: `%LOCALAPPDATA%\NetVision\cache\`
- Safe first-run initialization: automatically seeds database from `data/netvision.db` without overwriting existing user data.
- Works cleanly without administrator elevation on Windows 10 and 11.

### 3. Windows Executable Compilation (PyInstaller)
- Authored `scripts/build_exe.py` and `scripts/build_exe.bat`.
- Built onedir release bundle: `dist/NetVision/NetVision.exe`.
- Built standalone portable single-file executable: `dist/NetVision_Portable.exe`.
- Configured Windows PE version metadata via `scripts/windows_version_info.txt` (Product Name, Description, Version 2.0.0, Publisher).
- Bundled Qt plugins, Matplotlib data, and ReportLab resources.

### 4. Turnkey Windows Setup Wizard & Inno Setup Support
- Developed `scripts/installer_gui.py`: A native PySide6 Setup Wizard compiled to `installer/NetVision_Setup.exe`.
  - Installs to `%LOCALAPPDATA%\Programs\NetVision` (no UAC admin prompt required).
  - Custom install location selection with disk space validation.
  - Generates Desktop and Start Menu shortcuts.
  - Registers in Windows "Installed apps" Control Panel.
  - Offers immediate post-install application launch.
- Developed `scripts/uninstaller_gui.py`: Standalone uninstaller (`uninstall.exe`) with safe user-data preservation prompts.
- Authored `installer/NetVision_Setup.iss` for Inno Setup 6 compilation and created `scripts/compile_inno_setup.bat`.

### 5. Application Branding & Identity Overhaul
- Designed and embedded genuine multi-resolution Windows icon (`assets/icons/netvision.ico`: 16, 24, 32, 48, 64, 128, 256 px) and high-res PNG (`assets/icons/netvision.png`).
- Applied icon globally across main window, taskbar, dialogs, desktop shortcuts, uninstaller, and setup wizard.
- Removed all academic viva prep text and tabs from the application UI.
- Overhauled About Page into a technical System Architecture, Diagnostic Diagnostics, and Real-time Telemetry Dashboard.

### 6. Portable Windows Installation & Launcher
- Resolved developer environment portability by eliminating machine-specific bundled virtual environments.
- Dynamic Batch Launcher (`run_netvision.bat`): Auto-detects Python 3.10+, bootstraps `venv/`, installs dependencies, and executes `main.py`.
- Strict dependency segregation in `requirements.txt` and `requirements-dev.txt`.

### 7. Measurement Integrity & Latency
- Dropped ICMP packets are recorded honestly as lost probes, never masked by fallback connections.
- Strict target host validation using regex to prevent command injection and option flags.
- Microsecond ping parsing handling `time<1ms` (0.5 ms), `time=Xms`, and locale variations.
- Genuine Jitter Calculation using ITU Mean Consecutive Difference and RFC 3550 interarrival jitter.
- Schema migration mechanism with `schema_version` tracking in `DatabaseManager`.

### 8. Wi-Fi Scanner & Connected Interface Detection
- Integrated Windows Native WLAN API (`ctypes.windll.wlanapi.WlanScan`) to trigger active hardware spectrum scans.
- Segmented multi-interface parsing in `netsh wlan show interfaces` to prevent disconnected virtual adapters from masking physical Wi-Fi cards.
- Extracted genuine Default Gateway, DNS servers, and Local IPv4 via `netsh interface ip show config`.
- Resolved BSSID matching so identical SSIDs on different radios map to their exact connected BSSID.

### 9. Speed Tester & Background Workers
- Multi-chunk streaming download and upload against CDN edge nodes.
- Excluded initial 1 MB warmup chunk from download throughput calculation to eliminate TCP slow-start skew.
- Implemented chunked 64 KB upload streaming with responsive thread cancellation.
- All network I/O isolated onto dedicated `QThread` workers with Qt Signal/Slot communication.

### 10. RF Channel Analyzer & Congestion Scoring
- Implemented IEEE 802.11 spectral overlap weighting on 2.4 GHz channels.
- Segregated 2.4 GHz, 5 GHz, and 6 GHz spectrum analyses into dedicated views.
- Documented OS Wi-Fi card limitations regarding non-802.11 RF energy.

### 11. Multi-Location Comparison & Empirical Experiments
- Multi-location checkbox comparison with unrestricted relational querying.
- Empirical multi-trial experiment engine with Pearson correlation coefficient ($r$) and scatter plotting.

### 12. Automated Testing Suite Expansion
- 46 comprehensive unit and integration tests across:
  - Latency and packet loss tracking
  - Wi-Fi scanning and interface parsing
  - Multi-stream bandwidth testing
  - Database schema, WAL mode, and migrations
  - ReportLab PDF generation
  - User-data directory isolation and template seeding
