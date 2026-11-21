"""
NetVision - Database Models and Data Transfer Objects (DTOs)
Type-safe dataclasses for Wi-Fi observations, tests, and metrics.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any


def get_signal_category(signal_percent: Optional[int], thresholds: Optional[Dict[str, int]] = None) -> str:
    """Centralized categorizer for Wi-Fi signal percentage."""
    if signal_percent is None or signal_percent <= 0:
        return "No Signal"

    th = thresholds or {"excellent": 75, "good": 50, "fair": 30, "poor": 0}
    if signal_percent >= th.get("excellent", 75):
        return "Excellent"
    elif signal_percent >= th.get("good", 50):
        return "Good"
    elif signal_percent >= th.get("fair", 30):
        return "Fair"
    return "Poor"


@dataclass
class WifiNetwork:
    """Represents a discovered wireless network."""
    ssid: str
    bssid: str = ""
    signal_percent: int = 0
    channel: int = 0
    frequency_band: str = "2.4 GHz"  # "2.4 GHz", "5 GHz", or "6 GHz"
    security_type: str = "Unknown"
    is_connected: bool = False
    radio_type: str = ""             # e.g., 802.11ax, 802.11ac, 802.11n
    id: Optional[int] = None
    session_id: Optional[int] = None
    observed_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def signal_category(self) -> str:
        return get_signal_category(self.signal_percent)


@dataclass
class ConnectedInterfaceInfo:
    """Represents details of the active network interface on Windows."""
    interface_name: str = ""
    description: str = ""
    guid: str = ""
    state: str = "disconnected"       # "connected", "disconnected"
    ssid: str = ""
    bssid: str = ""
    radio_type: str = ""
    authentication: str = ""
    cipher: str = ""
    connection_mode: str = ""
    channel: int = 0
    receive_rate_mbps: Optional[float] = None
    transmit_rate_mbps: Optional[float] = None
    signal_percent: Optional[int] = None
    frequency_band: str = "Unknown"
    ipv4_address: str = "Unavailable"
    gateway: str = "Unavailable"
    dns_servers: List[str] = field(default_factory=list)

    @property
    def signal_category(self) -> str:
        return get_signal_category(self.signal_percent)


@dataclass
class SpeedTestResult:
    """Represents a finished, failed, or cancelled speed test measurement."""
    download_mbps: Optional[float] = None
    upload_mbps: Optional[float] = None
    ping_ms: Optional[float] = None
    jitter_ms: Optional[float] = None
    duration_sec: float = 0.0
    server_name: str = "Cloudflare Global Edge"
    network_ssid: str = ""
    location_label: str = "Default"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "completed"          # "completed", "cancelled", "failed"
    error_message: str = ""
    id: Optional[int] = None


@dataclass
class LatencyTestResult:
    """Represents a ping/latency test result."""
    target_host: str
    ping_count: int
    min_rtt_ms: Optional[float] = None
    max_rtt_ms: Optional[float] = None
    avg_rtt_ms: Optional[float] = None
    jitter_ms: Optional[float] = None
    packet_loss_percent: float = 0.0
    method: str = "ICMP"               # "ICMP" or "TCP_CONNECT"
    status: str = "completed"          # "completed", "cancelled", "failed"
    network_ssid: str = ""
    location_label: str = "Default"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    id: Optional[int] = None


@dataclass
class SignalLogEntry:
    """Represents a recorded signal sample over time."""
    network_ssid: str
    bssid: str
    signal_percent: int
    channel: int
    frequency_band: str
    location_label: str = "Default"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    id: Optional[int] = None


@dataclass
class ExperimentRun:
    """Represents one run in a multi-run repeated experiment."""
    experiment_id: str
    condition_label: str
    run_number: int
    network_ssid: str = ""
    location_label: str = ""
    signal_percent: Optional[int] = None
    ping_ms: Optional[float] = None
    jitter_ms: Optional[float] = None
    packet_loss_percent: Optional[float] = None
    download_mbps: Optional[float] = None
    upload_mbps: Optional[float] = None
    target_host: str = "8.8.8.8"
    status: str = "completed"          # "completed", "cancelled", "failed"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    id: Optional[int] = None
