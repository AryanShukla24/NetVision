"""NetVision Windows Setup Wizard.

A professional, standalone installer wizard for NetVision:
- Installs to %LOCALAPPDATA%\\Programs\\NetVision (per-user, no admin elevation required)
- Custom install directory selection with free space checking
- Creates Desktop and Start Menu shortcuts
- Generates uninstaller and registers in Windows Control Panel ("Installed apps")
- Option to launch application immediately after installation
"""

import os
import sys
import shutil
import zipfile
import winreg
import subprocess
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QIcon, QFont, QPixmap
from PySide6.QtWidgets import (
    QApplication, QWizard, QWizardPage, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QProgressBar,
    QFileDialog, QMessageBox, QFrame
)

APP_NAME = "NetVision"
APP_DISPLAY_NAME = "NetVision – Smart Network Quality & Wi-Fi Coverage Analyzer"
APP_VERSION = "2.0.0"
PUBLISHER = "NetVision Team"
ESTIMATED_SIZE_MB = 210


def get_default_install_dir() -> Path:
    local_app = os.environ.get("LOCALAPPDATA", "")
    if local_app:
        return Path(local_app) / "Programs" / APP_NAME
    return Path.home() / "AppData" / "Local" / "Programs" / APP_NAME


def get_desktop_dir() -> Path:
    return Path(os.environ.get("USERPROFILE", "")) / "Desktop"


def get_start_menu_dir() -> Path:
    return Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / APP_NAME


def get_payload_path() -> Path:
    """Finds payload.zip in PyInstaller bundle or project tree."""
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)
        payload = base / "payload.zip"
        if payload.exists():
            return payload
    
    # Development fallbacks
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir.parent / "installer" / "payload.zip",
        script_dir / "payload.zip",
    ]
    for c in candidates:
        if c.exists():
            return c
    return script_dir.parent / "installer" / "payload.zip"


def create_windows_shortcut(target_path: Path, shortcut_path: Path, icon_path: Path = None, description: str = "", working_dir: Path = None):
    shortcut_path.parent.mkdir(parents=True, exist_ok=True)
    ps_script = f"""
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut('{str(shortcut_path)}')
$Shortcut.TargetPath = '{str(target_path)}'
$Shortcut.WorkingDirectory = '{str(working_dir or target_path.parent)}'
$Shortcut.Description = '{description}'
"""
    if icon_path and icon_path.exists():
        ps_script += f"$Shortcut.IconLocation = '{str(icon_path)},0'\n"
    ps_script += "$Shortcut.Save()\n"

    startupinfo = None
    creationflags = 0
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

    subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", "-"],
        input=ps_script,
        text=True,
        capture_output=True,
        check=True,
        startupinfo=startupinfo,
        creationflags=creationflags,
    )


def register_uninstaller(install_dir: Path):
    """Registers NetVision in HKCU Uninstall key for Windows Control Panel."""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\NetVision"
    try:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_DISPLAY_NAME)
        winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, APP_VERSION)
        winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, PUBLISHER)
        winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(install_dir))
        
        exe_path = install_dir / "NetVision.exe"
        ico_path = install_dir / "assets" / "icons" / "netvision.ico"
        uninst_path = install_dir / "uninstall.exe"
        
        if ico_path.exists():
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, f'"{str(ico_path)}",0')
        elif exe_path.exists():
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, f'"{str(exe_path)}",0')
            
        winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'"{str(uninst_path)}"')
        winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "EstimatedSize", 0, winreg.REG_DWORD, ESTIMATED_SIZE_MB * 1024)
        winreg.CloseKey(key)
    except Exception as e:
        print(f"Warning: Failed to write uninstall registry key: {e}")


