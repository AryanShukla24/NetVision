"""
NetVision - Professional Academic PowerPoint Presentation Builder
Creates NetVision_Project_Presentation.pptx (16:9 widescreen, 17 slides)
using genuine live screenshots, verified technical diagrams, restrained engineering
palette, editable PowerPoint tables/shapes, and presenter speaker notes.
"""

import json
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

ROOT_DIR = Path(__file__).resolve().parent.parent
SHOTS_DIR = ROOT_DIR / "docs" / "screenshots"
DIAGRAMS_DIR = ROOT_DIR / "docs" / "diagrams"
OUT_PPTX = ROOT_DIR / "NetVision_Project_Presentation.pptx"

# Restrained University Engineering Color Palette
C_NAVY = RGBColor(0x14, 0x24, 0x3A)       # #14243A
C_SLATE = RGBColor(0x34, 0x4B, 0x64)      # #344B64
C_WHITE = RGBColor(0xFF, 0xFF, 0xFF)      # #FFFFFF
C_LIGHT_GRAY = RGBColor(0xF2, 0xF5, 0xF8) # #F2F5F8
C_TEAL = RGBColor(0x2A, 0x9D, 0x8F)       # #2A9D8F
C_DARK_TEXT = RGBColor(0x25, 0x32, 0x43)  # #253243
C_MUTED = RGBColor(0x64, 0x74, 0x8B)      # #64748B
C_BORDER = RGBColor(0xD0, 0xD8, 0xE2)     # #D0D8E2
C_SOFT_TEAL = RGBColor(0xE8, 0xF5, 0xF3)

FONT_MAIN = "Calibri"
TOTAL_SLIDES = 17


def set_slide_bg(slide, color):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_header_and_footer(slide, section_tag: str, title_text: str, slide_num: int):
    """Consistent restrained header bar, section divider, and footer with slide number."""
    # Top thin navy accent bar
    top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.08))
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = C_NAVY
    top_bar.line.fill.background()

    # Section tag (muted teal uppercase)
    tb_tag = slide.shapes.add_textbox(Inches(0.6), Inches(0.22), Inches(8.0), Inches(0.28))
    tf_tag = tb_tag.text_frame
    tf_tag.word_wrap = True
    tf_tag.margin_left = tf_tag.margin_top = tf_tag.margin_right = tf_tag.margin_bottom = 0
    p_tag = tf_tag.paragraphs[0]
    p_tag.text = section_tag.upper()
    p_tag.font.name = FONT_MAIN
    p_tag.font.size = Pt(10)
    p_tag.font.bold = True
    p_tag.font.color.rgb = C_TEAL

    # Slide Title
    tb_title = slide.shapes.add_textbox(Inches(0.6), Inches(0.46), Inches(11.8), Inches(0.55))
    tf_t = tb_title.text_frame
    tf_t.word_wrap = True
    tf_t.margin_left = tf_t.margin_top = tf_t.margin_right = tf_t.margin_bottom = 0
    p_t = tf_t.paragraphs[0]
    p_t.text = title_text
    p_t.font.name = FONT_MAIN
    p_t.font.size = Pt(24)
    p_t.font.bold = True
    p_t.font.color.rgb = C_NAVY

    # Subtle horizontal divider line under header
    div = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(1.06), Inches(12.133), Inches(0.018))
    div.fill.solid()
    div.fill.fore_color.rgb = C_BORDER
    div.line.fill.background()

    # Footer separator line
    f_div = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(7.02), Inches(12.133), Inches(0.01))
    f_div.fill.solid()
    f_div.fill.fore_color.rgb = C_BORDER
    f_div.line.fill.background()

    # Footer Left
    tb_fl = slide.shapes.add_textbox(Inches(0.6), Inches(7.08), Inches(8.5), Inches(0.3))
    p_fl = tb_fl.text_frame.paragraphs[0]
    p_fl.text = "NetVision — Smart Network Quality & Wi-Fi Coverage Analyzer  |  v2.0.0"
    p_fl.font.name = FONT_MAIN
    p_fl.font.size = Pt(9.5)
    p_fl.font.color.rgb = C_MUTED

    # Footer Right (Slide Number)
    tb_fr = slide.shapes.add_textbox(Inches(11.4), Inches(7.08), Inches(1.333), Inches(0.3))
    p_fr = tb_fr.text_frame.paragraphs[0]
    p_fr.text = f"{slide_num} / {TOTAL_SLIDES}"
    p_fr.alignment = PP_ALIGN.RIGHT
    p_fr.font.name = FONT_MAIN
    p_fr.font.size = Pt(9.5)
    p_fr.font.bold = True
    p_fr.font.color.rgb = C_SLATE


def add_bullets(slide, left, top, width, height, items, font_size=14, space_after=10, text_color=C_DARK_TEXT):
    """Adds clean structured bullet points with bold lead-ins when ':' is present."""
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

    for idx, item in enumerate(items):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.space_after = Pt(space_after)
        p.line_spacing = 1.22

        # Teal square bullet prefix
        r_b = p.add_run()
        r_b.text = "▪  "
        r_b.font.name = FONT_MAIN
        r_b.font.size = Pt(font_size)
        r_b.font.bold = True
        r_b.font.color.rgb = C_TEAL

        if ":" in item:
            lead, rest = item.split(":", 1)
            r1 = p.add_run()
            r1.text = lead + ":"
            r1.font.name = FONT_MAIN
            r1.font.size = Pt(font_size)
            r1.font.bold = True
            r1.font.color.rgb = C_NAVY

            r2 = p.add_run()
            r2.text = rest
            r2.font.name = FONT_MAIN
            r2.font.size = Pt(font_size)
            r2.font.color.rgb = text_color
        else:
            r1 = p.add_run()
            r1.text = item
            r1.font.name = FONT_MAIN
            r1.font.size = Pt(font_size)
            r1.font.color.rgb = text_color


