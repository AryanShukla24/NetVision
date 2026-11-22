"""
NetVision - Windows-Safe Subprocess Execution Utilities
Ensures internal OS diagnostic commands (netsh, ping) run without spawning
visible console windows when NetVision is launched as a windowed GUI executable.
"""

from __future__ import annotations

import logging
import subprocess
import sys
from typing import Any, Dict, Sequence

logger = logging.getLogger(__name__)

# Windows CreateProcess flag preventing creation of a visible console window
CREATE_NO_WINDOW_FLAG = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)


def get_hidden_subprocess_kwargs() -> Dict[str, Any]:
    """
    Returns platform-appropriate kwargs for subprocess.run / subprocess.Popen so
    Windows console utilities (netsh.exe, ping.exe, etc.) do not allocate or flash
    visible console windows when spawned from a GUI (--noconsole) process.
    """
    if sys.platform != "win32":
        return {}

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE  # 0

    return {
        "startupinfo": startupinfo,
        "creationflags": CREATE_NO_WINDOW_FLAG,
    }


def run_hidden_command(
    cmd: Sequence[str],
    timeout: float = 10.0,
    check: bool = False,
) -> subprocess.CompletedProcess:
    """
    Executes a command with shell=False, hidden Windows console configuration,
    isolated stdin (DEVNULL), and UTF-8 stdout/stderr capture.
    """
    kwargs = get_hidden_subprocess_kwargs()
    return subprocess.run(
        list(cmd),
        shell=False,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=check,
        encoding="utf-8",
        errors="replace",
        **kwargs,
    )


# Alias for backward and cross-module compatibility
run_subprocess = run_hidden_command
