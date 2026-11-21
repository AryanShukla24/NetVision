"""
NetVision - Genuine Live Application Screenshot Collector
Launches the real MainWindow using native Windows Qt rendering (crisp system fonts),
collects genuine live measurements from this Windows machine & existing user SQLite DB,
and saves high-resolution screenshots of all implemented pages to docs/screenshots/.

Strictly adheres to measurement integrity:
- No mock/fake networks, no synthetic data, no fabricated speed/latency numbers.
- Uses real local database (%LOCALAPPDATA%\\NetVision\\database\\netvision.db).
"""

import os
import sys
import json
import time
import shutil
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
sys.path.insert(0, str(SRC_DIR))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from netvision.config import DEFAULT_DB_PATH, APP_VERSION, USER_DATA_DIR
from netvision.ui.main_window import MainWindow
from netvision.ui.theme import DARK_THEME_QSS
from netvision.database.db_manager import DatabaseManager
from netvision.core.wifi_scanner import WifiScanner
from netvision.core.latency_monitor import LatencyMonitor
from netvision.core.speed_tester import SpeedTester
from netvision.core.signal_monitor import SignalMonitor
from netvision.core.channel_analyzer import ChannelAnalyzer
from netvision.core.recommendation_engine import RecommendationEngine


def collect_db_stats(db: DatabaseManager) -> dict:
    stats = {}
    with db.get_connection() as conn:
        for tbl in [
            "scan_sessions", "wifi_networks", "speed_tests",
            "latency_tests", "signal_logs", "locations",
            "experiment_runs", "app_settings"
        ]:
            row = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()
            stats[tbl] = row[0] if row else 0
    return stats