class ExtractionThread(QThread):
    progress = Signal(int, str)
    finished_signal = Signal(bool, str)

    def __init__(self, payload_path: Path, target_dir: Path, create_desktop: bool, create_start_menu: bool):
        super().__init__()
        self.payload_path = payload_path
        self.target_dir = target_dir
        self.create_desktop = create_desktop
        self.create_start_menu = create_start_menu

    def run(self):
        try:
            self.progress.emit(5, "Preparing installation directory...")
            self.target_dir.mkdir(parents=True, exist_ok=True)

            if not self.payload_path.exists():
                self.finished_signal.emit(False, f"Payload package not found: {self.payload_path}")
                return

            self.progress.emit(15, "Opening application payload...")
            with zipfile.ZipFile(self.payload_path, "r") as zf:
                infolist = zf.infolist()
                total = len(infolist)
                for idx, item in enumerate(infolist):
                    zf.extract(item, self.target_dir)
                    percent = int(15 + (idx / max(total, 1)) * 65)
                    if idx % 15 == 0 or idx == total - 1:
                        self.progress.emit(percent, f"Extracting: {item.filename}")

            self.progress.emit(85, "Configuring shortcuts and system integration...")
            target_exe = self.target_dir / "NetVision.exe"
            icon_path = self.target_dir / "assets" / "icons" / "netvision.ico"
            if not icon_path.exists():
                icon_path = self.target_dir / "netvision.ico"

            # Desktop shortcut
            if self.create_desktop:
                try:
                    desktop_lnk = get_desktop_dir() / "NetVision.lnk"
                    create_windows_shortcut(
                        target_path=target_exe,
                        shortcut_path=desktop_lnk,
                        icon_path=icon_path if icon_path.exists() else target_exe,
                        description="NetVision – Smart Network Quality & Wi-Fi Coverage Analyzer"
                    )
                except Exception as e:
                    print(f"Failed to create desktop shortcut: {e}")

            # Start menu shortcut
            if self.create_start_menu:
                try:
                    start_menu_dir = get_start_menu_dir()
                    sm_lnk = start_menu_dir / "NetVision.lnk"
                    create_windows_shortcut(
                        target_path=target_exe,
                        shortcut_path=sm_lnk,
                        icon_path=icon_path if icon_path.exists() else target_exe,
                        description="NetVision – Smart Network Quality & Wi-Fi Coverage Analyzer"
                    )
                    
                    # Uninstaller shortcut
                    uninst_exe = self.target_dir / "uninstall.exe"
                    if uninst_exe.exists():
                        uninst_lnk = start_menu_dir / "Uninstall NetVision.lnk"
                        create_windows_shortcut(
                            target_path=uninst_exe,
                            shortcut_path=uninst_lnk,
                            description="Uninstall NetVision"
                        )
                except Exception as e:
                    print(f"Failed to create Start Menu shortcuts: {e}")

            self.progress.emit(95, "Registering uninstaller in Windows...")
            register_uninstaller(self.target_dir)

            self.progress.emit(100, "Installation completed successfully.")
            self.finished_signal.emit(True, "")
        except Exception as e:
            self.finished_signal.emit(False, str(e))


class WelcomePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Welcome to NetVision Setup")
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        welcome_label = QLabel(
            f"<h2>Welcome to the {APP_DISPLAY_NAME} Setup Wizard</h2>"
            f"<p>This wizard will guide you through installing <b>NetVision {APP_VERSION}</b> on your computer.</p>"
            f"<p><b>Key Highlights:</b></p>"
            f"<ul>"
            f"<li>Real-time ICMP ping latency & dual-probe packet loss tracking</li>"
            f"<li>Wi-Fi signal strength analysis & interactive RF heatmap mapping</li>"
            f"<li>Single & multi-stream network speed testing</li>"
            f"<li>Automated Executive Summary & Technical PDF reporting</li>"
            f"</ul>"
            f"<p><b>Note:</b> NetVision installs into your user profile and does not require administrator privileges.</p>"
            f"<p>Click <b>Next</b> to continue.</p>"
        )
        welcome_label.setWordWrap(True)
        welcome_label.setStyleSheet("font-size: 13px; line-height: 1.5; color: #1e293b;")
        layout.addWidget(welcome_label)


class DirectoryPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Select Installation Folder")
        self.setSubTitle("Choose the folder in which to install NetVision.")

        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        info = QLabel("Setup will install NetVision into the following folder:")
        info.setStyleSheet("color: #334155; font-size: 13px;")
        layout.addWidget(info)

        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit(str(get_default_install_dir()))
        self.path_edit.setStyleSheet("padding: 6px; font-size: 13px; border: 1px solid #cbd5e1; border-radius: 4px;")
        self.path_edit.textChanged.connect(self._update_space_info)
        path_layout.addWidget(self.path_edit)

        browse_btn = QPushButton("Browse...")
        browse_btn.setStyleSheet("padding: 6px 14px; font-size: 13px;")
        browse_btn.clicked.connect(self._browse)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)

        self.space_label = QLabel()
        self.space_label.setStyleSheet("color: #64748b; font-size: 12px;")
        layout.addWidget(self.space_label)
        self._update_space_info()

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #e2e8f0; margin: 10px 0;")
        layout.addWidget(sep)

        sc_title = QLabel("Shortcut Options:")
        sc_title.setStyleSheet("font-weight: 600; color: #1e293b;")
        layout.addWidget(sc_title)

        self.cb_desktop = QCheckBox("Create a Desktop shortcut")
        self.cb_desktop.setChecked(True)
        layout.addWidget(self.cb_desktop)

        self.cb_start_menu = QCheckBox("Create a Start Menu shortcut")
        self.cb_start_menu.setChecked(True)
        layout.addWidget(self.cb_start_menu)

        layout.addStretch()

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, "Select Installation Directory", self.path_edit.text())
        if d:
            self.path_edit.setText(str(Path(d) / APP_NAME))

    def _update_space_info(self):
        try:
            target = Path(self.path_edit.text())
            parent = target.parent if not target.exists() else target
            while not parent.exists() and parent.parent != parent:
                parent = parent.parent
            usage = shutil.disk_usage(parent)
            free_mb = int(usage.free / (1024 * 1024))
            self.space_label.setText(f"Space required: ~{ESTIMATED_SIZE_MB} MB   |   Space available: {free_mb:,} MB")
        except Exception:
            self.space_label.setText(f"Space required: ~{ESTIMATED_SIZE_MB} MB")

    def get_target_path(self) -> Path:
        return Path(self.path_edit.text()).resolve()


class InstallPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Installing NetVision")
        self.setSubTitle("Please wait while NetVision is being installed on your computer...")
        self.is_installed = False

        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        self.status_label = QLabel("Initializing setup...")
        self.status_label.setStyleSheet("color: #334155; font-size: 13px;")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                text-align: center;
                height: 22px;
            }
            QProgressBar::chunk {
                background-color: #0284c7;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)

        self.detail_label = QLabel("")
        self.detail_label.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(self.detail_label)

        layout.addStretch()

    def initializePage(self):
        self.wizard().button(QWizard.BackButton).setEnabled(False)
        self.wizard().button(QWizard.NextButton).setEnabled(False)
        self.wizard().button(QWizard.CancelButton).setEnabled(False)

        dir_page = self.wizard().page(1)
        target_dir = dir_page.get_target_path()
        create_desktop = dir_page.cb_desktop.isChecked()
        create_start_menu = dir_page.cb_start_menu.isChecked()

        payload = get_payload_path()

        self.worker = ExtractionThread(payload, target_dir, create_desktop, create_start_menu)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.start()

    def _on_progress(self, val: int, msg: str):
        self.progress_bar.setValue(val)
        self.detail_label.setText(msg)

    def _on_finished(self, success: bool, err_msg: str):
        if success:
            self.status_label.setText("Installation completed successfully!")
            self.detail_label.setText("Click Next to finalize.")
            self.is_installed = True
            self.wizard().button(QWizard.NextButton).setEnabled(True)
            self.wizard().next()
        else:
            self.status_label.setText(f"Installation failed: {err_msg}")
            self.detail_label.setText("Please review the error and retry.")
            QMessageBox.critical(self, "Installation Failed", f"Setup encountered an error:\n{err_msg}")
            self.wizard().button(QWizard.CancelButton).setEnabled(True)

    def isComplete(self):
        return self.is_installed


class FinishedPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Completing NetVision Setup")
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        finish_label = QLabel(
            f"<h2>Completing the {APP_DISPLAY_NAME} Setup Wizard</h2>"
            f"<p>NetVision has been successfully installed on your computer.</p>"
            f"<p>You can launch NetVision from the Desktop shortcut, Start Menu, or directly from this wizard.</p>"
        )
        finish_label.setWordWrap(True)
        finish_label.setStyleSheet("font-size: 13px; line-height: 1.5; color: #1e293b;")
        layout.addWidget(finish_label)

        self.launch_cb = QCheckBox("Launch NetVision now")
        self.launch_cb.setChecked(True)
        self.launch_cb.setStyleSheet("font-size: 13px; font-weight: 500; color: #0f172a;")
        layout.addWidget(self.launch_cb)

        layout.addStretch()


class NetVisionInstallerWizard(QWizard):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} Setup Wizard")
        self.resize(620, 440)
        self.setWizardStyle(QWizard.ModernStyle)
        
        # Set app icon if available
        base_dir = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent
        icon_path = base_dir / "assets" / "icons" / "netvision.ico"
        if not icon_path.exists():
            icon_path = base_dir / "netvision.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.page_welcome = WelcomePage()
        self.page_dir = DirectoryPage()
        self.page_install = InstallPage()
        self.page_finish = FinishedPage()

        self.setPage(0, self.page_welcome)
        self.setPage(1, self.page_dir)
        self.setPage(2, self.page_install)
        self.setPage(3, self.page_finish)

    def accept(self):
        # Called when Finish button is clicked
        if self.page_finish.launch_cb.isChecked():
            target_exe = self.page_dir.get_target_path() / "NetVision.exe"
            if target_exe.exists():
                try:
                    subprocess.Popen([str(target_exe)], cwd=str(self.page_dir.get_target_path()))
                except Exception as e:
                    print(f"Failed to launch NetVision: {e}")
        super().accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    wizard = NetVisionInstallerWizard()
    wizard.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
