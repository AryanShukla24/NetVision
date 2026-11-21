"""
NetVision - Technical Engineering Diagram Generator
Generates crisp 300-DPI vector-style diagrams for the Project Report and Presentation:
1. System Layered Architecture (system_architecture.png)
2. Data Flow & Asynchronous QThread Concurrency (data_flow_diagram.png)
3. Relational Database ER Diagram (er_diagram.png)
4. Application Workflow & Use Cases (application_workflow.png)
"""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "diagrams"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Restrained Professional Engineering Palette
NAVY = "#14243A"
SLATE = "#344B64"
TEAL = "#2A9D8F"
LIGHT_BG = "#F2F5F8"
WHITE = "#FFFFFF"
DARK_TEXT = "#253243"
MUTED_TEXT = "#5A6B7C"
BORDER = "#B8C4D0"
SOFT_TEAL_BG = "#E8F5F3"
SOFT_BLUE_BG = "#EBF0F5"


def draw_box(ax, x, y, w, h, title, subtitle="", fc=WHITE, ec=SLATE, title_color=NAVY, sub_color=DARK_TEXT, lw=1.4, title_fs=10, sub_fs=8):
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.012,rounding_size=0.015",
        facecolor=fc, edgecolor=ec, linewidth=lw, zorder=3
    )
    ax.add_patch(box)
    if subtitle:
        ax.text(x + w / 2, y + h * 0.66, title, ha="center", va="center",
                fontsize=title_fs, fontweight="bold", color=title_color, family="sans-serif", zorder=4)
        ax.text(x + w / 2, y + h * 0.28, subtitle, ha="center", va="center",
                fontsize=sub_fs, color=sub_color, family="sans-serif", zorder=4)
    else:
        ax.text(x + w / 2, y + h / 2, title, ha="center", va="center",
                fontsize=title_fs, fontweight="bold", color=title_color, family="sans-serif", zorder=4)


def draw_arrow(ax, x1, y1, x2, y2, label="", color=SLATE, lw=1.6, label_offset=(0.015, 0)):
    arrow = FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle="-|>,head_length=6,head_width=3.5",
        color=color, linewidth=lw, zorder=5
    )
    ax.add_patch(arrow)
    if label:
        mx, my = (x1 + x2) / 2 + label_offset[0], (y1 + y2) / 2 + label_offset[1]
        ax.text(mx, my, label, ha="left", va="center", fontsize=8,
                fontstyle="italic", color=SLATE, family="sans-serif", zorder=6)