def main():
    out_dir = ROOT_DIR / "docs" / "screenshots"
    out_dir.mkdir(parents=True, exist_ok=True)
    assets_img_dir = ROOT_DIR / "assets" / "images"
    assets_img_dir.mkdir(parents=True, exist_ok=True)

    print("1. Connecting to real user database:", DEFAULT_DB_PATH)
    db = DatabaseManager(db_path=DEFAULT_DB_PATH)
    initial_stats = collect_db_stats(db)
    print("   Initial DB row counts:", initial_stats)

    # 2. Perform genuine live hardware & network observations
    scanner = WifiScanner()
    print("2. Reading active Windows wireless interface...")
    conn_info = scanner.get_connected_interface()
    print(f"   Connected: state={conn_info.state}, ssid={conn_info.ssid}, signal={conn_info.signal_percent}%, ch={conn_info.channel} ({conn_info.frequency_band})")

    print("3. Executing active Wi-Fi scan (wlanapi + netsh)...")
    networks, scan_err = scanner.scan_networks()
    print(f"   Discovered {len(networks)} real wireless networks (error={scan_err})")
    if networks:
        db.save_scan_session(networks, active_interface=conn_info.interface_name or "Wi-Fi", location_label="Home")

    # 4. Run genuine live ICMP latency test (6 probes to 8.8.8.8)
    print("4. Running genuine live ICMP ping probes to 8.8.8.8 (6 probes)...")
    lat_mon = LatencyMonitor(target_host="8.8.8.8", method="ICMP")
    live_rtts = []

    def on_probe(step, total, rtt):
        live_rtts.append(rtt)

    lat_result = lat_mon.run_test(
        count=6,
        interval_sec=0.2,
        progress_callback=on_probe,
        network_ssid=conn_info.ssid or "",
        location_label="Home"
    )
    db.save_latency_test(lat_result)
    print(f"   ICMP Result: avg={lat_result.avg_rtt_ms} ms, jitter={lat_result.jitter_ms} ms, loss={lat_result.packet_loss_percent}%")

    # 5. Collect 6 genuine signal samples from active interface
    print("5. Collecting 6 genuine real-time Wi-Fi signal samples...")
    sig_mon = SignalMonitor(db_manager=db)
    live_signal_entries = []
    for _ in range(6):
        entry, is_conn, _ = sig_mon.monitor_tick(location_label="Home")
        if is_conn and entry:
            live_signal_entries.append(entry)
        time.sleep(0.25)
    sig_stability = sig_mon.get_stability_summary()
    print(f"   Signal samples collected: {len(live_signal_entries)}, stability={sig_stability}")

    # 6. Check latest speed test in DB; if none completed, run 1 genuine Cloudflare speed test
    latest_speed = db.get_latest_speed_test()
    if not latest_speed or getattr(latest_speed, "status", None) != "completed" or getattr(latest_speed, "download_mbps", None) is None:
        print("6. No completed speed test in DB; running 1 genuine Cloudflare CDN speed test...")
        st = SpeedTester()
        sp_res = st.run_speed_test(network_ssid=conn_info.ssid or "", location_label="Home")
        db.save_speed_test(sp_res)
        latest_speed = db.get_latest_speed_test()
        print(f"   Speed test result: down={sp_res.download_mbps} Mbps, up={sp_res.upload_mbps} Mbps, status={sp_res.status}")
    else:
        print(f"6. Using genuine completed speed test from DB: down={latest_speed.download_mbps} Mbps, up={latest_speed.upload_mbps} Mbps")

    # 7. Launch real Qt MainWindow using native Windows platform rendering
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME_QSS)

    window = MainWindow(db_manager=db)
    window.resize(1360, 840)
    # Position on screen cleanly so Windows renders native fonts with ClearType
    window.move(40, 20)
    window.show()
    app.processEvents()
    time.sleep(0.5)
    app.processEvents()

    # Populate pages with genuine live observations & DB records
    latest_latency = db.get_latest_latency_test()
    window.page_dashboard.update_interface_info(conn_info)
    window.page_dashboard.update_latest_tests(latest_speed, latest_latency)

    # Scanner & Channel Analyzer
    display_nets = networks if networks else db.get_latest_networks()
    window.page_scanner.display_networks(display_nets)
    ch_analysis = ChannelAnalyzer.analyze_channels(display_nets)
    window.page_channel.display_analysis(ch_analysis)

    # Signal Analyzer
    for entry in live_signal_entries:
        window.page_signal.add_signal_sample(entry, sig_stability)

    # Speed Test page
    if latest_speed:
        window.page_speed.display_result(latest_speed)

    # Latency Monitor page
    for idx, rtt_val in enumerate(live_rtts, start=1):
        window.page_latency.add_probe_result(idx, len(live_rtts), rtt_val)
    window.page_latency.display_final_result(lat_result)

    # History, Comparison, Reports, Experiment pages
    window._refresh_history_page()
    locs = db.get_locations()
    window._refresh_comparison_page(locs)
    window._refresh_reports_page()

    # Load saved experiments if any exist in DB
    window._load_saved_experiments()
    saved_exps = db.get_experiment_runs()
    if saved_exps:
        from netvision.database.models import ExperimentRun
        exp_ids = []
        for r in saved_exps:
            eid = r["experiment_id"] if isinstance(r, dict) else r.experiment_id
            if eid not in exp_ids:
                exp_ids.append(eid)
        if exp_ids:
            latest_eid = exp_ids[0]
            matching = [r for r in saved_exps if (r["experiment_id"] if isinstance(r, dict) else r.experiment_id) == latest_eid]
            for r in matching:
                if isinstance(r, dict):
                    dto = ExperimentRun(
                        experiment_id=r["experiment_id"],
                        condition_label=r["condition_label"],
                        run_number=r["run_number"],
                        network_ssid=r.get("network_ssid", ""),
                        location_label=r.get("location_label", ""),
                        signal_percent=r.get("signal_percent"),
                        ping_ms=r.get("ping_ms"),
                        jitter_ms=r.get("jitter_ms"),
                        packet_loss_percent=r.get("packet_loss_percent"),
                        download_mbps=r.get("download_mbps"),
                        upload_mbps=r.get("upload_mbps"),
                        target_host=r.get("target_host", "8.8.8.8"),
                        status=r.get("status", "completed"),
                        timestamp=r.get("timestamp", ""),
                    )
                else:
                    dto = r
                window.page_experiment.add_trial_run(dto, len(matching))

    pages = [
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
        (10, "11_settings.png"),
        (11, "12_about_netvision.png"),
    ]

    captured = []
    for idx, fname in pages:
        window.switch_page(idx)
        app.processEvents()
        time.sleep(0.25)
        app.processEvents()

        pixmap = window.grab()
        dst = out_dir / fname
        pixmap.save(str(dst), "PNG")
        shutil.copy2(dst, assets_img_dir / fname)
        captured.append(fname)
        print(f"   Captured {fname} ({pixmap.width()}x{pixmap.height()})")

    # Save genuine telemetry summary for documentation accuracy
    final_stats = collect_db_stats(db)
    summary = {
        "captured_at": datetime.now().isoformat(),
        "app_version": APP_VERSION,
        "db_path": str(DEFAULT_DB_PATH),
        "db_counts": final_stats,
        "connected_interface": {
            "interface_name": conn_info.interface_name,
            "description": conn_info.description,
            "state": conn_info.state,
            "ssid": conn_info.ssid,
            "bssid": conn_info.bssid,
            "radio_type": conn_info.radio_type,
            "authentication": conn_info.authentication,
            "cipher": conn_info.cipher,
            "channel": conn_info.channel,
            "frequency_band": conn_info.frequency_band,
            "signal_percent": conn_info.signal_percent,
            "receive_rate_mbps": conn_info.receive_rate_mbps,
            "transmit_rate_mbps": conn_info.transmit_rate_mbps,
            "ipv4_address": conn_info.ipv4_address,
            "gateway": conn_info.gateway,
            "dns_servers": conn_info.dns_servers,
        },
        "wifi_scan_count": len(display_nets),
        "scan_error": scan_err,
        "channel_analysis_24": ch_analysis.get("band_24", {}),
        "channel_analysis_5": ch_analysis.get("band_5", {}),
        "live_latency_test": {
            "target_host": lat_result.target_host,
            "ping_count": lat_result.ping_count,
            "min_rtt_ms": lat_result.min_rtt_ms,
            "max_rtt_ms": lat_result.max_rtt_ms,
            "avg_rtt_ms": lat_result.avg_rtt_ms,
            "jitter_ms": lat_result.jitter_ms,
            "packet_loss_percent": lat_result.packet_loss_percent,
            "method": lat_result.method,
            "status": lat_result.status,
        },
        "latest_speed_test": (latest_speed.__dict__ if hasattr(latest_speed, "__dict__") else dict(latest_speed)) if latest_speed else None,
        "signal_stability": sig_stability,
        "locations": locs,
        "experiment_runs_count": len(saved_exps),
        "captured_files": captured,
    }
    summary_path = out_dir / "live_telemetry_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nSaved genuine telemetry summary to {summary_path}")

    window.close()
    app.quit()


if __name__ == "__main__":
    main()
