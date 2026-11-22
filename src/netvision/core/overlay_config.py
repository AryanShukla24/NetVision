"""
NetVision - Statistics Overlay Configuration and Presets
Supports multi-window independent floating widgets, per-widget screen positioning,
transparency styling, and strict disabled-by-default initialization.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional
import json
import logging
from pathlib import Path
from netvision.config import CONFIG_DIR

logger = logging.getLogger(__name__)

OVERLAY_CONFIG_FILE = CONFIG_DIR / "overlay_config.json"


class DisplayMode:
    DONT_SHOW = "hidden"
    NUMBERS = "numbers"
    GRAPH = "graph"

    CHOICES = [DONT_SHOW, NUMBERS, GRAPH]
    LABELS = {
        DONT_SHOW: "Don't Show",
        NUMBERS: "Numbers",
        GRAPH: "Graph"
    }


@dataclass
class StatItemConfig:
    stat_id: str
    name: str
    category: str = "network"        # "network" or "system"
    mode: str = DisplayMode.NUMBERS   # "hidden", "numbers", "graph"
    unit: str = ""                   # e.g. "%", "ms", "Mbps", "FPS"
    
    # Independent Multi-Window Desktop Coordinates
    x: int = 100
    y: int = 100
    width: int = 180
    height: int = 65
    
    # Appearance & Styling
    opacity: float = 0.95            # Window opacity (0.2 to 1.0)
    bg_opacity: float = 0.0          # Background container opacity (0.0 = completely transparent!)
    show_subtle_bg: bool = False     # When False, background is genuinely transparent
    show_shadow: bool = True         # Subtle text shadow for high contrast & legibility
    border_radius: int = 6
    text_color: str = "#D5DEE8"
    color: str = "#22B8CF"           # Accent / Graph color
    
    # Numerical style controls
    font_size: int = 13
    padding: int = 6
    
    # Graph style controls
    graph_width: int = 240
    graph_height: int = 110
    graph_scale_mode: str = "auto"   # "auto" or "fixed"
    graph_min: float = 0.0
    graph_max: float = 100.0
    history_len: int = 60            # 20 to 120 samples
    
    # Window behavior
    is_locked: bool = False          # When locked, ignores mouse drags to prevent misclicks in games
    enabled: bool = True             # Independent visibility toggle
    
    # Shortcuts: STRICT REQUIREMENT - All shortcuts unassigned by default!
    shortcut: str = ""               # Unassigned by default ("")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StatItemConfig":
        valid_keys = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


def get_default_stats_catalog() -> Dict[str, StatItemConfig]:
    """
    Returns the catalog of all 11 supported statistics configured with
    intelligent screen corner placement for multi-window floating mode.
    Fits seamlessly across 1366x768 laptop screens up to 4K displays.
    """
    return {
        # Top-Right System / Gaming Telemetry
        "fps": StatItemConfig(
            stat_id="fps",
            name="FPS (Frame Rate)",
            category="system",
            mode=DisplayMode.NUMBERS,
            unit="FPS",
            x=1160, y=20, width=180, height=65,
            graph_width=240, graph_height=110,
            color="#39D98A",
            shortcut=""
        ),
        "ping": StatItemConfig(
            stat_id="ping",
            name="Ping / Latency",
            category="network",
            mode=DisplayMode.NUMBERS,
            unit="ms",
            x=1160, y=95, width=180, height=65,
            graph_width=240, graph_height=110,
            color="#F5B942",
            shortcut=""
        ),
        "wifi_signal": StatItemConfig(
            stat_id="wifi_signal",
            name="Wi-Fi Signal",
            category="network",
            mode=DisplayMode.NUMBERS,
            unit="%",
            x=1160, y=170, width=180, height=65,
            graph_width=240, graph_height=110,
            color="#39D98A",
            shortcut=""
        ),

        # Top-Left Resource Telemetry
        "cpu": StatItemConfig(
            stat_id="cpu",
            name="CPU Usage",
            category="system",
            mode=DisplayMode.GRAPH,
            unit="%",
            x=20, y=20, width=180, height=65,
            graph_width=240, graph_height=110,
            graph_scale_mode="fixed", graph_min=0.0, graph_max=100.0,
            color="#22B8CF",
            shortcut=""
        ),
        "gpu": StatItemConfig(
            stat_id="gpu",
            name="GPU Usage",
            category="system",
            mode=DisplayMode.GRAPH,
            unit="%",
            x=20, y=140, width=180, height=65,
            graph_width=240, graph_height=110,
            graph_scale_mode="fixed", graph_min=0.0, graph_max=100.0,
            color="#B07CFA",
            shortcut=""
        ),
        "ram": StatItemConfig(
            stat_id="ram",
            name="RAM Usage",
            category="system",
            mode=DisplayMode.NUMBERS,
            unit="%",
            x=20, y=260, width=180, height=65,
            graph_width=240, graph_height=110,
            color="#F5B942",
            shortcut=""
        ),

        # Bottom-Right Network I/O
        "net_io": StatItemConfig(
            stat_id="net_io",
            name="Network I/O",
            category="network",
            mode=DisplayMode.NUMBERS,
            unit="KB/s",
            x=1160, y=680, width=180, height=65,
            graph_width=240, graph_height=110,
            color="#22B8CF",
            shortcut=""
        ),
        "download_speed": StatItemConfig(
            stat_id="download_speed",
            name="Download Speed",
            category="network",
            mode=DisplayMode.NUMBERS,
            unit="Mbps",
            x=1160, y=605, width=180, height=65,
            graph_width=240, graph_height=110,
            color="#22B8CF",
            shortcut=""
        ),
        "upload_speed": StatItemConfig(
            stat_id="upload_speed",
            name="Upload Speed",
            category="network",
            mode=DisplayMode.NUMBERS,
            unit="Mbps",
            x=1160, y=530, width=180, height=65,
            graph_width=240, graph_height=110,
            color="#7C8CF5",
            shortcut=""
        ),

        # Bottom-Left Stability Telemetry
        "jitter": StatItemConfig(
            stat_id="jitter",
            name="Network Jitter",
            category="network",
            mode=DisplayMode.NUMBERS,
            unit="ms",
            x=20, y=680, width=180, height=65,
            graph_width=240, graph_height=110,
            color="#F5B942",
            shortcut=""
        ),
        "packet_loss": StatItemConfig(
            stat_id="packet_loss",
            name="Packet Loss",
            category="network",
            mode=DisplayMode.NUMBERS,
            unit="%",
            x=20, y=605, width=180, height=65,
            graph_width=240, graph_height=110,
            color="#F06464",
            shortcut=""
        ),
    }


@dataclass
class OverlayConfig:
    # STRICT REQUIREMENT: Overlay is DISABLED by default and LOCKED during normal use!
    master_enabled: bool = False
    master_locked: bool = True
    master_shortcut: str = ""        # Global hotkey to toggle all widgets (unassigned by default)
    
    # Global Appearance Defaults
    transparent_bg: bool = True      # Default appearance is genuinely transparent
    global_opacity: float = 0.95
    subtle_bg_opacity: float = 0.25  # When subtle background is toggled
    active_preset: str = "Performance"
    refresh_rate_ms: int = 1000
    
    # Individual Statistics items
    stats: Dict[str, StatItemConfig] = field(default_factory=get_default_stats_catalog)
    
    # Saved custom presets
    custom_presets: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "master_enabled": self.master_enabled,
            "master_locked": self.master_locked,
            "master_shortcut": self.master_shortcut,
            "transparent_bg": self.transparent_bg,
            "global_opacity": self.global_opacity,
            "subtle_bg_opacity": self.subtle_bg_opacity,
            "active_preset": self.active_preset,
            "refresh_rate_ms": self.refresh_rate_ms,
            "stats": {k: v.to_dict() for k, v in self.stats.items()},
            "custom_presets": self.custom_presets
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OverlayConfig":
        cfg = cls()
        for k in (
            "master_enabled", "master_locked", "master_shortcut", "transparent_bg",
            "global_opacity", "subtle_bg_opacity", "active_preset", "refresh_rate_ms",
            "custom_presets"
        ):
            if k in data:
                setattr(cfg, k, data[k])

        catalog = get_default_stats_catalog()
        saved_stats = data.get("stats", {})
        for stat_id, default_item in catalog.items():
            if stat_id in saved_stats:
                item_data = saved_stats[stat_id]
                item_data["stat_id"] = stat_id
                catalog[stat_id] = StatItemConfig.from_dict(item_data)
        cfg.stats = catalog
        return cfg

    def save(self, filepath: Optional[Path] = None):
        """Persists config to JSON file."""
        path = filepath or OVERLAY_CONFIG_FILE
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, indent=2)
            logger.info(f"Saved overlay configuration to {path}")
        except Exception as e:
            logger.error(f"Failed to save overlay configuration to {path}: {e}")

    @classmethod
    def load(cls, filepath: Optional[Path] = None) -> "OverlayConfig":
        """Loads configuration from JSON file or initializes default (disabled)."""
        path = filepath or OVERLAY_CONFIG_FILE
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return cls.from_dict(data)
            except Exception as e:
                logger.warning(f"Could not parse {path}, using defaults: {e}")
        cfg = cls()
        cfg.apply_preset("Performance")
        cfg.master_enabled = False  # Ensure disabled on fresh initialization
        return cfg

    def apply_preset(self, preset_name: str):
        """Applies a named preset: 'Minimal', 'Performance', 'Detailed', or custom."""
        self.active_preset = preset_name

        if preset_name == "Minimal":
            # Only top-right essential widgets (FPS, Ping, Wi-Fi Signal)
            for s_id, item in self.stats.items():
                if s_id in ("fps", "ping", "wifi_signal"):
                    item.mode = DisplayMode.NUMBERS
                    item.enabled = True
                else:
                    item.mode = DisplayMode.DONT_SHOW
                    item.enabled = False

        elif preset_name == "Performance":
            # System focus: CPU & GPU graphs (top left), FPS & RAM (top right), Ping (top right)
            for s_id, item in self.stats.items():
                if s_id in ("cpu", "gpu"):
                    item.mode = DisplayMode.GRAPH
                    item.enabled = True
                elif s_id in ("fps", "ram", "ping"):
                    item.mode = DisplayMode.NUMBERS
                    item.enabled = True
                else:
                    item.mode = DisplayMode.DONT_SHOW
                    item.enabled = False

        elif preset_name == "Detailed":
            # All 11 metrics visible across corners
            for s_id, item in self.stats.items():
                if s_id in ("cpu", "gpu", "net_io"):
                    item.mode = DisplayMode.GRAPH
                    item.enabled = True
                else:
                    item.mode = DisplayMode.NUMBERS
                    item.enabled = True

        elif preset_name in self.custom_presets:
            saved_preset = self.custom_presets[preset_name]
            stats_data = saved_preset.get("stats", {})
            for s_id, it_data in stats_data.items():
                if s_id in self.stats:
                    self.stats[s_id] = StatItemConfig.from_dict(it_data)

    def save_custom_preset(self, name: str):
        self.custom_presets[name] = {
            "stats": {k: v.to_dict() for k, v in self.stats.items()}
        }
        self.active_preset = name
        self.save()

    def delete_custom_preset(self, name: str) -> bool:
        if name in self.custom_presets:
            del self.custom_presets[name]
            if self.active_preset == name:
                self.active_preset = "Performance"
            self.save()
            return True
        return False
