"""
NetVision - Statistics Overlay Configuration and Presets
Defines data structures, serialization, display modes, and built-in presets
for the real-time statistics overlay system.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List
import json
import logging
from pathlib import Path
from netvision.config import CONFIG_DIR

logger = logging.getLogger(__name__)

# Default config file path in %LOCALAPPDATA%\NetVision\config\
OVERLAY_CONFIG_FILE = CONFIG_DIR / "overlay_config.json"
PRESETS_DIR = CONFIG_DIR / "overlay_presets"


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
    
    # 2D Canvas positioning & geometry
    x: int = 10
    y: int = 10
    width: int = 180
    height: int = 48
    
    # Numerical style controls
    font_size: int = 13
    padding: int = 8
    
    # Graph style controls
    graph_width: int = 200
    graph_height: int = 65
    graph_scale_mode: str = "auto"   # "auto" or "fixed"
    graph_min: float = 0.0
    graph_max: float = 100.0
    history_len: int = 60            # 20 to 120 samples
    
    # Aesthetic coloring & appearance
    color: str = "#38bdf8"           # Accent hex color
    
    # Shortcut System: STRICT REQUIREMENT - All shortcuts unassigned by default!
    shortcut: str = ""               # Unassigned by default ("")
    enabled: bool = True             # Runtime visibility toggle via shortcut

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StatItemConfig":
        valid_keys = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


def get_default_stats_catalog() -> Dict[str, StatItemConfig]:
    """Returns the full catalog of 11 supported statistics with default layout properties."""
    return {
        "fps": StatItemConfig(
            stat_id="fps",
            name="FPS (Frame Rate)",
            category="system",
            mode=DisplayMode.NUMBERS,
            unit="FPS",
            x=12, y=12, width=180, height=48,
            graph_width=220, graph_height=65,
            color="#34d399",
            shortcut=""
        ),
        "cpu": StatItemConfig(
            stat_id="cpu",
            name="CPU Usage",
            category="system",
            mode=DisplayMode.GRAPH,
            unit="%",
            x=12, y=66, width=180, height=48,
            graph_width=220, graph_height=65,
            graph_scale_mode="fixed", graph_min=0.0, graph_max=100.0,
            color="#38bdf8",
            shortcut=""
        ),
        "gpu": StatItemConfig(
            stat_id="gpu",
            name="GPU Usage",
            category="system",
            mode=DisplayMode.GRAPH,
            unit="%",
            x=12, y=137, width=180, height=48,
            graph_width=220, graph_height=65,
            graph_scale_mode="fixed", graph_min=0.0, graph_max=100.0,
            color="#a78bfa",
            shortcut=""
        ),
        "ram": StatItemConfig(
            stat_id="ram",
            name="RAM / Memory Usage",
            category="system",
            mode=DisplayMode.NUMBERS,
            unit="%",
            x=12, y=208, width=180, height=48,
            graph_width=220, graph_height=65,
            graph_scale_mode="fixed", graph_min=0.0, graph_max=100.0,
            color="#f472b6",
            shortcut=""
        ),
        "net_io": StatItemConfig(
            stat_id="net_io",
            name="Network I/O Throughput",
            category="network",
            mode=DisplayMode.NUMBERS,
            unit="KB/s",
            x=12, y=262, width=180, height=48,
            graph_width=220, graph_height=65,
            color="#38bdf8",
            shortcut=""
        ),
        "wifi_signal": StatItemConfig(
            stat_id="wifi_signal",
            name="Wi-Fi Signal Quality",
            category="network",
            mode=DisplayMode.NUMBERS,
            unit="%",
            x=200, y=12, width=180, height=48,
            graph_width=220, graph_height=65,
            graph_scale_mode="fixed", graph_min=0.0, graph_max=100.0,
            color="#34d399",
            shortcut=""
        ),
        "ping": StatItemConfig(
            stat_id="ping",
            name="Round-Trip Ping / Latency",
            category="network",
            mode=DisplayMode.NUMBERS,
            unit="ms",
            x=200, y=66, width=180, height=48,
            graph_width=220, graph_height=65,
            graph_scale_mode="auto", graph_min=0.0, graph_max=150.0,
            color="#fbbf24",
            shortcut=""
        ),
        "jitter": StatItemConfig(
            stat_id="jitter",
            name="Network Jitter",
            category="network",
            mode=DisplayMode.NUMBERS,
            unit="ms",
            x=200, y=120, width=180, height=48,
            graph_width=220, graph_height=65,
            color="#f97316",
            shortcut=""
        ),
        "packet_loss": StatItemConfig(
            stat_id="packet_loss",
            name="Packet Loss",
            category="network",
            mode=DisplayMode.NUMBERS,
            unit="%",
            x=200, y=174, width=180, height=48,
            graph_width=220, graph_height=65,
            graph_scale_mode="fixed", graph_min=0.0, graph_max=20.0,
            color="#f87171",
            shortcut=""
        ),
        "download_speed": StatItemConfig(
            stat_id="download_speed",
            name="Download Speed",
            category="network",
            mode=DisplayMode.NUMBERS,
            unit="Mbps",
            x=200, y=228, width=180, height=48,
            graph_width=220, graph_height=65,
            color="#60a5fa",
            shortcut=""
        ),
        "upload_speed": StatItemConfig(
            stat_id="upload_speed",
            name="Upload Speed",
            category="network",
            mode=DisplayMode.NUMBERS,
            unit="Mbps",
            x=200, y=282, width=180, height=48,
            graph_width=220, graph_height=65,
            color="#818cf8",
            shortcut=""
        ),
    }


@dataclass
class OverlayConfig:
    # Master controls
    master_enabled: bool = True
    active_preset: str = "Detailed"
    
    # Overlay Window Aesthetics & Position
    opacity: float = 0.90
    bg_color: str = "#0f172a"
    border_color: str = "#334155"
    text_color: str = "#f8fafc"
    locked: bool = False             # When locked, window ignores drag/repositioning
    always_on_top: bool = True
    
    # Window placement
    window_x: int = 50
    window_y: int = 50
    window_width: int = 420
    window_height: int = 380
    
    # Editor & Grid Snapping
    snap_to_grid: bool = True
    grid_size: int = 8
    show_alignment_guides: bool = True
    
    # Refresh rate
    refresh_rate_ms: int = 1000      # 500ms to 5000ms
    
    # Individual Statistics items
    stats: Dict[str, StatItemConfig] = field(default_factory=get_default_stats_catalog)
    
    # Saved custom presets: name -> dict of stat settings
    custom_presets: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "master_enabled": self.master_enabled,
            "active_preset": self.active_preset,
            "opacity": self.opacity,
            "bg_color": self.bg_color,
            "border_color": self.border_color,
            "text_color": self.text_color,
            "locked": self.locked,
            "always_on_top": self.always_on_top,
            "window_x": self.window_x,
            "window_y": self.window_y,
            "window_width": self.window_width,
            "window_height": self.window_height,
            "snap_to_grid": self.snap_to_grid,
            "grid_size": self.grid_size,
            "show_alignment_guides": self.show_alignment_guides,
            "refresh_rate_ms": self.refresh_rate_ms,
            "stats": {k: v.to_dict() for k, v in self.stats.items()},
            "custom_presets": self.custom_presets
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OverlayConfig":
        cfg = cls()
        for k in (
            "master_enabled", "active_preset", "opacity", "bg_color",
            "border_color", "text_color", "locked", "always_on_top",
            "window_x", "window_y", "window_width", "window_height",
            "snap_to_grid", "grid_size", "show_alignment_guides",
            "refresh_rate_ms", "custom_presets"
        ):
            if k in data:
                setattr(cfg, k, data[k])

        catalog = get_default_stats_catalog()
        saved_stats = data.get("stats", {})
        for stat_id, default_item in catalog.items():
            if stat_id in saved_stats:
                item_data = saved_stats[stat_id]
                # Keep fixed properties like stat_id and category
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
        """Loads configuration from JSON file or initializes default."""
        path = filepath or OVERLAY_CONFIG_FILE
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                logger.info(f"Loaded overlay configuration from {path}")
                return cls.from_dict(data)
            except Exception as e:
                logger.warning(f"Could not parse {path}, using defaults: {e}")
        cfg = cls()
        cfg.apply_preset("Detailed")
        return cfg

    # --- Built-in Presets Engine ---

    def apply_preset(self, preset_name: str):
        """
        Applies a named preset: 'Minimal', 'Performance', 'Detailed',
        or a user custom preset name.
        """
        self.active_preset = preset_name
        
        if preset_name == "Minimal":
            # Essential lightweight stats in single-column numbers mode
            self.window_width = 240
            self.window_height = 190
            
            y_offset = 12
            for stat_id, item in self.stats.items():
                if stat_id in ("ping", "wifi_signal", "fps"):
                    item.mode = DisplayMode.NUMBERS
                    item.enabled = True
                    item.x = 12
                    item.y = y_offset
                    item.width = 216
                    item.height = 46
                    y_offset += 54
                else:
                    item.mode = DisplayMode.DONT_SHOW

        elif preset_name == "Performance":
            # Gaming and system resource focus
            self.window_width = 460
            self.window_height = 280
            
            # Left column: FPS, RAM, Ping, Net I/O
            y_left = 12
            for s in ("fps", "ram", "ping", "net_io"):
                if s in self.stats:
                    self.stats[s].mode = DisplayMode.NUMBERS
                    self.stats[s].enabled = True
                    self.stats[s].x = 12
                    self.stats[s].y = y_left
                    self.stats[s].width = 190
                    self.stats[s].height = 48
                    y_left += 54
            
            # Right column: CPU Graph, GPU Graph
            y_right = 12
            for s in ("cpu", "gpu"):
                if s in self.stats:
                    self.stats[s].mode = DisplayMode.GRAPH
                    self.stats[s].enabled = True
                    self.stats[s].x = 214
                    self.stats[s].y = y_right
                    self.stats[s].width = 230
                    self.stats[s].height = 100
                    self.stats[s].graph_width = 230
                    self.stats[s].graph_height = 100
                    y_right += 108
            
            for s in ("wifi_signal", "jitter", "packet_loss", "download_speed", "upload_speed"):
                if s in self.stats:
                    self.stats[s].mode = DisplayMode.DONT_SHOW

        elif preset_name == "Detailed":
            # Complete system and network telemetry dashboard
            self.window_width = 490
            self.window_height = 490
            
            # Column 1 (x=12): System + Speeds
            col1 = [
                ("fps", DisplayMode.NUMBERS, 46),
                ("cpu", DisplayMode.GRAPH, 80),
                ("gpu", DisplayMode.GRAPH, 80),
                ("ram", DisplayMode.NUMBERS, 46),
                ("download_speed", DisplayMode.NUMBERS, 46),
                ("upload_speed", DisplayMode.NUMBERS, 46),
            ]
            y = 12
            for s_id, mode, h in col1:
                if s_id in self.stats:
                    it = self.stats[s_id]
                    it.mode = mode
                    it.enabled = True
                    it.x = 12
                    it.y = y
                    it.width = 225
                    it.height = h
                    it.graph_width = 225
                    it.graph_height = h
                    y += h + 8

            # Column 2 (x=248): Network & Wi-Fi
            col2 = [
                ("wifi_signal", DisplayMode.GRAPH, 80),
                ("ping", DisplayMode.GRAPH, 80),
                ("jitter", DisplayMode.NUMBERS, 46),
                ("packet_loss", DisplayMode.NUMBERS, 46),
                ("net_io", DisplayMode.GRAPH, 80),
            ]
            y = 12
            for s_id, mode, h in col2:
                if s_id in self.stats:
                    it = self.stats[s_id]
                    it.mode = mode
                    it.enabled = True
                    it.x = 248
                    it.y = y
                    it.width = 225
                    it.height = h
                    it.graph_width = 225
                    it.graph_height = h
                    y += h + 8

        elif preset_name in self.custom_presets:
            saved_preset = self.custom_presets[preset_name]
            stats_data = saved_preset.get("stats", {})
            for s_id, it_data in stats_data.items():
                if s_id in self.stats:
                    self.stats[s_id] = StatItemConfig.from_dict(it_data)
            if "window_width" in saved_preset:
                self.window_width = saved_preset["window_width"]
            if "window_height" in saved_preset:
                self.window_height = saved_preset["window_height"]

    def save_custom_preset(self, name: str):
        """Saves current statistics configuration as a custom preset."""
        preset_data = {
            "window_width": self.window_width,
            "window_height": self.window_height,
            "stats": {k: v.to_dict() for k, v in self.stats.items()}
        }
        self.custom_presets[name] = preset_data
        self.active_preset = name
        self.save()

    def delete_custom_preset(self, name: str) -> bool:
        if name in self.custom_presets:
            del self.custom_presets[name]
            if self.active_preset == name:
                self.active_preset = "Detailed"
            self.save()
            return True
        return False