def add_framed_image(slide, img_path: Path, left, top, max_w, max_h, caption=""):
    """Adds a real screenshot or diagram with subtle border framing and aspect-ratio preservation."""
    from PIL import Image
    with Image.open(img_path) as im:
        iw, ih = im.size
    ratio = iw / ih
    w = max_w
    h = w / ratio
    if h > max_h:
        h = max_h
        w = h * ratio

    # Center within bounding box
    x = left + (max_w - w) / 2
    y = top + (max_h - h) / 2

    # Crisp thin border rectangle behind image
    border = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(x - 0.03), Inches(y - 0.03), Inches(w + 0.06), Inches(h + 0.06)
    )
    border.fill.solid()
    border.fill.fore_color.rgb = C_WHITE
    border.line.color.rgb = C_BORDER
    border.line.width = Pt(1.0)

    slide.shapes.add_picture(str(img_path), Inches(x), Inches(y), width=Inches(w), height=Inches(h))

    if caption:
        tb = slide.shapes.add_textbox(Inches(left), Inches(y + h + 0.06), Inches(max_w), Inches(0.32))
        p = tb.text_frame.paragraphs[0]
        p.text = caption
        p.alignment = PP_ALIGN.CENTER
        p.font.name = FONT_MAIN
        p.font.size = Pt(9.5)
        p.font.italic = True
        p.font.color.rgb = C_MUTED


def add_callout_box(slide, left, top, width, height, heading, body, bg_color=C_LIGHT_GRAY, accent_color=C_TEAL):
    """Restrained flat callout with a clean left accent stripe."""
    box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    box.fill.solid()
    box.fill.fore_color.rgb = bg_color
    box.line.color.rgb = C_BORDER
    box.line.width = Pt(0.75)

    stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left), Inches(top), Inches(0.07), Inches(height))
    stripe.fill.solid()
    stripe.fill.fore_color.rgb = accent_color
    stripe.line.fill.background()

    tb = slide.shapes.add_textbox(Inches(left + 0.18), Inches(top + 0.10), Inches(width - 0.28), Inches(height - 0.18))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

    p1 = tf.paragraphs[0]
    p1.text = heading
    p1.font.name = FONT_MAIN
    p1.font.size = Pt(11.5)
    p1.font.bold = True
    p1.font.color.rgb = C_NAVY
    p1.space_after = Pt(3)

    p2 = tf.add_paragraph()
    p2.text = body
    p2.font.name = FONT_MAIN
    p2.font.size = Pt(10.5)
    p2.font.color.rgb = C_DARK_TEXT
    p2.line_spacing = 1.15


def add_notes(slide, text: str):
    notes_slide = slide.notes_slide
    notes_slide.notes_text_frame.text = text


