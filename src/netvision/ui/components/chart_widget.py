"""
NetVision - Dark-Themed Matplotlib Chart Canvas
Seamlessly embeds interactive plots inside PySide6 with custom dark styling.
"""

from typing import List, Optional, Any
from PySide6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib
matplotlib.use("QtAgg")

from netvision.config import COLORS


class ChartWidget(QWidget):
    """Reusable dark-mode matplotlib chart widget."""

    def __init__(self, title: str = "", xlabel: str = "", ylabel: str = "", parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(6, 3), dpi=100)
        self.figure.patch.set_facecolor(COLORS["bg_surface"])

        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet(f"background-color: {COLORS['bg_surface']}; border-radius: 8px;")

        self.ax = self.figure.add_subplot(111)
        self._apply_dark_styling(title, xlabel, ylabel)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

    def _apply_dark_styling(self, title: str = "", xlabel: str = "", ylabel: str = ""):
        """Applies consistent dark theme to axes, spines, and ticks."""
        self.ax.set_facecolor(COLORS["bg_surface"])
        self.ax.tick_params(colors=COLORS["text_secondary"], labelsize=9)
        self.ax.grid(True, color=COLORS["border"], linestyle="--", linewidth=0.6, alpha=0.7)

        for spine in self.ax.spines.values():
            spine.set_color(COLORS["border"])

        if title:
            self.ax.set_title(title, color=COLORS["text_primary"], fontsize=11, fontweight="bold", pad=8)
        if xlabel:
            self.ax.set_xlabel(xlabel, color=COLORS["text_secondary"], fontsize=9)
        if ylabel:
            self.ax.set_ylabel(ylabel, color=COLORS["text_secondary"], fontsize=9)

    def clear(self, title: str = "", xlabel: str = "", ylabel: str = ""):
        """Clears axes and reapplies dark styling."""
        self.ax.clear()
        self._apply_dark_styling(title, xlabel, ylabel)

    def plot_line(
        self,
        x_data: List[Any],
        y_data: List[float],
        label: str = "",
        color: str = COLORS["primary"],
        ylim: Optional[tuple] = None,
        marker: str = "o"
    ):
        """Plots a styled time-series or sequential line."""
        self.ax.plot(
            x_data, y_data,
            label=label,
            color=color,
            linewidth=2.0,
            marker=marker,
            markersize=4,
            markerfacecolor=color,
            markeredgewidth=0
        )
        if ylim:
            self.ax.set_ylim(ylim)
        if label:
            legend = self.ax.legend(facecolor=COLORS["bg_surface"], edgecolor=COLORS["border"], labelcolor=COLORS["text_primary"], fontsize=9)
            if legend:
                legend.get_frame().set_alpha(0.8)
        self.figure.tight_layout()
        self.canvas.draw()

    def plot_scatter(
        self,
        x_data: List[Any],
        y_data: List[float],
        label: str = "",
        color: str = COLORS["primary"],
        xlim: Optional[tuple] = None,
        ylim: Optional[tuple] = None
    ):
        """Plots a styled scatter plot (points without connecting lines)."""
        self.ax.scatter(
            x_data, y_data,
            label=label,
            color=color,
            s=40,
            alpha=0.8,
            edgecolors="none"
        )
        if xlim:
            self.ax.set_xlim(xlim)
        if ylim:
            self.ax.set_ylim(ylim)
        if label:
            legend = self.ax.legend(facecolor=COLORS["bg_surface"], edgecolor=COLORS["border"], labelcolor=COLORS["text_primary"], fontsize=9)
            if legend:
                legend.get_frame().set_alpha(0.8)
        self.figure.tight_layout()
        self.canvas.draw()

    def plot_bars(
        self,
        categories: List[str],
        values: List[float],
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
        colors: Optional[List[str]] = None
    ):
        """Plots a styled categorical bar chart."""
        self.clear(title=title, xlabel=xlabel, ylabel=ylabel)
        bar_colors = colors or [COLORS["primary"]] * len(categories)
        self.ax.bar(categories, values, color=bar_colors, width=0.55, edgecolor=COLORS["border"])
        self.figure.tight_layout()
        self.canvas.draw()
