"""
NetVision - Continuous Signal Monitor
Polls connected Wi-Fi signal percentage, tracks stability (standard deviation, min, max),
handles disconnections cleanly without retaining stale values, and logs samples tagged with custom locations.
"""

import time
import math
import logging
from typing import List, Optional, Callable, Dict, Any, Tuple
from datetime import datetime

from netvision.core.wifi_scanner import WifiScanner
from netvision.database.models import SignalLogEntry, ConnectedInterfaceInfo
from netvision.database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


def compute_signal_stability(samples: List[int]) -> Dict[str, Any]:
    """
    Computes statistical stability metrics for signal samples:
    - mean: average signal %
    - std_dev: standard deviation (lower means more stable)
    - min_sig, max_sig, range_sig
    - stability_label: "Very Stable", "Moderate Fluctuation", "Highly Unstable"
    """
    if not samples:
        return {
            "mean": 0.0,
            "std_dev": 0.0,
            "min": 0,
            "max": 0,
            "range": 0,
            "stability_label": "No Data"
        }

    n = len(samples)
    mean_val = sum(samples) / n
    variance = sum((x - mean_val) ** 2 for x in samples) / (n if n > 1 else 1)
    std_dev = math.sqrt(variance)
    min_sig = min(samples)
    max_sig = max(samples)

    if std_dev <= 3.0:
        label = "Very Stable"
    elif std_dev <= 7.0:
        label = "Moderate Fluctuation"
    else:
        label = "Highly Unstable"

    return {
        "mean": round(mean_val, 1),
        "std_dev": round(std_dev, 2),
        "min": min_sig,
        "max": max_sig,
        "range": max_sig - min_sig,
        "stability_label": label
    }


class SignalMonitor:
    """Manages continuous polling of the active Wi-Fi connection's signal quality."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager
        self.scanner = WifiScanner()
        self._is_monitoring = False
        self.history_samples: List[int] = []
        self.history_timestamps: List[str] = []

    def monitor_tick(self, location_label: str = "Default") -> Tuple[Optional[SignalLogEntry], bool, ConnectedInterfaceInfo]:
        """
        Performs a single signal observation.
        Returns (entry, is_connected, interface_info).
        """
        info = self.scanner.get_connected_interface()
        if info.state != "connected" or not info.ssid:
            return None, False, info

        sig_pct = info.signal_percent if info.signal_percent is not None else 0
        entry = SignalLogEntry(
            network_ssid=info.ssid,
            bssid=info.bssid,
            signal_percent=sig_pct,
            channel=info.channel,
            frequency_band=info.frequency_band,
            location_label=location_label,
            timestamp=datetime.now().isoformat()
        )

        self.history_samples.append(sig_pct)
        self.history_timestamps.append(entry.timestamp)

        # Retain last 300 samples in memory
        if len(self.history_samples) > 300:
            self.history_samples.pop(0)
            self.history_timestamps.pop(0)

        if self.db:
            try:
                self.db.save_signal_log(entry)
            except Exception as e:
                logger.error(f"Error saving signal log: {e}")

        return entry, True, info

    def get_stability_summary(self) -> Dict[str, Any]:
        """Returns the stability statistics of the currently accumulated sample window."""
        return compute_signal_stability(self.history_samples)

    def clear_history(self) -> None:
        """Clears in-memory session samples."""
        self.history_samples.clear()
        self.history_timestamps.clear()
