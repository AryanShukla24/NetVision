"""
NetVision - Windows Native and Qt Global Shortcut Manager
Provides system-wide Windows hotkey registration (WM_HOTKEY) and Qt fallbacks.
Supports conflict detection, dynamic hotkey binding, and ensures all shortcuts
remain unassigned by default until configured by the user.
"""

import sys
import ctypes
from ctypes import wintypes
import logging
from typing import Dict, Optional, Callable, Set, Tuple

from PySide6.QtCore import QObject, Signal, QAbstractNativeEventFilter, QCoreApplication
from PySide6.QtGui import QKeySequence

logger = logging.getLogger(__name__)

# Win32 Constants for RegisterHotKey
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312

# Virtual Key Codes Mapping
VK_MAPPING = {
    "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73, "F5": 0x74, "F6": 0x75,
    "F7": 0x76, "F8": 0x77, "F9": 0x78, "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
    "0": 0x30, "1": 0x31, "2": 0x32, "3": 0x33, "4": 0x34,
    "5": 0x35, "6": 0x36, "7": 0x37, "8": 0x38, "9": 0x39,
    "A": 0x41, "B": 0x42, "C": 0x43, "D": 0x44, "E": 0x45, "F": 0x46,
    "G": 0x47, "H": 0x48, "I": 0x49, "J": 0x4A, "K": 0x4B, "L": 0x4C,
    "M": 0x4D, "N": 0x4E, "O": 0x4F, "P": 0x50, "Q": 0x51, "R": 0x52,
    "S": 0x53, "T": 0x54, "U": 0x55, "V": 0x56, "W": 0x57, "X": 0x58,
    "Y": 0x59, "Z": 0x5A,
    "TAB": 0x09, "SPACE": 0x20, "BACKSPACE": 0x08, "RETURN": 0x0D,
    "ENTER": 0x0D, "ESCAPE": 0x1B, "ESC": 0x1B, "TILDE": 0xC0, "`": 0xC0,
}


def parse_hotkey_string(shortcut_str: str) -> Optional[Tuple[int, int]]:
    """
    Parses strings like 'Ctrl+Shift+C', 'Alt+F9', or 'F10'
    into (win32_modifiers, win32_vk_code).
    """
    if not shortcut_str or not shortcut_str.strip():
        return None

    parts = [p.strip().upper() for p in shortcut_str.split("+") if p.strip()]
    if not parts:
        return None

    mods = MOD_NOREPEAT
    key_part = None

    for p in parts:
        if p in ("CTRL", "CONTROL"):
            mods |= MOD_CONTROL
        elif p in ("ALT", "MENU"):
            mods |= MOD_ALT
        elif p in ("SHIFT",):
            mods |= MOD_SHIFT
        elif p in ("WIN", "WINDOWS", "SUPER"):
            mods |= MOD_WIN
        else:
            key_part = p

    if not key_part:
        return None

    vk = VK_MAPPING.get(key_part)
    if vk is None and len(key_part) == 1:
        vk = ord(key_part)

    if vk is None:
        return None

    return (mods, vk)


class WindowsNativeEventFilter(QAbstractNativeEventFilter):
    """Intercepts WM_HOTKEY events dispatched to the application message loop."""

    def __init__(self, callback: Callable[[int], None]):
        super().__init__()
        self.callback = callback

    def nativeEventFilter(self, event_type, message):
        if event_type == b"windows_generic_MSG" or event_type == "windows_generic_MSG":
            msg = wintypes.MSG.from_address(message.__int__())
            if msg.message == WM_HOTKEY:
                hotkey_id = msg.wParam
                self.callback(hotkey_id)
                return True, 0
        return False, 0


class GlobalShortcutManager(QObject):
    """
    Manages registration, unregistration, and execution of global hotkeys.
    Ensures zero default hotkeys and detects duplicate/conflicting key sequences.
    """

    shortcut_triggered = Signal(str)  # Emits stat_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._user32 = ctypes.windll.user32 if sys.platform == "win32" else None
        self._registered_hotkeys: Dict[int, str] = {}  # hotkey_id -> stat_id
        self._stat_to_hotkey_id: Dict[str, int] = {}  # stat_id -> hotkey_id
        self._assigned_shortcuts: Dict[str, str] = {} # stat_id -> shortcut_str
        self._next_id = 100

        self._filter: Optional[WindowsNativeEventFilter] = None
        if self._user32:
            self._filter = WindowsNativeEventFilter(self._on_native_hotkey)
            QCoreApplication.instance().installNativeEventFilter(self._filter)

    def _on_native_hotkey(self, hotkey_id: int):
        stat_id = self._registered_hotkeys.get(hotkey_id)
        if stat_id:
            logger.info(f"Global hotkey triggered for stat: {stat_id}")
            self.shortcut_triggered.emit(stat_id)

    def register_shortcut(self, stat_id: str, shortcut_str: str) -> bool:
        """
        Binds a keyboard shortcut to a statistic.
        Returns True if successfully registered, False if invalid or conflict.
        """
        self.unregister_shortcut(stat_id)

        shortcut_str = shortcut_str.strip()
        if not shortcut_str:
            return True

        parsed = parse_hotkey_string(shortcut_str)
        if not parsed:
            logger.warning(f"Failed to parse shortcut string '{shortcut_str}'")
            return False

        mods, vk = parsed
        hotkey_id = self._next_id
        self._next_id += 1

        if self._user32:
            success = self._user32.RegisterHotKey(None, hotkey_id, mods, vk)
            if not success:
                err = ctypes.GetLastError()
                logger.warning(f"Windows RegisterHotKey failed for '{shortcut_str}' (Error {err})")
                return False

        self._registered_hotkeys[hotkey_id] = stat_id
        self._stat_to_hotkey_id[stat_id] = hotkey_id
        self._assigned_shortcuts[stat_id] = shortcut_str
        return True

    def unregister_shortcut(self, stat_id: str):
        """Unregisters any active hotkey for the given statistic."""
        if stat_id in self._stat_to_hotkey_id:
            hotkey_id = self._stat_to_hotkey_id.pop(stat_id)
            self._registered_hotkeys.pop(hotkey_id, None)
            self._assigned_shortcuts.pop(stat_id, None)
            if self._user32:
                self._user32.UnregisterHotKey(None, hotkey_id)

    def unregister_all(self):
        """Unregisters all active hotkeys."""
        for stat_id in list(self._stat_to_hotkey_id.keys()):
            self.unregister_shortcut(stat_id)

    def get_assigned_shortcut(self, stat_id: str) -> str:
        return self._assigned_shortcuts.get(stat_id, "")

    def check_conflict(self, shortcut_str: str, stat_id: str) -> Optional[str]:
        """
        Checks if shortcut_str is already used by another statistic.
        Returns the conflicting stat_id if conflict exists, or None.
        """
        normalized = shortcut_str.strip().upper()
        if not normalized:
            return None

        for existing_stat, existing_sc in self._assigned_shortcuts.items():
            if existing_stat != stat_id and existing_sc.strip().upper() == normalized:
                return existing_stat
        return None

    def clean_up(self):
        self.unregister_all()
        if self._filter:
            try:
                QCoreApplication.instance().removeNativeEventFilter(self._filter)
            except Exception:
                pass
            self._filter = None