def make_system_architecture():
    fig, ax = plt.subplots(figsize=(11, 6.8), dpi=300)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_facecolor(WHITE)

    ax.text(0.5, 0.96, "NetVision v2.0.0 — Layered System Architecture",
            ha="center", va="center", fontsize=14, fontweight="bold", color=NAVY)
    ax.text(0.5, 0.92, "Decoupled Presentation, Asynchronous Worker, Core Measurement, OS Interface, and Persistence Tiers",
            ha="center", va="center", fontsize=9, color=MUTED_TEXT)

    # Layer 1: Presentation Tier
    draw_box(ax, 0.05, 0.74, 0.90, 0.13,
             "Presentation Tier — PySide6 (Qt 6) Desktop User Interface",
             "MainWindow (QStackedWidget)  |  12 Functional Pages: Dashboard, Wi-Fi Scanner, Signal Analyzer, Speed Test,\n"
             "Latency Monitor, Channel Analyzer, History, Location Comparison, Academic Experiment, Reports, Settings, About  |  Matplotlib Charts",
             fc=NAVY, ec=NAVY, title_color=WHITE, sub_color="#D9E4EE", title_fs=10.5, sub_fs=7.8)

    draw_arrow(ax, 0.35, 0.74, 0.35, 0.67, "User Commands (Qt Signals)", color=TEAL)
    draw_arrow(ax, 0.65, 0.67, 0.65, 0.74, "Live Progress & DTOs (Qt Slots)", color=SLATE)

    # Layer 2: Worker Thread Tier
    draw_box(ax, 0.05, 0.54, 0.90, 0.12,
             "Asynchronous Concurrency Tier — QThread Background Workers (core/workers.py)",
             "WifiScanWorker   |   SpeedTestWorker   |   LatencyTestWorker   |   SignalMonitorWorker   |   ExperimentWorker\n"
             "Non-blocking UI execution with cooperative cancellation (abort flags) and graceful shutdown in closeEvent()",
             fc=SOFT_TEAL_BG, ec=TEAL, title_color=NAVY, sub_color=DARK_TEXT, title_fs=10, sub_fs=7.8)

    draw_arrow(ax, 0.50, 0.54, 0.50, 0.47, "Python Domain API Calls", color=SLATE)

    # Layer 3: Core Domain Tier
    core_bg = FancyBboxPatch((0.05, 0.25), 0.90, 0.21, boxstyle="round,pad=0.01,rounding_size=0.015",
                             facecolor=LIGHT_BG, edgecolor=BORDER, linewidth=1.2, zorder=1)
    ax.add_patch(core_bg)
    ax.text(0.50, 0.438, "Core Measurement, Analytics & Reporting Tier (src/netvision/core/)",
            ha="center", va="center", fontsize=10, fontweight="bold", color=NAVY)

    mods = [
        ("WifiScanner", "wlanapi.dll + netsh"),
        ("SignalMonitor", "Continuous polling"),
        ("SpeedTester", "Cloudflare HTTP stream"),
        ("LatencyMonitor", "ICMP / TCP isolated"),
        ("ChannelAnalyzer", "2.4G overlap / 5G"),
        ("ExperimentAnalytics", "Mean, SD, Pearson r"),
        ("RecommendationEngine", "Rule-based thresholds"),
        ("ReportGenerator", "ReportLab PDF & CSV"),
    ]
    for i, (m_title, m_sub) in enumerate(mods):
        col = i % 4
        row = 1 - (i // 4)
        bx = 0.07 + col * 0.22
        by = 0.268 + row * 0.075
        draw_box(ax, bx, by, 0.20, 0.062, m_title, m_sub, fc=WHITE, ec=SLATE, title_fs=8.5, sub_fs=7.2, lw=1.0)

    draw_arrow(ax, 0.28, 0.25, 0.28, 0.17, "OS & WAN Probes", color=SLATE)
    draw_arrow(ax, 0.72, 0.25, 0.72, 0.17, "SQL CRUD & Reports", color=TEAL)

    # Layer 4 Left: OS & Network Interfaces
    draw_box(ax, 0.05, 0.04, 0.43, 0.12,
             "Windows OS & Network Subsystem Tier",
             "Native WLAN API (wlanapi.dll via ctypes)  |  netsh wlan / ip\n"
             "Windows ping.exe (ICMP)  |  TCP Sockets  |  Cloudflare CDN HTTPS",
             fc=SOFT_BLUE_BG, ec=SLATE, title_color=NAVY, sub_color=DARK_TEXT, title_fs=9.5, sub_fs=7.6)

    # Layer 4 Right: Persistence & User Data Tier
    draw_box(ax, 0.52, 0.04, 0.43, 0.12,
             "Persistence & User-Data Tier (%LOCALAPPDATA%\\NetVision)",
             "SQLite 3 Database (WAL Mode, Schema v2, 9 Tables, 9 Indices)\n"
             "Isolated Folders: database/ | logs/ | reports/ | exports/ | config/",
             fc=SOFT_BLUE_BG, ec=TEAL, title_color=NAVY, sub_color=DARK_TEXT, title_fs=9.5, sub_fs=7.6)

    plt.tight_layout()
    fig.savefig(OUT_DIR / "system_architecture.png", dpi=300, bbox_inches="tight", facecolor=WHITE)
    plt.close(fig)


def make_data_flow_diagram():
    fig, ax = plt.subplots(figsize=(11, 5.4), dpi=300)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_facecolor(WHITE)

    ax.text(0.5, 0.94, "NetVision — End-to-End Measurement Data Flow & Thread Lifecycle",
            ha="center", va="center", fontsize=13.5, fontweight="bold", color=NAVY)
    ax.text(0.5, 0.89, "How user actions execute non-blocking probes, persist relational telemetry, and update live analytics",
            ha="center", va="center", fontsize=9, color=MUTED_TEXT)

    # Top horizontal pipeline
    steps = [
        (0.03, "1. User Action", "Clicks Scan / Speed /\nPing / Experiment\non PySide6 Page", NAVY, WHITE, "#D9E4EE"),
        (0.22, "2. Worker Dispatch", "MainWindow instantiates\nQThread Worker &\nwires Signals/Slots", SLATE, WHITE, "#D9E4EE"),
        (0.41, "3. Core Execution", "Runs wlanapi / netsh /\nping.exe / HTTP chunks\non background thread", SOFT_TEAL_BG, NAVY, DARK_TEXT),
        (0.60, "4. Validation & Calc", "Parses output, guards\nNULLs, calculates RTT,\njitter, overlap, stats", SOFT_BLUE_BG, NAVY, DARK_TEXT),
        (0.79, "5. SQLite Persist", "Saves typed DTO into\nnetvision.db (WAL)\nwith location tag", WHITE, NAVY, DARK_TEXT),
    ]
    for x, t, s, fc, tc, sc in steps:
        ec = TEAL if fc == SOFT_TEAL_BG else SLATE
        draw_box(ax, x, 0.52, 0.17, 0.25, t, s, fc=fc, ec=ec, title_color=tc, sub_color=sc, title_fs=9, sub_fs=7.5)

    for x_end in [0.20, 0.39, 0.58, 0.77]:
        draw_arrow(ax, x_end, 0.645, x_end + 0.02, 0.645, color=SLATE)

    # Bottom feedback / output row
    draw_box(ax, 0.08, 0.12, 0.25, 0.22,
             "Live UI Charts & Metric Cards",
             "Qt Signals deliver progress & final DTOs\nto Matplotlib canvas & tables\n(Zero main-thread freezing)",
             fc=WHITE, ec=TEAL, title_fs=9, sub_fs=7.5)

    draw_box(ax, 0.38, 0.12, 0.25, 0.22,
             "Analytics & Comparisons",
             "History trends, multi-location bar charts,\nAcademic Experiment mean/SD & Pearson r,\nRule-based diagnostic recommendations",
             fc=WHITE, ec=SLATE, title_fs=9, sub_fs=7.5)

    draw_box(ax, 0.68, 0.12, 0.25, 0.22,
             "PDF & CSV Audit Exports",
             "ReportLab PDF (XML-escaped) &\nUTF-8 BOM CSV (formula-sanitized)\nsaved to %LOCALAPPDATA%\\NetVision\\reports",
             fc=WHITE, ec=SLATE, title_fs=9, sub_fs=7.5)

    # Arrows connecting top to bottom
    draw_arrow(ax, 0.495, 0.52, 0.205, 0.34, "Progress Signals", color=TEAL, label_offset=(-0.09, 0.01))
    draw_arrow(ax, 0.875, 0.52, 0.805, 0.34, "Query Archive", color=SLATE, label_offset=(0.01, 0))
    draw_arrow(ax, 0.83, 0.52, 0.505, 0.34, "SQL Read", color=SLATE, label_offset=(-0.06, 0.01))

    plt.tight_layout()
    fig.savefig(OUT_DIR / "data_flow_diagram.png", dpi=300, bbox_inches="tight", facecolor=WHITE)
    plt.close(fig)


def make_er_diagram():
    fig, ax = plt.subplots(figsize=(11.5, 7.2), dpi=300)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_facecolor(WHITE)

    ax.text(0.5, 0.96, "NetVision — Relational SQLite Database Schema (Version 2, WAL Mode)",
            ha="center", va="center", fontsize=13.5, fontweight="bold", color=NAVY)
    ax.text(0.5, 0.925, "Verified from src/netvision/database/db_manager.py — Foreign Keys Enabled, 9 Tables, 9 Performance Indices",
            ha="center", va="center", fontsize=8.8, color=MUTED_TEXT)

    def draw_entity(x, y, w, h, name, fields, header_color=NAVY):
        # Outer box
        outer = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.005,rounding_size=0.01",
                               facecolor=WHITE, edgecolor=SLATE, linewidth=1.2, zorder=2)
        ax.add_patch(outer)
        hdr_h = 0.042
        hdr = FancyBboxPatch((x, y + h - hdr_h), w, hdr_h, boxstyle="round,pad=0.005,rounding_size=0.01",
                             facecolor=header_color, edgecolor=header_color, linewidth=1.0, zorder=3)
        ax.add_patch(hdr)
        ax.text(x + w / 2, y + h - hdr_h / 2, name, ha="center", va="center",
                fontsize=8.5, fontweight="bold", color=WHITE, zorder=4)
        body_text = "\n".join(fields)
        ax.text(x + 0.01, y + h - hdr_h - 0.012, body_text, ha="left", va="top",
                fontsize=6.9, color=DARK_TEXT, family="monospace", linespacing=1.32, zorder=4)

    # Row 1
    draw_entity(0.03, 0.62, 0.26, 0.25, "scan_sessions", [
        "PK id (INTEGER)",
        "   timestamp (TEXT)",
        "   total_networks (INT)",
        "   active_interface (TEXT)",
        "   location_label (TEXT)"
    ], NAVY)

    draw_entity(0.36, 0.56, 0.28, 0.31, "wifi_networks", [
        "PK id (INTEGER)",
        "FK session_id -> scan_sessions",
        "   ssid (TEXT NOT NULL)",
        "   bssid (TEXT)",
        "   signal_percent (INT)",
        "   channel (INT)",
        "   frequency_band (TEXT)",
        "   security_type (TEXT)",
        "   is_connected (INT)",
        "   radio_type / observed_at"
    ], TEAL)

    draw_entity(0.71, 0.62, 0.26, 0.25, "locations", [
        "PK id (INTEGER)",
        "UK name (TEXT UNIQUE)",
        "   created_at (TEXT)",
        "   description (TEXT)",
        "-- Default: Home, Library,",
        "   Classroom, Cafe, Office"
    ], NAVY)

    # Row 2
    draw_entity(0.03, 0.24, 0.28, 0.30, "speed_tests", [
        "PK id (INTEGER)",
        "   timestamp (TEXT)",
        "   download_mbps (REAL NULL)",
        "   upload_mbps (REAL NULL)",
        "   ping_ms / jitter_ms (NULL)",
        "   duration_sec (REAL)",
        "   server_name (TEXT)",
        "   network_ssid (TEXT)",
        "   location_label (TEXT)",
        "   status / error_message"
    ], SLATE)

    draw_entity(0.36, 0.20, 0.28, 0.32, "latency_tests", [
        "PK id (INTEGER)",
        "   timestamp (TEXT)",
        "   target_host (TEXT)",
        "   ping_count (INTEGER)",
        "   min/max/avg_rtt_ms (NULL)",
        "   jitter_ms (REAL NULL)",
        "   packet_loss_percent (REAL)",
        "   method (ICMP/TCP_CONNECT)",
        "   status (TEXT)",
        "   network_ssid / location"
    ], SLATE)

    draw_entity(0.69, 0.24, 0.28, 0.30, "experiment_runs", [
        "PK id (INTEGER)",
        "   experiment_id (TEXT)",
        "   condition_label (TEXT)",
        "   run_number (INTEGER)",
        "   timestamp / network_ssid",
        "   location_label (TEXT)",
        "   signal_percent (INT NULL)",
        "   ping/jitter/loss (NULL)",
        "   download/upload (NULL)",
        "   target_host / status"
    ], SLATE)

    # Row 3
    draw_entity(0.03, 0.03, 0.30, 0.17, "signal_logs", [
        "PK id | timestamp | network_ssid",
        "   bssid | signal_percent (INT)",
        "   channel | frequency_band",
        "   location_label (TEXT)"
    ], TEAL)

    draw_entity(0.38, 0.03, 0.26, 0.14, "app_settings", [
        "PK key (TEXT)",
        "   value (TEXT NOT NULL)",
        "   updated_at (TEXT)"
    ], NAVY)

    draw_entity(0.69, 0.03, 0.28, 0.14, "schema_version", [
        "PK version (INTEGER)",
        "   applied_at (TEXT)",
        "   description (TEXT)"
    ], NAVY)

    # FK arrow scan_sessions -> wifi_networks
    draw_arrow(ax, 0.295, 0.74, 0.355, 0.74, color=TEAL, lw=2.0)
    ax.text(0.325, 0.768, "1 : N", ha="center", va="bottom", fontsize=7.8, fontweight="bold", color=TEAL, zorder=6)
    ax.text(0.325, 0.718, "CASCADE", ha="center", va="top", fontsize=6.6, color=SLATE, zorder=6)
    # Logical location tag connectors (short clean dashed connectors)
    arr1 = FancyArrowPatch((0.84, 0.615), (0.84, 0.545), arrowstyle="-|>,head_length=5,head_width=3",
                           linestyle="--", color=MUTED_TEXT, linewidth=1.2, zorder=4)
    ax.add_patch(arr1)
    arr2 = FancyArrowPatch((0.705, 0.635), (0.645, 0.51), arrowstyle="-|>,head_length=5,head_width=3",
                           linestyle="--", color=MUTED_TEXT, linewidth=1.2, zorder=4)
    ax.add_patch(arr2)
    ax.text(0.85, 0.58, "location_label", ha="left", va="center", fontsize=6.8, fontstyle="italic", color=MUTED_TEXT)

    ax.text(0.5, 0.005, "Solid arrow: Enforced Foreign Key (ON DELETE CASCADE)  |  Dashed lines: Logical location_label tagging across measurement tables",
            ha="center", va="bottom", fontsize=7.5, fontstyle="italic", color=MUTED_TEXT)

    plt.tight_layout()
    fig.savefig(OUT_DIR / "er_diagram.png", dpi=300, bbox_inches="tight", facecolor=WHITE)
    plt.close(fig)


