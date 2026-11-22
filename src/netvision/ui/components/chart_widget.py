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
        self.figure.patch.set_facecolor(COLORS["bg_dark"])

        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet(f"background-color: {COLORS['bg_dark']}; border: 1px solid {COLORS['border']}; border-radius: 4px;")

        self.ax = self.figure.add_subplot(111)
        self._apply_dark_styling(title, xlabel, ylabel)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

    def _apply_dark_styling(self, title: str = "", xlabel: str = "", ylabel: str = ""):
        """Applies consistent dark theme to axes, spines, and ticks."""
        self.ax.set_facecolor(COLORS["bg_dark"])
        self.ax.tick_params(colors=COLORS["text_secondary"], labelsize=8.5)
        self.ax.grid(True, color=COLORS["border"], linestyle="--", linewidth=0.5, alpha=0.6)

        for spine in self.ax.spines.values():
            spine.set_color(COLORS["border"])

        if title:
            self.ax.set_title(title, color=COLORS["text_bright"], fontsize=10.5, fontweight="bold", pad=8)
        if xlabel:
            self.ax.set_xlabel(xlabel, color=COLORS["text_secondary"], fontsize=8.5, labelpad=5)
        if ylabel:
            self.ax.set_ylabel(ylabel, color=COLORS["text_secondary"], fontsize=8.5, labelpad=5)

        try:
            self.figure.subplots_adjust(top=0.88, bottom=0.20, left=0.12, right=0.95)
        except Exception:
            pass

    def clear(self, title: str = "", xlabel: str = "", ylabel: str = ""):
        """Clears axes and reapplies dark styling."""
        self.ax.clear()
        self._apply_dark_styling(title, xlabel, ylabel)

    def show_empty_message(self, message: str = "No test data available yet", title: str = ""):
        """Renders a clean empty placeholder state."""
        self.ax.clear()
        self._apply_dark_styling(title=title)
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.text(
            0.5, 0.5, message,
            horizontalalignment="center",
            verticalalignment="center",
            transform=self.ax.transAxes,
            color=COLORS["text_muted"],
            fontsize=9.5,
            fontstyle="italic"
        )
        self.canvas.draw()

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
            linewidth=1.8,
            marker=marker,
            markersize=3.5,
            markerfacecolor=color,
            markeredgewidth=0
        )
        if ylim:
            self.ax.set_ylim(ylim)
        if label:
            legend = self.ax.legend(facecolor=COLORS["bg_elevated"], edgecolor=COLORS["border"], labelcolor=COLORS["text_primary"], fontsize=8.5)
            if legend:
                legend.get_frame().set_alpha(0.85)
        try:
            self.figure.tight_layout(pad=1.2)
        except Exception:
            self.figure.subplots_adjust(top=0.88, bottom=0.20, left=0.12, right=0.95)
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
            s=35,
            alpha=0.85,
            edgecolors="none"
        )
        if xlim:
            self.ax.set_xlim(xlim)
        if ylim:
            self.ax.set_ylim(ylim)
        if label:
            legend = self.ax.legend(facecolor=COLORS["bg_elevated"], edgecolor=COLORS["border"], labelcolor=COLORS["text_primary"], fontsize=8.5)
            if legend:
                legend.get_frame().set_alpha(0.85)
        try:
            self.figure.tight_layout(pad=1.2)
        except Exception:
            self.figure.subplots_adjust(top=0.88, bottom=0.20, left=0.12, right=0.95)
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
        self.ax.bar(categories, values, color=bar_colors, width=0.50, edgecolor=COLORS["border"])
        try:
            self.figure.tight_layout(pad=1.2)
        except Exception:
            self.figure.subplots_adjust(top=0.88, bottom=0.20, left=0.12, right=0.95)
        self.canvas.draw()