def add_feature_slide(prs, slide_num, section, title, img_name, caption, bullets, callout=None, notes=""):
    """Standard high-clarity layout: Large real screenshot on left (7.85 in), concise technical points on right (4.1 in)."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, C_WHITE)
    add_header_and_footer(slide, section, title, slide_num)

    add_framed_image(slide, SHOTS_DIR / img_name, left=0.55, top=1.28, max_w=7.95, max_h=5.20, caption=caption)

    # Right column
    bullet_h = 3.85 if callout else 5.4
    add_bullets(slide, left=8.75, top=1.32, width=4.05, height=bullet_h, items=bullets, font_size=13, space_after=9)

    if callout:
        add_callout_box(slide, left=8.75, top=5.32, width=4.05, height=1.32,
                        heading=callout[0], body=callout[1], bg_color=C_SOFT_TEAL, accent_color=C_TEAL)

    if notes:
        add_notes(slide, notes)
    return slide


def build_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    # =========================================================================
    # SLIDE 1 — COVER
    # =========================================================================
    s1 = prs.slides.add_slide(blank)
    set_slide_bg(s1, C_NAVY)

    # Subtle geometric network pattern on right side (clean thin lines + nodes)
    nodes = [
        (10.1, 1.3), (11.7, 1.0), (12.4, 2.4), (10.7, 2.8),
        (9.6, 4.1), (11.5, 4.4), (12.5, 5.7), (10.3, 6.0)
    ]
    edges = [(0, 1), (1, 2), (0, 3), (2, 3), (3, 4), (3, 5), (2, 5), (4, 5), (5, 6), (4, 7), (5, 7)]
    for i, j in edges:
        x1, y1 = nodes[i]
        x2, y2 = nodes[j]
        conn = s1.shapes.add_connector(1, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
        conn.line.color.rgb = RGBColor(0x28, 0x41, 0x5E)
        conn.line.width = Pt(1.0)
    for nx, ny in nodes:
        dot = s1.shapes.add_shape(MSO_SHAPE.OVAL, Inches(nx - 0.08), Inches(ny - 0.08), Inches(0.16), Inches(0.16))
        dot.fill.solid()
        dot.fill.fore_color.rgb = C_TEAL if nx > 11.0 else C_SLATE
        dot.line.fill.background()

    # Left vertical muted teal accent stripe
    bar = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.75), Inches(1.15), Inches(0.08), Inches(4.85))
    bar.fill.solid()
    bar.fill.fore_color.rgb = C_TEAL
    bar.line.fill.background()

    # Category label
    tb_cat = s1.shapes.add_textbox(Inches(1.05), Inches(1.15), Inches(8.0), Inches(0.35))
    p = tb_cat.text_frame.paragraphs[0]
    p.text = "BTECH COMPUTER SCIENCE & ENGINEERING  |  PROJECT PRESENTATION"
    p.font.name = FONT_MAIN
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = C_TEAL

    # Main Title
    tb_title = s1.shapes.add_textbox(Inches(1.05), Inches(1.62), Inches(8.4), Inches(1.65))
    tf = tb_title.text_frame
    tf.word_wrap = True
    p1 = tf.paragraphs[0]
    p1.text = "NetVision"
    p1.font.name = FONT_MAIN
    p1.font.size = Pt(46)
    p1.font.bold = True
    p1.font.color.rgb = C_WHITE

    p2 = tf.add_paragraph()
    p2.text = "Smart Network Quality & Wi-Fi Coverage Analyzer"
    p2.font.name = FONT_MAIN
    p2.font.size = Pt(22)
    p2.font.color.rgb = RGBColor(0xD3, 0xDF, 0xEC)
    p2.space_before = Pt(4)

    # Thin divider
    div1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.05), Inches(3.52), Inches(6.5), Inches(0.02))
    div1.fill.solid()
    div1.fill.fore_color.rgb = C_SLATE
    div1.line.fill.background()

    # Submitted By Block (EXACT names & roll numbers)
    tb_team = s1.shapes.add_textbox(Inches(1.05), Inches(3.82), Inches(7.5), Inches(2.2))
    tf_t = tb_team.text_frame
    tf_t.word_wrap = True

    ph = tf_t.paragraphs[0]
    ph.text = "Submitted by:"
    ph.font.name = FONT_MAIN
    ph.font.size = Pt(13)
    ph.font.bold = True
    ph.font.color.rgb = C_TEAL
    ph.space_after = Pt(8)

    for member in [
        "1.  Aryan Shukla — 09117702724",
        "2.  Aaditya Rawat — 07917702724",
        "3.  Kushal Shedha — 08817702724",
    ]:
        pm = tf_t.add_paragraph()
        pm.text = member
        pm.font.name = FONT_MAIN
        pm.font.size = Pt(16)
        pm.font.color.rgb = C_WHITE
        pm.space_after = Pt(6)

    # Bottom clean editable placeholder bar
    tb_meta = s1.shapes.add_textbox(Inches(1.05), Inches(6.65), Inches(11.0), Inches(0.4))
    pm_bot = tb_meta.text_frame.paragraphs[0]
    pm_bot.text = "Department of Computer Science & Engineering  |  [Institution Name]  |  [Academic Session]"
    pm_bot.font.name = FONT_MAIN
    pm_bot.font.size = Pt(10.5)
    pm_bot.font.color.rgb = RGBColor(0x94, 0xA8, 0xBE)

    add_notes(s1, "Welcome everyone. Today we are presenting NetVision: Smart Network Quality & Wi-Fi Coverage Analyzer, developed by Aryan Shukla, Aaditya Rawat, and Kushal Shedha. NetVision is a native Windows desktop application built to measure, log, compare, and report real Wi-Fi and internet quality metrics.")

    # =========================================================================
    # SLIDE 2 — PROBLEM STATEMENT
    # =========================================================================
    s2 = prs.slides.add_slide(blank)
    set_slide_bg(s2, C_WHITE)
    add_header_and_footer(s2, "Introduction", "Problem Statement", 2)

    add_bullets(s2, left=0.65, top=1.35, width=7.2, height=5.2, items=[
        "Limited Visibility into Wi-Fi Conditions: Standard Windows Wi-Fi bars hide channel congestion, BSSID identity, radio standard, and signal stability over time.",
        "Signal Strength Does Not Equal Internet Performance: A strong local Wi-Fi link (e.g., 83% signal) can still suffer from ISP throughput bottlenecks, high latency, or packet loss.",
        "Spatial Variation Across Locations: Network performance changes significantly across rooms, classrooms, hostels, or campus zones due to attenuation and interference.",
        "Fragmented Built-In Diagnostics: Combining netsh, ping, and browser speed tests manually is slow, error-prone, and lacks unified measurement integrity.",
        "Missing History and Structured Reporting: Basic utilities do not persist timestamped records, support multi-location comparison, or export audit-ready reports."
    ], font_size=14.5, space_after=14)

    # Right side: concise contrast panel
    add_callout_box(s2, left=8.25, top=1.38, width=4.45, height=2.35,
                    heading="Typical User Confusion",
                    body="Users frequently assume full Wi-Fi bars guarantee fast, stable connectivity—unable to isolate whether slowdowns originate from weak RF reception, 2.4 GHz channel crowding, or external WAN latency.",
                    bg_color=C_LIGHT_GRAY, accent_color=C_SLATE)

    add_callout_box(s2, left=8.25, top=4.05, width=4.45, height=2.35,
                    heading="Engineering Gap Addressed",
                    body="A unified desktop diagnostic suite is needed to correlate physical-layer Wi-Fi metrics with Layer 3/4 latency, CDN throughput, persistent SQLite history, and statistical experiment tracking.",
                    bg_color=C_SOFT_TEAL, accent_color=C_TEAL)

    add_notes(s2, "Explain why existing Windows tools are insufficient: users look at Wi-Fi bars and assume their connection is healthy, yet real-time applications fail due to jitter, packet loss, channel overlap, or ISP limits. NetVision consolidates these layers into one structured desktop tool.")

    # =========================================================================
    # SLIDE 3 — PROJECT OBJECTIVES
    # =========================================================================
    s3 = prs.slides.add_slide(blank)
    set_slide_bg(s3, C_WHITE)
    add_header_and_footer(s3, "Introduction", "Project Objectives", 3)

    left_objs = [
        "Inspect Physical Wi-Fi Conditions: Query active interface parameters (SSID, BSSID, band, channel, link rate, IP, gateway, DNS) and scan nearby 802.11 access points.",
        "Monitor Signal Stability: Continuously poll active signal percentage, compute statistical spread, and detect disconnections cleanly.",
        "Measure WAN Throughput: Stream chunked HTTP payloads against Cloudflare Global Edge with TCP slow-start warm-up exclusion.",
        "Evaluate Latency, Jitter & Loss: Execute isolated ICMP echo or TCP 3-way handshake probes without masking dropped packets."
    ]
    right_objs = [
        "Estimate Channel Congestion: Model 2.4 GHz spectral overlap (Channels 1, 6, 11) and 5 GHz occupancy to suggest less crowded channels.",
        "Compare Environments & Experiments: Tag measurements by location, run repeated multi-trial experiments, and compute mean, SD, and Pearson correlation.",
        "Persist & Export Audit Data: Store relational telemetry in SQLite 3 (WAL mode) under %LOCALAPPDATA%\\NetVision and export PDF/CSV reports.",
        "Deliver Native Windows Distribution: Package standalone executables and a per-user Windows installer requiring zero Python setup."
    ]

    add_bullets(s3, left=0.65, top=1.40, width=5.8, height=5.2, items=left_objs, font_size=13.5, space_after=15)
    add_bullets(s3, left=6.85, top=1.40, width=5.85, height=5.2, items=right_objs, font_size=13.5, space_after=15)

    # Vertical subtle divider between two columns
    vdiv = s3.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(6.62), Inches(1.42), Inches(0.015), Inches(5.1))
    vdiv.fill.solid()
    vdiv.fill.fore_color.rgb = C_BORDER
    vdiv.line.fill.background()

    add_notes(s3, "Every objective on this slide maps directly to implemented modules verified in the NetVision v2.0.0 codebase—spanning radio inspection, honest latency/throughput telemetry, SQLite persistence, and standalone Windows packaging.")

    # =========================================================================
    # SLIDE 4 — SYSTEM OVERVIEW / ARCHITECTURE
    # =========================================================================
    s4 = prs.slides.add_slide(blank)
    set_slide_bg(s4, C_WHITE)
    add_header_and_footer(s4, "System Design", "System Overview & Layered Architecture", 4)

    add_framed_image(s4, DIAGRAMS_DIR / "system_architecture.png",
                     left=0.55, top=1.25, max_w=8.55, max_h=5.45,
                     caption="Figure 1: Four-tier architecture separating PySide6 UI, QThread workers, core networking modules, and SQLite WAL storage.")

    add_bullets(s4, left=9.30, top=1.35, width=3.45, height=3.8, items=[
        "Layered MVC Design: Clean separation across ui/, core/, and database/ packages inside src/netvision/.",
        "Non-Blocking Concurrency: 5 dedicated QThread workers prevent UI freezes during scans, pings, and downloads.",
        "Safe Shutdown: MainWindow.closeEvent() aborts active threads cleanly before exit.",
        "Data Isolation: User DB, logs, and reports live in %LOCALAPPDATA%\\NetVision."
    ], font_size=12.5, space_after=11)

    add_callout_box(s4, left=9.30, top=5.32, width=3.45, height=1.28,
                    heading="Measurement Integrity Rule",
                    body="Missing or failed measurements are stored as SQL NULL and displayed as '—' or 'No data', never falsified as zero.",
                    bg_color=C_SOFT_TEAL, accent_color=C_TEAL)

    add_notes(s4, "Walk through the four architectural tiers from top to bottom. Emphasize that all slow OS commands and network sockets run on QThread workers and report back via Qt Signals and Slots, keeping the GUI responsive at all times.")

    # =========================================================================
    # SLIDE 5 — TECHNOLOGY STACK
    # =========================================================================
    s5 = prs.slides.add_slide(blank)
    set_slide_bg(s5, C_WHITE)
    add_header_and_footer(s5, "System Design", "Verified Technology Stack", 5)

    rows_data = [
        ("Layer / Component", "Technology Used", "Role in NetVision"),
        ("Core Language", "Python 3.12 (3.10–3.12)", "Application logic, data modeling (dataclasses), subprocess & socket control"),
        ("Desktop GUI", "PySide6 (Qt 6.8)", "Native Windows desktop UI, QStackedWidget navigation, dark slate styling"),
        ("Concurrency", "Qt QThread & Signals/Slots", "Asynchronous Wi-Fi scans, speed tests, ping probes, signal polling, experiments"),
        ("OS Networking", "wlanapi.dll (ctypes), netsh, ping.exe", "Active hardware Wi-Fi scans, BSSID/interface parsing, gateway/DNS, ICMP probes"),
        ("HTTP / WAN", "requests, urllib3, socket", "Chunked Cloudflare Edge downloads/uploads & isolated TCP handshake probes"),
        ("Visualization", "Matplotlib, NumPy, Pandas", "Embedded interactive time-series charts, bar comparisons, and scatter plots"),
        ("Persistence", "SQLite 3 (WAL Mode, Schema v2)", "9 normalized tables, foreign keys, indices, safe schema migrations"),
        ("Reporting", "ReportLab, csv (UTF-8 BOM)", "XML-escaped PDF audit reports and formula-sanitized CSV exports"),
        ("Testing & Packaging", "Pytest (46 tests), PyInstaller, Inno Setup", "Automated verification, standalone EXEs (onedir/onefile), Windows Setup Wizard"),
    ]

    tbl_shape = s5.shapes.add_table(len(rows_data), 3, Inches(0.6), Inches(1.28), Inches(12.133), Inches(5.45))
    tbl = tbl_shape.table
    tbl.columns[0].width = Inches(2.35)
    tbl.columns[1].width = Inches(3.55)
    tbl.columns[2].width = Inches(6.233)

    for r_idx, row in enumerate(rows_data):
        for c_idx, val in enumerate(row):
            cell = tbl.cell(r_idx, c_idx)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.margin_left = Inches(0.12)
            cell.margin_right = Inches(0.10)
            cell.margin_top = Inches(0.05)
            cell.margin_bottom = Inches(0.05)
            cell.fill.solid()
            if r_idx == 0:
                cell.fill.fore_color.rgb = C_NAVY
            elif r_idx % 2 == 1:
                cell.fill.fore_color.rgb = C_WHITE
            else:
                cell.fill.fore_color.rgb = C_LIGHT_GRAY

            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.name = FONT_MAIN
            if r_idx == 0:
                p.font.size = Pt(11.5)
                p.font.bold = True
                p.font.color.rgb = C_WHITE
            else:
                p.font.size = Pt(10.8)
                p.font.bold = (c_idx == 0)
                p.font.color.rgb = C_NAVY if c_idx == 0 else C_DARK_TEXT

    add_notes(s5, "Every technology in this table is verified directly from requirements.txt, pyproject.toml, and the source code. Note how we chose native Windows APIs (wlanapi.dll and netsh) rather than unreliable third-party Wi-Fi wrappers.")

    # =========================================================================
    # SLIDE 6 — DASHBOARD
    # =========================================================================
    add_feature_slide(
        prs, 6, "Core Modules", "Network Status & Health Dashboard",
        "01_dashboard.png",
        "Live capture: Active connection (Airtel_maha_9259, 83% signal, 47.4 Mbps down, 12.0 ms ICMP RTT, 0.0% loss).",
        bullets=[
            "Unified Connection Overview: Displays active SSID, interface name, frequency band (2.4 GHz), channel (11), and local IPv4.",
            "Six Primary Health Metrics: Wi-Fi Signal Quality (%), Download & Upload Speed (Mbps), Round-Trip Ping (ms), Jitter (ms), and Packet Loss (%).",
            "Radio & Gateway Details: Shows BSSID, 802.11n PHY standard, WPA2-Personal/CCMP security, 72.2 Mbps Rx/Tx link rate, Default Gateway, and DNS servers.",
            "Holistic Diagnosis: Correlates local RF conditions with end-to-end WAN performance on a single screen."
        ],
        callout=("Live Observation on Test Machine",
                 "83% Wi-Fi signal with 72.2 Mbps PHY link rate yielded 47.4 Mbps download, 33.3 Mbps upload, and 12.0 ms ping—illustrating normal Wi-Fi protocol overhead."),
        notes="Point out the six metric cards and the bottom radio/gateway panel. Emphasize why combining RF signal with WAN speed, latency, jitter, and packet loss gives a far better diagnosis than Windows Wi-Fi bars alone."
    )

    # =========================================================================
    # SLIDE 7 — WI-FI SCANNER
    # =========================================================================
    add_feature_slide(
        prs, 7, "Core Modules", "Nearby Wi-Fi Network Scanner",
        "02_wifi_scanner.png",
        "Live capture: 31 real wireless access points discovered on Windows using wlanapi.dll active scan + netsh mode=bssid.",
        bullets=[
            "Active Hardware Radio Scan: Invokes Windows Native WLAN API (WlanScan in wlanapi.dll via ctypes) before querying netsh to avoid stale cache results.",
            "Multi-BSSID Disambiguation: Parses individual BSSID entries per SSID and matches the exact connected access point MAC address.",
            "Comprehensive Metadata: Extracts Signal %, Quality Category, Channel, Band (2.4/5/6 GHz), Security (WPA2/WPA3/Open), and Radio Standard.",
            "Filtering & Persistence: Instant search by SSID/channel/band, signal sorting, and automatic session logging to SQLite."
        ],
        callout=("Windows & Hardware Limitation",
                 "The test laptop uses a single-band 2.4 GHz adapter (Realtek RTL8723DE 802.11b/g/n); OS scans can only detect bands supported by the installed NIC."),
        notes="Highlight that NetVision triggered an active hardware scan and discovered 31 real surrounding networks—including multiple BSSIDs and hidden SSIDs—while faithfully reporting hardware band capabilities."
    )

    # =========================================================================
    # SLIDE 8 — SIGNAL ANALYZER
    # =========================================================================
    add_feature_slide(
        prs, 8, "Core Modules", "Wi-Fi Signal & RF Stability Analyzer",
        "03_signal_analyzer.png",
        "Live capture: Continuous signal sampling of Airtel_maha_9259 (83% mean, 0.0 sigma, classified 'Very Stable').",
        bullets=[
            "Continuous Polling Worker: SignalMonitorWorker polls the active Wi-Fi interface at configurable intervals (default 2 seconds) without blocking the UI.",
            "Monotonic Sample Tracking: Uses a strictly monotonic sample index counter with a rolling 300-sample memory window.",
            "Statistical Stability Metrics: Computes session mean, standard deviation (sigma), minimum, maximum, and range to classify links as Very Stable (<=3), Moderate (<=7), or Highly Unstable (>7).",
            "Disconnect Detection: Immediately notifies the user if Wi-Fi drops instead of retaining stale percentages."
        ],
        callout=("Why Stability Matters",
                 "Two locations with identical 75% average signal behave differently if one stays flat (0.0 sigma) while the other fluctuates widely due to obstructions or interference."),
        notes="Explain how continuous signal logging tagged with location labels enables objective comparison between rooms, desks, or router placements."
    )

    # =========================================================================
    # SLIDE 9 — INTERNET SPEED TESTING
    # =========================================================================
    add_feature_slide(
        prs, 9, "Core Modules", "Internet Speed & Bandwidth Testing",
        "04_speed_test.png",
        "Live capture: Cloudflare Global Edge test completed in 3.9s (47.4 Mbps download, 33.3 Mbps upload, 28.4 ms TCP edge ping).",
        bullets=[
            "Cloudflare Global Edge CDN: Streams genuine binary payloads over HTTPS (/ __down and /__up) instead of mock estimates.",
            "TCP Slow-Start Warm-Up: Downloads an initial 1 MB warm-up tier excluded from timing, then measures a 10 MB steady-state download in 64 KB chunks.",
            "Cancellable Chunked Upload: Streams 5 MB via a 64 KB Python generator checking abort flags on every chunk.",
            "PHY Link Rate vs Internet Throughput: 72.2 Mbps 802.11n PHY link rate measures raw wireless signaling, whereas 47.4 Mbps reflects real TCP/IP WAN throughput."
        ],
        callout=("Test Scope & Limitations",
                 "Results reflect path capacity to the nearest Cloudflare Anycast node and vary with ISP load, local Wi-Fi contention, and single-stream TCP window dynamics."),
        notes="Be sure to emphasize the Computer Networks concept here: Wi-Fi link rate (72.2 Mbps on 802.11n) is the Layer 1/2 maximum physical rate including framing overhead, while measured download (47.4 Mbps) is actual Layer 7 end-to-end WAN throughput."
    )

    # =========================================================================
    # SLIDE 10 — LATENCY AND PACKET LOSS
    # =========================================================================
    add_feature_slide(
        prs, 10, "Core Modules", "Latency, Jitter & Packet Loss Monitor",
        "05_latency_monitor.png",
        "Live capture: 6 ICMP probes to 8.8.8.8 (Min 7 ms, Avg 12.0 ms, Max 32 ms, Jitter 5.8 ms, Packet Loss 0.0%).",
        bullets=[
            "Strict Method Isolation: Supports ICMP Echo (ping -n 1) and TCP 3-Way Handshake (ports 53/443/80) as separate selectable methods—never masking lost ICMP packets with TCP fallback.",
            "Host Input Validation: Regex & ipaddress validation prevents shell injection or command-line option abuse.",
            "Genuine Jitter Formulas: Computes mean consecutive RTT difference (|RTT_i - RTT_{i-1}|) by default, with RFC 3550 smoothed interarrival jitter also implemented; returns NULL if < 2 replies.",
            "Real-Time Relevance: Low RTT, low jitter, and 0% packet loss are essential for VoIP, video conferencing, and online gaming."
        ],
        callout=("Honest Failure Handling",
                 "Sub-millisecond replies ('time<1ms') record as 0.5 ms; 100% packet loss stores NULL for min/max/avg/jitter rather than misleading 0.0 ms."),
        notes="Emphasize measurement integrity: many student projects silently catch a failed ping and substitute TCP or zero. NetVision strictly isolates ICMP from TCP_CONNECT and records lost probes honestly."
    )

    # =========================================================================
    # SLIDE 11 — CHANNEL ANALYSIS
    # =========================================================================
    add_feature_slide(
        prs, 11, "Core Modules", "Wi-Fi Spectrum & Channel Congestion Analyzer",
        "06_channel_analyzer.png",
        "Live capture: 31 APs across 2.4 GHz; Channel 11 (11 APs) & Channel 6 (9 APs) heavily congested -> recommends Channel 1 (score 7.4).",
        bullets=[
            "2.4 GHz Spectral Overlap Model: Applies 20 MHz IEEE 802.11 channel-spacing weights (Delta 0 = 1.0, Delta 1 = 0.75, Delta 2 = 0.50, Delta 3 = 0.25, Delta >= 4 = 0.0).",
            "Signal-Weighted Scoring: Weights each competing AP by w * (1 + signal%/100) across standard non-overlapping channels 1, 6, and 11.",
            "Band Separation: Separates 2.4 GHz and 5 GHz spectrum tabs cleanly without mixing incompatible channel numbering.",
            "Transparent Hardware Scope: Explicitly discloses that scores are estimated from 802.11 beacon frames—not direct non-Wi-Fi RF spectrum measurement."
        ],
        callout=("Actionable Finding on Test Host",
                 "Connected router is on Channel 11 (11 competing APs, score 13.19). Switching to Channel 1 reduces direct AP contention to 4 APs (overlap score 7.39)."),
        notes="Point out the bar chart from the real scan: Channel 11 has 11 APs and Channel 6 has 9 APs. Crucially, tell the examiner that NetVision honestly distinguishes AP-based overlap estimation from dedicated RF spectrum analyzer hardware."
    )

    # =========================================================================
    # SLIDE 12 — HISTORY AND LOCATION COMPARISON
    # =========================================================================
    s12 = prs.slides.add_slide(blank)
    set_slide_bg(s12, C_WHITE)
    add_header_and_footer(s12, "Analytics", "Historical Archive & Cross-Location Comparison", 12)

    add_framed_image(s12, SHOTS_DIR / "07_history_analytics.png",
                     left=0.55, top=1.22, max_w=6.00, max_h=3.65,
                     caption="History & Analytics: Filterable SQLite tables & trend plots.")
    add_framed_image(s12, SHOTS_DIR / "08_location_comparison.png",
                     left=6.78, top=1.22, max_w=6.00, max_h=3.65,
                     caption="Location Comparison: Side-by-side signal, speed & latency bars.")

    add_bullets(s12, left=0.60, top=5.28, width=5.95, height=1.65, items=[
        "Persistent Telemetry Archive: Stores timestamped speed tests, latency runs, and signal logs in SQLite with search, location filter, date range filter, and safe record deletion.",
        "Trend Visualization: Plots historical download throughput and latency trends over sequential test runs."
    ], font_size=12, space_after=6)

    add_bullets(s12, left=6.82, top=5.28, width=5.95, height=1.65, items=[
        "Multi-Location Selection: Checkable list compares arbitrary user-defined environments (Home, Cafe, Library, Classroom, Office, or custom tags).",
        "Statistical Fairness: Excludes failed runs, weights latency averages by probe count, and never plots missing metrics as zero."
    ], font_size=12, space_after=6)

    add_notes(s12, "Show how measurements collected across sessions are persisted in SQLite and compared across locations. Highlight that unequal sample counts and missing metrics are handled cleanly without distorting averages.")

    # =========================================================================
    # SLIDE 13 — ACADEMIC EXPERIMENT / TESTING
    # =========================================================================
    add_feature_slide(
        prs, 13, "Empirical Evaluation", "Academic Multi-Trial Experiment Module",
        "09_academic_experiment.png",
        "Live capture: 5 genuine trials under Condition A (Mean Signal 88.0% +-0.0%, Download 43.8 +-2.3 Mbps, Latency 12.1 +-2.5 ms).",
        bullets=[
            "Controlled Repeated Trials: Automates 3 to 10 sequential trials under a labeled physical condition (e.g., Near Router, Wall Barrier, Far Distance).",
            "Per-Trial Telemetry: Captures Wi-Fi signal %, Cloudflare download/upload throughput, ICMP ping, jitter, and packet loss per run.",
            "Statistical Rigor: Computes sample mean and sample standard deviation (sigma) across valid trials via experiment_analytics.py.",
            "Honest Pearson Correlation (r): Computes signal-vs-throughput correlation only when N >= 3 and both series exhibit variance; otherwise displays 'N/A (insufficient variance)'."
        ],
        callout=("Authentic Result Shown",
                 "In the 5 stationary trials shown, signal remained constant at 88% (0.0% variance), so NetVision honestly reported Correlation: N/A rather than fabricating an r value."),
        notes="This slide is a favorite for viva examiners! Point out the right chart: because all 5 stationary runs stayed at 88% signal (zero variance in X), Pearson correlation is mathematically undefined—and NetVision explicitly reports N/A instead of crashing or inventing a number."
    )

    # =========================================================================
    # SLIDE 14 — REPORTS AND DATA MANAGEMENT
    # =========================================================================
    add_feature_slide(
        prs, 14, "Reporting & Storage", "Audit Reports, Recommendations & SQLite Storage",
        "10_audit_reports.png",
        "Live capture: Rule-based diagnostic findings paired with one-click PDF and Excel-safe CSV export.",
        bullets=[
            "Evidence-Backed Recommendations: RecommendationEngine evaluates live telemetry against configurable thresholds (identifying strong signal, 2.4 GHz band use, low latency, and suboptimal Channel 11).",
            "ReportLab PDF Audit Reports: Multi-section PDFs with active link metadata, speed/latency tables, and XML entity escaping (safe for '<Hidden SSID>').",
            "Formula-Sanitized CSV Export: UTF-8 BOM encoding for Excel compatibility with DDE formula injection protection (=, +, -, @ prefix escaping).",
            "Isolated SQLite WAL Storage: 9 tables with Schema v1->v2 migration stored under %LOCALAPPDATA%\\NetVision\\database\\netvision.db."
        ],
        callout=("Packaging & Deployment",
                 "Built into dist/NetVision_Portable.exe (87.4 MB) and installer/NetVision_Setup.exe (per-user install, Desktop/Start Menu shortcuts, data-preserving uninstaller)."),
        notes="Explain how NetVision converts raw measurements into actionable recommendations and shareable PDF/CSV audit documents, while keeping all user data cleanly separated in %LOCALAPPDATA%\\NetVision."
    )

    # =========================================================================
    # SLIDE 15 — TESTING, RESULTS AND LIMITATIONS
    # =========================================================================
    s15 = prs.slides.add_slide(blank)
    set_slide_bg(s15, C_WHITE)
    add_header_and_footer(s15, "Verification", "Testing Summary, Verified Results & Limitations", 15)

    # Left: Testing Table
    t_rows = [
        ("Verification Category", "Scope & Evidence", "Result"),
        ("Automated Unit & Integration", "46 pytest cases: jitter/ping parsing, channel overlap, SQLite CRUD/migrations, analytics, recommendations, PDF/CSV safety, config isolation, headless GUI", "46 / 46 Passed (6.99s)"),
        ("Live Windows Wi-Fi Hardware", "Realtek RTL8723DE NIC via wlanapi.dll + netsh; active BSSID match, gateway/DNS extraction", "Verified (31 APs found)"),
        ("Live Internet & ICMP Tests", "ICMP ping to 8.8.8.8 (6 probes: 12.0 ms avg, 0% loss); Cloudflare Edge (47.4 down / 33.3 up Mbps)", "Verified (Live WAN)"),
        ("Packaged Windows Binaries", "Executed NetVision.exe (onedir), NetVision_Portable.exe (onefile), and NetVision_Setup.exe", "Verified (Clean launch)"),
    ]
    t_shape = s15.shapes.add_table(len(t_rows), 3, Inches(0.6), Inches(1.28), Inches(7.75), Inches(5.35))
    tt = t_shape.table
    tt.columns[0].width = Inches(2.15)
    tt.columns[1].width = Inches(4.05)
    tt.columns[2].width = Inches(1.55)
    for r_idx, row in enumerate(t_rows):
        for c_idx, val in enumerate(row):
            cell = tt.cell(r_idx, c_idx)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.margin_left = Inches(0.10)
            cell.margin_right = Inches(0.08)
            cell.fill.solid()
            cell.fill.fore_color.rgb = C_NAVY if r_idx == 0 else (C_WHITE if r_idx % 2 == 1 else C_LIGHT_GRAY)
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.name = FONT_MAIN
            p.font.size = Pt(10.8 if r_idx == 0 else 10.2)
            p.font.bold = (r_idx == 0 or c_idx == 0 or c_idx == 2)
            p.font.color.rgb = C_WHITE if r_idx == 0 else (C_TEAL if c_idx == 2 else (C_NAVY if c_idx == 0 else C_DARK_TEXT))

    # Right: Honest Limitations
    tb_lim_hdr = s15.shapes.add_textbox(Inches(8.65), Inches(1.28), Inches(4.1), Inches(0.35))
    pl = tb_lim_hdr.text_frame.paragraphs[0]
    pl.text = "Honest System Limitations"
    pl.font.name = FONT_MAIN
    pl.font.size = Pt(14)
    pl.font.bold = True
    pl.font.color.rgb = C_NAVY

    add_bullets(s15, left=8.65, top=1.72, width=4.1, height=4.95, items=[
        "Windows-Only Wireless Stack: Wi-Fi scanning relies on Windows wlanapi.dll and netsh; Linux/macOS are not currently supported.",
        "No Physical RF Spectrum Analyzer: Channel congestion is estimated from 802.11 AP beacons; non-Wi-Fi RF interference (microwaves, Bluetooth) is invisible to standard NICs.",
        "Single-Band NIC Constraint: 5 GHz / 6 GHz detection depends on host hardware capability.",
        "Single-Stream WAN Benchmark: Speed tests target Cloudflare Global Edge over a single HTTPS stream and require active internet access.",
        "Unsigned Installer Binary: PyInstaller EXEs are not Authenticode code-signed, so Windows SmartScreen may prompt on first run."
    ], font_size=11.5, space_after=9)

    add_notes(s15, "Clearly distinguish automated pytest verification (46 passing tests) from live hardware and WAN validation on Windows. Being transparent about hardware and platform limitations shows strong engineering maturity.")

    # =========================================================================
    # SLIDE 16 — CONCLUSION AND FUTURE SCOPE
    # =========================================================================
    s16 = prs.slides.add_slide(blank)
    set_slide_bg(s16, C_WHITE)
    add_header_and_footer(s16, "Summary", "Conclusion & Future Scope", 16)

    # Left Column: Conclusion (Implemented Reality)
    tb_c = s16.shapes.add_textbox(Inches(0.65), Inches(1.32), Inches(5.7), Inches(0.38))
    pc = tb_c.text_frame.paragraphs[0]
    pc.text = "Conclusion (Implemented in v2.0.0)"
    pc.font.name = FONT_MAIN
    pc.font.size = Pt(15)
    pc.font.bold = True
    pc.font.color.rgb = C_NAVY

    add_bullets(s16, left=0.65, top=1.80, width=5.75, height=4.9, items=[
        "Unified Diagnostic Suite: Delivered a 12-module Windows desktop application combining Wi-Fi radio telemetry, throughput, ICMP/TCP latency, channel overlap analysis, and reporting.",
        "Measurement Integrity: Enforced strict ICMP/TCP separation, genuine jitter formulas, NULL handling for failed runs, and transparent hardware disclaimers.",
        "Reliable Architecture: Decoupled PySide6 UI from 5 QThread workers and SQLite 3 WAL storage isolated in %LOCALAPPDATA%\\NetVision.",
        "Verified & Distributable: Backed by 46 passing automated tests, live hardware verification, standalone executables, and a Windows setup wizard."
    ], font_size=13, space_after=12)

    # Center Divider
    vdiv2 = s16.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(6.62), Inches(1.38), Inches(0.015), Inches(5.2))
    vdiv2.fill.solid()
    vdiv2.fill.fore_color.rgb = C_BORDER
    vdiv2.line.fill.background()

    # Right Column: Future Scope (Clearly Labeled)
    tb_f = s16.shapes.add_textbox(Inches(6.90), Inches(1.32), Inches(5.7), Inches(0.38))
    pf = tb_f.text_frame.paragraphs[0]
    pf.text = "Future Scope (Planned Enhancements)"
    pf.font.name = FONT_MAIN
    pf.font.size = Pt(15)
    pf.font.bold = True
    pf.font.color.rgb = C_TEAL

    add_bullets(s16, left=6.90, top=1.80, width=5.75, height=4.9, items=[
        "Spatial Floor-Plan Heatmaps: Plot location-tagged RSSI measurements onto user-uploaded floor plans with spatial interpolation.",
        "Multi-Stream & Multi-Server Speed Testing: Add parallel TCP stream benchmarking and selectable regional test servers.",
        "Advanced Diagnostics: Integrate traceroute hop latency, DNS lookup timing, and automated bufferbloat testing under load.",
        "Cross-Platform & Signed Releases: Extend wireless scanning adapters to Linux/macOS and add code-signed MSI/Inno Setup releases.",
        "Richer Longitudinal Analytics: Add scheduled background monitoring and time-of-day anomaly detection."
    ], font_size=13, space_after=12)

    add_notes(s16, "Conclude by summarizing what is concretely built and tested today in v2.0.0, and clearly separating future enhancements like floor-plan heatmaps, traceroute, and multi-stream testing.")

    # =========================================================================
    # SLIDE 17 — THANK YOU
    # =========================================================================
    s17 = prs.slides.add_slide(blank)
    set_slide_bg(s17, C_NAVY)

    # Subtle accent bar
    cbar = s17.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(5.85), Inches(2.55), Inches(1.63), Inches(0.06))
    cbar.fill.solid()
    cbar.fill.fore_color.rgb = C_TEAL
    cbar.line.fill.background()

    tb_ty = s17.shapes.add_textbox(Inches(1.5), Inches(2.80), Inches(10.333), Inches(1.2))
    pty = tb_ty.text_frame.paragraphs[0]
    pty.text = "Thank You"
    pty.alignment = PP_ALIGN.CENTER
    pty.font.name = FONT_MAIN
    pty.font.size = Pt(46)
    pty.font.bold = True
    pty.font.color.rgb = C_WHITE

    tb_q = s17.shapes.add_textbox(Inches(1.5), Inches(4.05), Inches(10.333), Inches(0.8))
    pq = tb_q.text_frame.paragraphs[0]
    pq.text = "Questions?"
    pq.alignment = PP_ALIGN.CENTER
    pq.font.name = FONT_MAIN
    pq.font.size = Pt(22)
    pq.font.color.rgb = RGBColor(0xB8, 0xCA, 0xDC)

    tb_sub = s17.shapes.add_textbox(Inches(1.5), Inches(5.35), Inches(10.333), Inches(0.5))
    psub = tb_sub.text_frame.paragraphs[0]
    psub.text = "NetVision — Smart Network Quality & Wi-Fi Coverage Analyzer  |  Live Demonstration Ready"
    psub.alignment = PP_ALIGN.CENTER
    psub.font.name = FONT_MAIN
    psub.font.size = Pt(12)
    psub.font.color.rgb = C_TEAL

    add_notes(s17, "Thank the faculty and examiners, and invite questions or a live demonstration of NetVision.")

    prs.save(str(OUT_PPTX))
    print(f"Presentation saved successfully to: {OUT_PPTX} ({OUT_PPTX.stat().st_size / (1024*1024):.2f} MB)")


if __name__ == "__main__":
    build_presentation()
