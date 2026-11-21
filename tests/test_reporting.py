"""
Unit Tests for CSV and PDF Report Generation
Ensures file exports create valid non-empty files with proper data structure,
Excel-safe encoding, formula injection sanitization, and XML entity escaping.
"""

import tempfile
from pathlib import Path
from netvision.core.reporter import ReportGenerator, sanitize_csv_cell, escape_report_text


def test_sanitize_csv_cell():
    """Verifies DDE formula injection prevention while keeping numeric values intact."""
    assert sanitize_csv_cell("=1+1") == "'=1+1"
    assert sanitize_csv_cell("+cmd|' /C calc'!A0") == "'+cmd|' /C calc'!A0"
    assert sanitize_csv_cell("@SUM(A1:A10)") == "'@SUM(A1:A10)"
    assert sanitize_csv_cell("-malicious") == "'-malicious"
    
    # Valid numbers (positive and negative) should remain numbers
    assert sanitize_csv_cell(42) == 42
    assert sanitize_csv_cell(-75.5) == -75.5
    assert sanitize_csv_cell("-75") == "-75"
    assert sanitize_csv_cell(None) == ""
    assert sanitize_csv_cell("Normal Text") == "Normal Text"


def test_escape_report_text():
    """Verifies XML entity escaping for ReportLab strings."""
    assert escape_report_text("<Hidden SSID>") == "&lt;Hidden SSID&gt;"
    assert escape_report_text("AT&T Wi-Fi") == "AT&amp;T Wi-Fi"
    assert escape_report_text(None) == "—"
    assert escape_report_text(85) == "85"


def test_csv_export_utf8_sig_and_nulls():
    """Tests CSV export with UTF-8 BOM, formula protection, and NULL handling."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_csv = Path(tmp_dir) / "test_report.csv"
        speed_tests = [
            {
                "timestamp": "2026-11-17T12:00:00",
                "network_ssid": "=MaliciousSSID",
                "location_label": "Library",
                "download_mbps": 45.2,
                "upload_mbps": 12.8,
                "ping_ms": 22.0,
                "jitter_ms": 1.8,
                "server_name": "Edge Server",
                "status": "completed"
            },
            {
                "timestamp": "2026-11-17T12:01:00",
                "network_ssid": "FailedNet",
                "location_label": "Office",
                "download_mbps": None,  # Should be empty string, not 0.0
                "upload_mbps": None,
                "ping_ms": None,
                "jitter_ms": None,
                "server_name": "Edge Server",
                "status": "failed"
            }
        ]
        latency_tests = [{
            "timestamp": "2026-11-17T12:05:00",
            "network_ssid": "Test_WiFi",
            "location_label": "Library",
            "avg_rtt_ms": None,
            "jitter_ms": None,
            "packet_loss_percent": 100.0,
            "target_host": "8.8.8.8",
            "method": "ICMP",
            "status": "failed"
        }]
        signal_logs = [{
            "timestamp": "2026-11-17T12:10:00",
            "network_ssid": "@PublicWiFi",
            "location_label": "Library",
            "signal_percent": 82,
            "bssid": "00:11:22:33:44:55"
        }]

        res_path = ReportGenerator.export_csv(speed_tests, latency_tests, signal_logs, output_path=out_csv)
        assert res_path.exists()
        assert res_path.stat().st_size > 0

        # Check UTF-8 BOM
        raw_bytes = res_path.read_bytes()
        assert raw_bytes[:3] == b"\xef\xbb\xbf"

        content = res_path.read_text(encoding="utf-8-sig")
        assert "'=MaliciousSSID" in content
        assert "'@PublicWiFi" in content
        assert "45.20" in content
        assert "SpeedTest" in content
        assert "LatencyTest" in content
        assert "SignalLog" in content


def test_pdf_export_with_special_characters_and_nulls():
    """Tests ReportLab PDF compilation with XML special characters and NULL measurements."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_pdf = Path(tmp_dir) / "test_report.pdf"
        summary = {
            "ssid": "<Hidden SSID>",
            "bssid": "00:11:22:33:44:55 & 66",
            "signal": None,
            "signal_category": "No data",
            "channel": None,
            "band": None,
            "ip": "192.168.1.100",
            "gateway": "192.168.1.1"
        }
        speed_tests = [
            {
                "timestamp": "2026-11-17T12:00:00",
                "location_label": "<Lab & Office>",
                "download_mbps": None,
                "upload_mbps": None,
                "ping_ms": None,
                "status": "failed"
            },
            {
                "timestamp": "2026-11-17T12:01:00",
                "location_label": "CS Lab",
                "download_mbps": 82.4,
                "upload_mbps": 35.1,
                "ping_ms": 14.2,
                "status": "completed"
            }
        ]
        latency_tests = [{
            "timestamp": "2026-11-17T12:02:00",
            "target_host": "<dns.google>",
            "avg_rtt_ms": None,
            "min_rtt_ms": None,
            "max_rtt_ms": None,
            "jitter_ms": None,
            "packet_loss_percent": 100.0,
            "method": "ICMP",
            "status": "failed"
        }]
        recommendations = [{
            "title": "Suboptimal <RF> & Channel",
            "category": "Wi-Fi RF",
            "severity": "Warning",
            "evidence": "Signal is < 30% & Channel congested",
            "advice": "Switch to 5 GHz channel 36 & keep line of sight."
        }]
        exp_summary = {
            "trial_count": 5,
            "mean_signal": 75.0,
            "stdev_signal": 3.2,
            "mean_download": 45.0,
            "stdev_download": 4.1,
            "mean_latency": 18.0,
            "stdev_latency": 1.5,
            "r_interpretation": "r = +0.892 (Strong Positive)"
        }

        # Must not raise XML syntax error or LayoutError
        res_path = ReportGenerator.export_pdf(
            summary_info=summary,
            speed_tests=speed_tests,
            latency_tests=latency_tests,
            recommendations=recommendations,
            output_path=out_pdf,
            experiment_summary=exp_summary
        )
        assert res_path.exists()
        assert res_path.stat().st_size > 1000
