"""NetVision Uninstaller.

Provides a clean uninstallation experience:
- Prompts for confirmation
- Preserves user data (%LOCALAPPDATA%\\NetVision) by default
- Removes Desktop and Start Menu shortcuts
- Removes HKCU Uninstall registry key
- Cleans up installed files via detached process
"""

import os
import sys
import shutil
import winreg
import subprocess
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QFont
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QCheckBox, QMessageBox, QFrame
)


def get_desktop_dir() -> Path:
    return Path(os.environ.get("USERPROFILE", "")) / "Desktop"


def get_start_menu_dir() -> Path:
    return Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "NetVision"


def get_user_data_dir() -> Path:
    local_app = os.environ.get("LOCALAPPDATA", "")
    return Path(local_app) / "NetVision" if local_app else Path.home() / ".netvision"


def remove_shortcuts():
    # Remove desktop shortcut
    desktop_lnk = get_desktop_dir() / "NetVision.lnk"
    if desktop_lnk.exists():
        try:
            desktop_lnk.unlink()
        except Exception:
            pass

    # Remove Start Menu shortcut folder
    start_menu = get_start_menu_dir()
    if start_menu.exists():
        try:
            shutil.rmtree(start_menu, ignore_errors=True)
        except Exception:
            pass


def remove_registry_entry():
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\NetVision"
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
    except FileNotFoundError:
        pass
    except Exception:
        pass


def schedule_directory_removal(install_dir: Path):
    """Spawns a detached process to remove the install dir after this process exits."""
    bat_content = f"""@echo off
timeout /t 2 /nobreak > nul
rmdir /s /q "{install_dir}"
del "%~f0"
"""
    temp_dir = os.environ.get("TEMP", os.path.expanduser("~"))
    bat_path = Path(temp_dir) / "netvision_uninstall_cleanup.bat"
    try:
        bat_path.write_text(bat_content, encoding="utf-8")
        startupinfo = None
        creationflags = 0
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        subprocess.Popen(
            ["cmd.exe", "/c", str(bat_path)],
            startupinfo=startupinfo,
            creationflags=creationflags,
            stdin=subprocess.DEVNULL,
            close_fds=True
        )
    except Exception:
        pass


class UninstallerDialog(QDialog):
    def __init__(self, install_dir: Path):
        super().__init__()
        self.install_dir = install_dir
        self.setWindowTitle("NetVision Uninstaller")
        self.setFixedSize(500, 320)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # Set icon if available
        icon_path = self.install_dir / "assets" / "icons" / "netvision.ico"
        if not icon_path.exists():
            icon_path = self.install_dir / "netvision.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QLabel("Uninstall NetVision")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setStyleSheet("color: #0f172a;")
        layout.addWidget(header)

        # Message
        msg = QLabel(
            f"Are you sure you want to uninstall NetVision and all of its components from your computer?\n\n"
            f"Installation Location:\n{self.install_dir}"
        )
        msg.setWordWrap(True)
        msg.setStyleSheet("color: #475569; font-size: 13px; line-height: 1.4;")
        layout.addWidget(msg)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color: #e2e8f0;")
        layout.addWidget(divider)

        # Option: Remove user data
        self.remove_user_data_cb = QCheckBox(
            "Also delete saved network scan history, databases, and reports\n"
            f"({get_user_data_dir()})"
        )
        self.remove_user_data_cb.setChecked(False)  # Safe by default!
        self.remove_user_data_cb.setStyleSheet("color: #dc2626; font-size: 12px;")
        layout.addWidget(self.remove_user_data_cb)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedSize(90, 34)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: #f1f5f9;
                color: #334155;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover { background: #e2e8f0; }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.uninstall_btn = QPushButton("Uninstall")
        self.uninstall_btn.setFixedSize(100, 34)
        self.uninstall_btn.setStyleSheet("""
            QPushButton {
                background: #ef4444;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover { background: #dc2626; }
            QPushButton:pressed { background: #b91c1c; }
        """)
        self.uninstall_btn.clicked.connect(self._do_uninstall)
        btn_layout.addWidget(self.uninstall_btn)

        layout.addLayout(btn_layout)

    def _do_uninstall(self):
        self.uninstall_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.repaint()

        try:
            # 1. Remove shortcuts
            remove_shortcuts()

            # 2. Remove registry entry
            remove_registry_entry()

            # 3. Remove user data if explicitly requested
            if self.remove_user_data_cb.isChecked():
                user_data = get_user_data_dir()
                if user_data.exists():
                    shutil.rmtree(user_data, ignore_errors=True)

            # 4. Schedule cleanup of the installation folder
            schedule_directory_removal(self.install_dir)

            QMessageBox.information(
                self,
                "Uninstall Complete",
                "NetVision has been successfully uninstalled from your computer.",
                QMessageBox.Ok
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Uninstall Error",
                f"An error occurred during uninstallation:\n{e}",
                QMessageBox.Ok
            )
            self.reject()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Determine install dir (directory containing uninstaller)
    if getattr(sys, "frozen", False):
        install_dir = Path(sys.executable).resolve().parent
    else:
        install_dir = Path(__file__).resolve().parent.parent

    dialog = UninstallerDialog(install_dir)
    dialog.exec()


if __name__ == "__main__":
    main()
