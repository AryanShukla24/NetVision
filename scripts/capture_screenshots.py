"""
NetVision - Headless Screenshot Generator
Renders MainWindow across key navigation pages and saves high-resolution PNG images.
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Use offscreen platform for headless rendering
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication
from netvision.ui.main_window import MainWindow
from netvision.ui.theme import DARK_THEME_QSS
from netvision.database.db_manager import DatabaseManager
from netvision.database.models import (
    WifiNetwork, SpeedTestResult, LatencyTestResult,
    SignalLogEntry, ExperimentRun, ConnectedInterfaceInfo
)


def populate_demo_data(db: DatabaseManager):
    """Seeds rich illustrative data so screenshots showcase full interface capabilities."""
    # 1. Seed scan session
    nets = [
        WifiNetwork(ssid="Campus_FastNet_5G", bssid="00:1A:2B:3C:4D:5E", signal_percent=92, channel=36, frequency_band="5 GHz", security_type="WPA2-Enterprise", is_connected=True, radio_type="802.11ax"),
        WifiNetwork(ssid="College_Library_WiFi", bssid="10:20:30:40:50:60", signal_percent=78, channel=6, frequency_band="2.4 GHz", security_type="WPA2-Personal", is_connected=False, radio_type="802.11ax"),
        WifiNetwork(ssid="Hostel_BlockA_WLAN", bssid="A0:B1:C2:D3:E4:F5", signal_percent=64, channel=149, frequency_band="5 GHz", security_type="WPA2-Personal", is_connected=False, radio_type="802.11ac"),
        WifiNetwork(ssid="Academic_Guest_Open", bssid="44:55:66:77:88:99", signal_percent=45, channel=1, frequency_band="2.4 GHz", security_type="Open", is_connected=False, radio_type="802.11n"),
        WifiNetwork(ssid="Campus_IoT_Sensors", bssid="DE:AD:BE:EF:00:01", signal_percent=32, channel=11, frequency_band="2.4 GHz", security_type="WPA2-Personal", is_connected=False, radio_type="802.11g"),
    ]
    db.save_scan_session(nets, active_interface="Wi-Fi 6 AX201", location_label="College Library")

    # 2. Seed speed tests across locations
    db.save_speed_test(SpeedTestResult(download_mbps=88.4, upload_mbps=32.1, ping_ms=14.2, jitter_ms=1.5, duration_sec=7.2, server_name="Cloudflare Edge", network_ssid="Campus_FastNet_5G", location_label="College Library"))
    db.save_speed_test(SpeedTestResult(download_mbps=45.6, upload_mbps=18.3, ping_ms=28.4, jitter_ms=3.2, duration_sec=8.1, server_name="Cloudflare Edge", network_ssid="Campus_FastNet_5G", location_label="Classroom"))
    db.save_speed_test(SpeedTestResult(download_mbps=22.1, upload_mbps=8.5, ping_ms=54.1, jitter_ms=6.8, duration_sec=8.5, server_name="Cloudflare Edge", network_ssid="Campus_FastNet_5G", location_label="Cafe"))
    db.save_speed_test(SpeedTestResult(download_mbps=112.5, upload_mbps=48.0, ping_ms=9.8, jitter_ms=0.9, duration_sec=6.9, server_name="Cloudflare Edge", network_ssid="Home_Fiber_5G", location_label="Home"))

    # 3. Seed latency tests
    db.save_latency_test(LatencyTestResult(target_host="8.8.8.8", ping_count=10, min_rtt_ms=12.0, max_rtt_ms=22.0, avg_rtt_ms=15.4, jitter_ms=1.8, packet_loss_percent=0.0, network_ssid="Campus_FastNet_5G", location_label="College Library"))
    db.save_latency_test(LatencyTestResult(target_host="1.1.1.1", ping_count=10, min_rtt_ms=18.0, max_rtt_ms=48.0, avg_rtt_ms=29.2, jitter_ms=4.1, packet_loss_percent=0.0, network_ssid="Campus_FastNet_5G", location_label="Classroom"))

    # 4. Seed signal logs
    for sig in [90, 92, 91, 93, 89, 92, 94]:
        db.save_signal_log(SignalLogEntry(network_ssid="Campus_FastNet_5G", bssid="00:1A:2B:3C:4D:5E", signal_percent=sig, channel=36, frequency_band="5 GHz", location_label="College Library"))
    for sig in [60, 62, 58, 65, 63]:
        db.save_signal_log(SignalLogEntry(network_ssid="Campus_FastNet_5G", bssid="00:1A:2B:3C:4D:5E", signal_percent=sig, channel=36, frequency_band="5 GHz", location_label="Classroom"))

    # 5. Seed experiment runs
    for run_no, (s, d, p) in enumerate([(92, 88.5, 14.1), (90, 84.2, 15.0), (93, 89.1, 13.8), (91, 87.0, 14.5), (92, 88.0, 14.2)], start=1):
        db.save_experiment_run(ExperimentRun(experiment_id="EXP_DEMO_01", condition_label="Condition A (Near Router)", run_number=run_no, network_ssid="Campus_FastNet_5G", location_label="Library", signal_percent=s, ping_ms=p, jitter_ms=1.2, packet_loss_percent=0.0, download_mbps=d, upload_mbps=30.0))


def main():
    screenshots_dir = PROJECT_ROOT / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    app = QApplication([])
    app.setStyleSheet(DARK_THEME_QSS)

    db_path = PROJECT_ROOT / "data" / "screenshot_demo.db"
    if db_path.exists():
        db_path.unlink()
    db = DatabaseManager(db_path=db_path)
    populate_demo_data(db)

    window = MainWindow(db_manager=db)
    window.resize(1280, 800)
    window.show()

    # Configure mock connected interface for dashboard display
    mock_info = ConnectedInterfaceInfo(
        interface_name="Wi-Fi (Intel Wi-Fi 6 AX201)",
        description="Intel(R) Wi-Fi 6 AX201 160MHz",
        state="connected",
        ssid="Campus_FastNet_5G",
        bssid="00:1A:2B:3C:4D:5E",
        radio_type="802.11ax",
        authentication="WPA2-Enterprise",
        cipher="CCMP",
        channel=36,
        receive_rate_mbps=866.0,
        transmit_rate_mbps=866.0,
        signal_percent=92,
        frequency_band="5 GHz",
        ipv4_address="192.168.1.145",
        gateway="192.168.1.1"
    )
    window.page_dashboard.update_interface_info(mock_info)
    window.page_dashboard.update_latest_tests(db.get_latest_speed_test(), db.get_latest_latency_test())

    # Pages to capture
    pages_to_capture = [
        (0, "01_dashboard.png"),
        (1, "02_wifi_scanner.png"),
        (2, "03_signal_analyzer.png"),
        (3, "04_speed_test.png"),
        (4, "05_latency_monitor.png"),
        (5, "06_channel_analyzer.png"),
        (6, "07_history_analytics.png"),
        (7, "08_location_comparison.png"),
        (8, "09_academic_experiment.png"),
        (9, "10_audit_reports.png"),
    ]

    for page_idx, filename in pages_to_capture:
        window.switch_page(page_idx)
        app.processEvents()

        # Special page population for rich screenshots
        if page_idx == 1:
            window.page_scanner.display_networks(db.get_latest_networks())
        elif page_idx == 2:
            stability = {"mean": 91.5, "std_dev": 1.25, "min": 89, "max": 94, "range": 5, "stability_label": "Very Stable"}
            for s in [90, 92, 91, 93, 89, 92, 94]:
                entry = SignalLogEntry(network_ssid="Campus_FastNet_5G", bssid="00:1A:2B:3C:4D:5E", signal_percent=s, channel=36, frequency_band="5 GHz")
                window.page_signal.add_signal_sample(entry, stability)
        elif page_idx == 3:
            latest_sp = db.get_latest_speed_test()
            window.page_speed.display_result(latest_sp)
        elif page_idx == 4:
            latest_lat = db.get_latest_latency_test()
            window.page_latency.display_final_result(latest_lat)
        elif page_idx == 8:
            runs = db.get_experiment_runs("EXP_DEMO_01")
            for r in runs:
                exp_obj = ExperimentRun(**r)
                window.page_experiment.add_trial_run(exp_obj, 5)
            window.page_experiment.experiment_completed()

        app.processEvents()
        save_path = screenshots_dir / filename
        pixmap = window.grab()
        pixmap.save(str(save_path), "PNG")
        print(f"Captured: {save_path.name}")

    window.close()
    print("All screenshots generated successfully.")


if __name__ == "__main__":
    main()