def make_application_workflow():
    fig, ax = plt.subplots(figsize=(11, 4.8), dpi=300)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_facecolor(WHITE)

    ax.text(0.5, 0.93, "NetVision — Application Startup & Diagnostic Workflow",
            ha="center", va="center", fontsize=13.5, fontweight="bold", color=NAVY)
    ax.text(0.5, 0.875, "End-to-end operational lifecycle from initialization to multi-location audit reporting",
            ha="center", va="center", fontsize=9, color=MUTED_TEXT)

    nodes = [
        (0.03, 0.48, 0.15, 0.25, "Launch & Init", "Create %LOCALAPPDATA%\nfolders, seed/migrate\nSQLite v2 WAL DB", NAVY, WHITE, "#D9E4EE"),
        (0.22, 0.48, 0.16, 0.25, "Live Telemetry", "Inspect Wi-Fi NIC,\nBSSID, signal %,\nIP, Gateway & DNS", SLATE, WHITE, "#D9E4EE"),
        (0.42, 0.48, 0.17, 0.25, "Active Diagnostics", "Run Wi-Fi Scan,\nICMP/TCP Latency,\nCloudflare Speed Test", SOFT_TEAL_BG, NAVY, DARK_TEXT),
        (0.63, 0.48, 0.16, 0.25, "Scientific Analysis", "Channel Overlap,\nLocation Comparison,\nMulti-Trial Experiment", SOFT_BLUE_BG, NAVY, DARK_TEXT),
        (0.83, 0.48, 0.14, 0.25, "Audit Output", "Rule-based advice,\nReportLab PDF &\nSanitized CSV", WHITE, NAVY, DARK_TEXT),
    ]
    for x, y, w, h, t, s, fc, tc, sc in nodes:
        draw_box(ax, x, y, w, h, t, s, fc=fc, ec=TEAL if fc == SOFT_TEAL_BG else SLATE,
                 title_color=tc, sub_color=sc, title_fs=9, sub_fs=7.4)

    draw_arrow(ax, 0.18, 0.605, 0.22, 0.605)
    draw_arrow(ax, 0.38, 0.605, 0.42, 0.605)
    draw_arrow(ax, 0.59, 0.605, 0.63, 0.605)
    draw_arrow(ax, 0.79, 0.605, 0.83, 0.605)

    # Bottom governance bar
    draw_box(ax, 0.08, 0.10, 0.84, 0.22,
             "Measurement Integrity & Safety Guardrails Applied Across Every Stage",
             "• Strict NULL representation for failed/timed-out probes (never falsified as 0 ms or 0 Mbps)     "
             "• ICMP packet loss never masked by TCP fallback\n"
             "• Target host regex validation against command injection     "
             "• Graceful worker thread shutdown on window close     "
             "• Safe user-data preservation on uninstall",
             fc=LIGHT_BG, ec=BORDER, title_color=NAVY, sub_color=DARK_TEXT, title_fs=9.2, sub_fs=7.8)

    plt.tight_layout()
    fig.savefig(OUT_DIR / "application_workflow.png", dpi=300, bbox_inches="tight", facecolor=WHITE)
    plt.close(fig)


if __name__ == "__main__":
    make_system_architecture()
    make_data_flow_diagram()
    make_er_diagram()
    make_application_workflow()
    print("Generated all 4 engineering diagrams in:", OUT_DIR)
