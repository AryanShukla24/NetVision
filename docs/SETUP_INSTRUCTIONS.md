# NetVision — Setup & Installation Guide

This document provides complete instructions for both **End Users** (running pre-built executables or installers) and **Software Developers** (setting up the Python development environment, running tests, and building binaries).

---

## Part 1: End-User Installation Guide

NetVision provides two turnkey deployment options for Windows 10 and 11. **Neither option requires Python or administrative privileges.**

### Option A: Windows Setup Wizard (Recommended)
1. Locate or download `installer/NetVision_Setup.exe`.
2. Double-click `NetVision_Setup.exe` to launch the Setup Wizard.
3. Follow the on-screen steps:
   - **Destination Folder:** Default is `%LOCALAPPDATA%\Programs\NetVision` (installs cleanly into your user profile).
   - **Shortcuts:** Choose whether to create Desktop and Start Menu shortcuts.
   - **Installation:** Files are extracted and the uninstaller is registered in Windows Control Panel.
4. Check **"Launch NetVision now"** and click **Finish**.
5. You can now launch NetVision anytime from your Start Menu or Desktop.

### Option B: Standalone Portable Executable
1. Locate `dist/NetVision_Portable.exe`.
2. Copy it anywhere on your computer (e.g., Desktop, Documents, or USB drive).
3. Double-click `NetVision_Portable.exe` to run.
4. It operates completely standalone and stores your network history safely in `%LOCALAPPDATA%\NetVision\database\`.

### How to Uninstall NetVision
- Go to **Windows Settings > Apps > Installed apps** (or Control Panel > Programs and Features).
- Locate **NetVision – Smart Network Quality & Wi-Fi Coverage Analyzer**.
- Click **Uninstall**.
- The uninstaller gives you the option to preserve your scan history and reports (default) or delete them.

---

## Part 2: Developer Environment Setup

For software engineers modifying the code or running inside VS Code / PyCharm:

### System Requirements
- **OS:** Windows 10 (64-bit) or Windows 11 (64-bit)
- **Python:** Python 3.10, 3.11, or 3.12 (64-bit)
- **Wi-Fi Card:** Standard 802.11b/g/n/ac/ax wireless network adapter
- **WLAN Service:** Windows WLAN AutoConfig (`wlansvc`) running

### 1. Automatic One-Click Launcher
Double-click `run_netvision.bat` in the project root. The batch file will:
1. Locate Python 3.10+ using `py -3` or `python`.
2. Automatically create `venv/` if absent.
3. Install all dependencies from `requirements.txt`.
4. Launch `main.py`.

### 2. Manual Terminal Setup
```powershell
# 1. Navigate to project root
cd NetVision

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 4. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 5. Launch application
python main.py
```

---

## Part 3: Running Automated Tests

Run the complete 46-test test suite to verify core logic, database transactions, and data isolation:

```powershell
# Using the batch runner
.\run_tests.bat

# Or directly with pytest
.\venv\Scripts\pytest -v
```

---

## Part 4: Building Executables & Installers

### 1. Build Windows Executables
```cmd
scripts\build_exe.bat
```
Generates:
- `dist/NetVision/NetVision.exe` (`onedir` bundle)
- `dist/NetVision_Portable.exe` (`onefile` portable standalone)

### 2. Build Windows Setup Wizard
```cmd
scripts\build_installer.bat
```
Generates:
- `installer/NetVision_Setup.exe` (Complete graphical setup wizard)

### 3. (Optional) Compile Inno Setup Script
If you have Inno Setup 6 installed:
```cmd
scripts\compile_inno_setup.bat
```
Generates:
- `installer/NetVision_Setup_Inno.exe`

---

## Part 5: User Data & Filesystem Locations

NetVision never writes runtime telemetry inside its installation directory. All dynamic files reside under `%LOCALAPPDATA%\NetVision`:

- **Database:** `%LOCALAPPDATA%\NetVision\database\netvision.db`
- **Application Logs:** `%LOCALAPPDATA%\NetVision\logs\netvision.log`
- **PDF Reports:** `%LOCALAPPDATA%\NetVision\reports\`
- **Data Exports:** `%LOCALAPPDATA%\NetVision\exports\`
- **Settings:** `%LOCALAPPDATA%\NetVision\config\settings.json`
