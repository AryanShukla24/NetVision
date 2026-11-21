"""
NetVision - Report Generator (PDF and CSV)
Exports historical network audits, speed tests, and telemetry to CSV and styled PDF.
Designed for college project demonstrations and professional network documentation.
"""

import csv
import logging
import xml.sax.saxutils
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from netvision.config import REPORTS_DIR

logger = logging.getLogger(__name__)


def sanitize_csv_cell(val: Any) -> Any:
    """Guards against CSV formula injection (DDE attacks) while preserving numbers."""
    if val is None:
        return ""
    if isinstance(val, (int, float)):
        return val
    s = str(val).strip()
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        try:
            float(s)
            return s
        except ValueError:
            return "'" + s
    return s


def escape_report_text(val: Any) -> str:
    """Escapes HTML/XML entities so ReportLab Paragraphs never crash on characters like '<Hidden SSID>'."""
    if val is None:
        return "—"
    s = str(val)
    # ReportLab Paragraph treats & and < > as tags
    return xml.sax.saxutils.escape(s)


class ReportGenerator:
    """Handles CSV and PDF report generation for network measurements."""

    @classmethod
    def export_csv(
        cls,
        speed_tests: List[Dict[str, Any]],
        latency_tests: List[Dict[str, Any]],
        signal_logs: List[Dict[str, Any]],
        output_path: Optional[Path] = None
    ) -> Path:
        """Exports unified measurement records into a structured Excel-safe CSV file."""
        if not output_path:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = REPORTS_DIR / f"NetVision_Audit_{ts}.csv"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Record_Type", "Timestamp", "Network_SSID", "Location_Label",
                "Signal_Percent", "Download_Mbps", "Upload_Mbps", "Ping_ms",
                "Jitter_ms", "Packet_Loss_Percent", "Target_Host_or_Server", "Method", "Status"
            ])

            for s in speed_tests:
                d_val = f"{s['download_mbps']:.2f}" if s.get("download_mbps") is not None else ""
                u_val = f"{s['upload_mbps']:.2f}" if s.get("upload_mbps") is not None else ""
                p_val = f"{s['ping_ms']:.2f}" if s.get("ping_ms") is not None else ""
                j_val = f"{s['jitter_ms']:.2f}" if s.get("jitter_ms") is not None else ""

                writer.writerow([
                    "SpeedTest",
                    sanitize_csv_cell(s.get("timestamp", "")),
                    sanitize_csv_cell(s.get("network_ssid", "")),
                    sanitize_csv_cell(s.get("location_label", "")),
                    "",
                    d_val,
                    u_val,
                    p_val,
                    j_val,
                    "",
                    sanitize_csv_cell(s.get("server_name", "")),
                    "HTTP_CHUNKED",
                    sanitize_csv_cell(s.get("status", "completed"))
                ])

            for l in latency_tests:
                rtt_val = f"{l['avg_rtt_ms']:.2f}" if l.get("avg_rtt_ms") is not None else ""
                jit_val = f"{l['jitter_ms']:.2f}" if l.get("jitter_ms") is not None else ""
                loss_val = f"{l['packet_loss_percent']:.2f}" if l.get("packet_loss_percent") is not None else ""

                writer.writerow([
                    "LatencyTest",
                    sanitize_csv_cell(l.get("timestamp", "")),
                    sanitize_csv_cell(l.get("network_ssid", "")),
                    sanitize_csv_cell(l.get("location_label", "")),
                    "",
                    "",
                    "",
                    rtt_val,
                    jit_val,
                    loss_val,
                    sanitize_csv_cell(l.get("target_host", "")),
                    sanitize_csv_cell(l.get("method", "ICMP")),
                    sanitize_csv_cell(l.get("status", "completed"))
                ])

            for sig in signal_logs:
                sig_val = sig.get("signal_percent") if sig.get("signal_percent") is not None else ""
                writer.writerow([
                    "SignalLog",
                    sanitize_csv_cell(sig.get("timestamp", "")),
                    sanitize_csv_cell(sig.get("network_ssid", "")),
                    sanitize_csv_cell(sig.get("location_label", "")),
                    sig_val,
                    "",
                    "",
                    "",
                    "",
                    "",
                    sanitize_csv_cell(sig.get("bssid", "")),
                    "WLAN_QUERY",
                    "recorded"
                ])

        return output_path

    @classmethod
    def export_pdf(
        cls,
        summary_info: Dict[str, Any],
        speed_tests: List[Dict[str, Any]],
        latency_tests: List[Dict[str, Any]],
        recommendations: List[Dict[str, str]],
        output_path: Optional[Path] = None,
        discovered_networks: Optional[List[Dict[str, Any]]] = None,
        experiment_summary: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Generates a professional multi-page PDF report using ReportLab.
        Suitable for academic evaluation and technical documentation.
        Safely escapes all XML entities.
        """
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        if not output_path:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = REPORTS_DIR / f"NetVision_Report_{ts}.pdf"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=20,
            textColor=colors.HexColor("#0f172a"),
            leading=24
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            textColor=colors.HexColor("#475569"),
            leading=14
        )
        heading_style = ParagraphStyle(
            "DocHeading",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            textColor=colors.HexColor("#0284c7"),
            spaceBefore=12,
            spaceAfter=6,
            leading=16
        )
        body_style = ParagraphStyle(
            "DocBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            textColor=colors.HexColor("#1e293b"),
            leading=12
        )
        bold_cell_style = ParagraphStyle(
            "BoldCell",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            textColor=colors.HexColor("#0f172a"),
            leading=12
        )

        elements = []

        # Header Title
        elements.append(Paragraph("NetVision — Network Quality & Wi-Fi Audit Report", title_style))
        elements.append(Paragraph("Smart Network Quality & Wi-Fi Analyzer | BTech Academic Project Submission", subtitle_style))
        elements.append(Spacer(1, 8))
        elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#0284c7"), spaceAfter=12))

        # Metadata Table
        ssid_clean = escape_report_text(summary_info.get("ssid", "Not Connected"))
        bssid_clean = escape_report_text(summary_info.get("bssid", "N/A"))
        ip_clean = escape_report_text(summary_info.get("ip", "N/A"))
        band_clean = escape_report_text(summary_info.get("band", "N/A"))
        channel_clean = escape_report_text(summary_info.get("channel", "N/A"))
        gateway_clean = escape_report_text(summary_info.get("gateway", "Unavailable"))

        sig_val = summary_info.get("signal")
        sig_str = f"{sig_val}%" if sig_val is not None else "No data"
        cat_str = escape_report_text(summary_info.get("signal_category", "N/A"))

        meta_data = [
            [
                Paragraph("<b>Audit Date:</b>", body_style),
                Paragraph(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), body_style),
                Paragraph("<b>Active Network:</b>", body_style),
                Paragraph(ssid_clean, body_style),
            ],
            [
                Paragraph("<b>BSSID:</b>", body_style),
                Paragraph(bssid_clean, body_style),
                Paragraph("<b>Signal Quality:</b>", body_style),
                Paragraph(f"{sig_str} ({cat_str})", body_style),
            ],
            [
                Paragraph("<b>Channel / Band:</b>", body_style),
                Paragraph(f"Ch {channel_clean} ({band_clean})", body_style),
                Paragraph("<b>Local IPv4:</b>", body_style),
                Paragraph(ip_clean, body_style),
            ],
            [
                Paragraph("<b>Default Gateway:</b>", body_style),
                Paragraph(gateway_clean, body_style),
                Paragraph("<b>Measurement Mode:</b>", body_style),
                Paragraph("Native WLAN API & Chunked Edge Stream", body_style),
            ]
        ]
        meta_table = Table(meta_data, colWidths=[95, 175, 95, 175])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 12))

        # Speed Tests Section
        elements.append(Paragraph("1. Internet Throughput & Speed Test History", heading_style))
        if speed_tests:
            speed_rows = [[
                Paragraph("<b>Timestamp</b>", bold_cell_style),
                Paragraph("<b>Location</b>", bold_cell_style),
                Paragraph("<b>Download</b>", bold_cell_style),
                Paragraph("<b>Upload</b>", bold_cell_style),
                Paragraph("<b>Ping</b>", bold_cell_style),
                Paragraph("<b>Status</b>", bold_cell_style),
            ]]
            for s in speed_tests[:10]:
                d_str = f"{s['download_mbps']:.1f} Mbps" if s.get('download_mbps') is not None else "—"
                u_str = f"{s['upload_mbps']:.1f} Mbps" if s.get('upload_mbps') is not None else "—"
                p_str = f"{s['ping_ms']:.1f} ms" if s.get('ping_ms') is not None else "—"
                ts_str = escape_report_text(str(s.get("timestamp", ""))[:19].replace("T", " "))
                loc_str = escape_report_text(s.get("location_label", "Default"))
                st_str = escape_report_text(s.get("status", "completed"))

                speed_rows.append([
                    Paragraph(ts_str, body_style),
                    Paragraph(loc_str, body_style),
                    Paragraph(d_str, body_style),
                    Paragraph(u_str, body_style),
                    Paragraph(p_str, body_style),
                    Paragraph(st_str, body_style),
                ])
            speed_table = Table(speed_rows, colWidths=[110, 95, 85, 85, 75, 90])
            speed_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e0f2fe")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            elements.append(speed_table)
        else:
            elements.append(Paragraph("<i>No speed test records found in the selected range.</i>", body_style))

        elements.append(Spacer(1, 12))

        # Latency Tests Section
        elements.append(Paragraph("2. Round-Trip Latency, Jitter & Packet Loss", heading_style))
        if latency_tests:
            lat_rows = [[
                Paragraph("<b>Timestamp</b>", bold_cell_style),
                Paragraph("<b>Target Host</b>", bold_cell_style),
                Paragraph("<b>Method</b>", bold_cell_style),
                Paragraph("<b>Avg RTT</b>", bold_cell_style),
                Paragraph("<b>Jitter</b>", bold_cell_style),
                Paragraph("<b>Loss %</b>", bold_cell_style),
            ]]
            for l in latency_tests[:10]:
                rtt_str = f"{l['avg_rtt_ms']:.1f} ms" if l.get('avg_rtt_ms') is not None else "—"
                jit_str = f"{l['jitter_ms']:.1f} ms" if l.get('jitter_ms') is not None else "—"
                loss_str = f"{l['packet_loss_percent']:.1f}%" if l.get('packet_loss_percent') is not None else "—"
                ts_str = escape_report_text(str(l.get("timestamp", ""))[:19].replace("T", " "))
                host_str = escape_report_text(l.get("target_host", ""))
                meth_str = escape_report_text(l.get("method", "ICMP"))

                lat_rows.append([
                    Paragraph(ts_str, body_style),
                    Paragraph(host_str, body_style),
                    Paragraph(meth_str, body_style),
                    Paragraph(rtt_str, body_style),
                    Paragraph(jit_str, body_style),
                    Paragraph(loss_str, body_style),
                ])
            lat_table = Table(lat_rows, colWidths=[110, 110, 65, 85, 85, 85])
            lat_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            elements.append(lat_table)
        else:
            elements.append(Paragraph("<i>No latency test records found.</i>", body_style))

        elements.append(Spacer(1, 12))

        # Recommendations Section
        elements.append(Paragraph("3. Network Engineering Recommendations", heading_style))
        if recommendations:
            for rec in recommendations:
                sev = escape_report_text(rec.get("severity", "Info")).upper()
                title = escape_report_text(rec.get("title", ""))
                cat = escape_report_text(rec.get("category", ""))
                ev = escape_report_text(rec.get("evidence", ""))
                adv = escape_report_text(rec.get("advice", ""))

                rec_text = (
                    f"<b>[{sev}] {title}</b> <i>({cat})</i><br/>"
                    f"<b>Evidence:</b> {ev}<br/>"
                    f"<b>Recommendation:</b> {adv}"
                )
                elements.append(Paragraph(rec_text, body_style))
                elements.append(Spacer(1, 5))
        else:
            elements.append(Paragraph("<i>No diagnostic recommendations generated. Network metrics within standard bounds.</i>", body_style))

        # Academic Experiment Section if provided
        if experiment_summary:
            elements.append(Spacer(1, 12))
            elements.append(Paragraph("4. Academic Experiment & Pearson Correlation Summary", heading_style))
            exp_text = (
                f"<b>Total Empirical Trials:</b> {experiment_summary.get('trial_count', 0)}<br/>"
                f"<b>Mean Signal Quality:</b> {experiment_summary.get('mean_signal', '—')}% (σ: ±{experiment_summary.get('stdev_signal', 0)}%)<br/>"
                f"<b>Mean Throughput:</b> {experiment_summary.get('mean_download', '—')} Mbps (σ: ±{experiment_summary.get('stdev_download', 0)} Mbps)<br/>"
                f"<b>Mean Latency:</b> {experiment_summary.get('mean_latency', '—')} ms (σ: ±{experiment_summary.get('stdev_latency', 0)} ms)<br/>"
                f"<b>Pearson Correlation (Signal vs Download):</b> {escape_report_text(experiment_summary.get('r_interpretation', 'N/A'))}"
            )
            elements.append(Paragraph(exp_text, body_style))

        elements.append(Spacer(1, 16))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=8))
        elements.append(Paragraph("<i>Generated by NetVision Desktop Application — All measurements reflect actual network responses. Missing metrics are marked '—'.</i>", subtitle_style))

        doc.build(elements)
        return output_path
