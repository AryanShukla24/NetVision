"""
NetVision - Statistics Overlay UI Package
Provides independent floating statistic windows, mini sparkline graphs,
and multi-window overlay management.
"""

from netvision.ui.overlay.mini_graph import MiniGraphWidget
from netvision.ui.overlay.floating_widget import FloatingStatWidget
from netvision.ui.overlay.overlay_manager import OverlayManager

__all__ = ["MiniGraphWidget", "FloatingStatWidget", "OverlayManager"]
