"""
Unit Tests for NetVision Database Operations
Tests SQLite initialization, CRUD transactions, safe migrations, NULL handling, and deletions.
"""

import pytest
import tempfile
import gc
from pathlib import Path

from netvision.database.db_manager import DatabaseManager
from netvision.database.models import (
    WifiNetwork, SpeedTestResult, LatencyTestResult,
    SignalLogEntry, ExperimentRun
)


@pytest.fixture
def temp_db():
    """Provides a fresh isolated temporary SQLite database for testing."""
    tmp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    db_file = Path(tmp_dir.name) / "test_netvision.db"
    manager = DatabaseManager(db_path=db_file)
    yield manager
    gc.collect()
    try:
        tmp_dir.cleanup()
    except Exception:
        pass


def test_database_initialization(temp_db):
    """Verifies that all required tables, schema version, and default locations are populated."""
    locations = temp_db.get_locations()
    assert "Home" in locations
    assert "College Library" in locations
    assert len(locations) >= 5

    # Check WAL mode and schema version
    with temp_db.get_connection() as conn:
        cursor = conn.cursor()
        v = cursor.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
        assert v >= 2
        wal = cursor.execute("PRAGMA journal_mode;").fetchone()[0]
        assert wal.lower() == "wal"


def test_save_and_retrieve_scan_session(temp_db):
    """Verifies scan session and Wi-Fi networks persistence."""
    sample_networks = [
        WifiNetwork(ssid="Campus_AP1", bssid="00:11:22:33:44:55", signal_percent=88, channel=6, frequency_band="2.4 GHz"),
        WifiNetwork(ssid="Campus_AP2", bssid="aa:bb:cc:dd:ee:ff", signal_percent=64, channel=36, frequency_band="5 GHz")
    ]
    session_id = temp_db.save_scan_session(sample_networks, active_interface="Wi-Fi", location_label="Library")
    assert session_id > 0

    latest = temp_db.get_latest_networks()
    assert len(latest) == 2
    assert latest[0].ssid == "Campus_AP1"
    assert latest[0].signal_percent == 88


def test_speed_test_crud(temp_db):
    """Verifies speed test saving, querying, and latest fetching."""
    result = SpeedTestResult(
        download_mbps=75.5,
        upload_mbps=24.2,
        ping_ms=18.4,
        jitter_ms=2.1,
        duration_sec=8.5,
        server_name="Test Edge",
        network_ssid="Lab_WiFi",
        location_label="Classroom"
    )
    rec_id = temp_db.save_speed_test(result)
    assert rec_id > 0

    latest = temp_db.get_latest_speed_test()
    assert latest is not None
    assert latest.download_mbps == 75.5
    assert latest.upload_mbps == 24.2
    assert latest.location_label == "Classroom"


def test_speed_test_null_handling(temp_db):
    """Verifies that failed or cancelled speed tests preserve NULLs and do not become 0.0."""
    failed_result = SpeedTestResult(
        download_mbps=None,
        upload_mbps=None,
        ping_ms=None,
        jitter_ms=None,
        duration_sec=2.1,
        server_name="Cloudflare Edge",
        network_ssid="Office_WiFi",
        location_label="Office",
        status="failed",
        error_message="Connection timed out"
    )
    rec_id = temp_db.save_speed_test(failed_result)
    assert rec_id > 0

    records = temp_db.get_speed_tests(limit=1, status="failed")
    assert len(records) == 1
    assert records[0]["download_mbps"] is None
    assert records[0]["upload_mbps"] is None
    assert records[0]["ping_ms"] is None
    assert records[0]["status"] == "failed"


def test_latency_test_crud(temp_db):
    """Verifies latency test storage and retrieval."""
    lat_result = LatencyTestResult(
        target_host="1.1.1.1",
        ping_count=10,
        min_rtt_ms=12.0,
        max_rtt_ms=28.0,
        avg_rtt_ms=16.5,
        jitter_ms=3.2,
        packet_loss_percent=0.0,
        method="ICMP",
        network_ssid="Home_5G",
        location_label="Living Room"
    )
    rec_id = temp_db.save_latency_test(lat_result)
    assert rec_id > 0

    latest = temp_db.get_latest_latency_test()
    assert latest is not None
    assert latest.avg_rtt_ms == 16.5
    assert latest.jitter_ms == 3.2
    assert latest.packet_loss_percent == 0.0
    assert latest.method == "ICMP"


def test_latency_test_null_on_total_loss(temp_db):
    """Verifies that 100% packet loss preserves NULL for RTT and jitter."""
    total_loss_result = LatencyTestResult(
        target_host="192.0.2.1",
        ping_count=5,
        min_rtt_ms=None,
        max_rtt_ms=None,
        avg_rtt_ms=None,
        jitter_ms=None,
        packet_loss_percent=100.0,
        method="ICMP",
        status="completed",
        network_ssid="DeadZone",
        location_label="Basement"
    )
    rec_id = temp_db.save_latency_test(total_loss_result)
    assert rec_id > 0

    records = temp_db.get_latency_tests(limit=1, location="Basement")
    assert len(records) == 1
    assert records[0]["min_rtt_ms"] is None
    assert records[0]["avg_rtt_ms"] is None
    assert records[0]["jitter_ms"] is None
    assert records[0]["packet_loss_percent"] == 100.0


def test_signal_log_crud(temp_db):
    """Verifies signal log recording."""
    entry = SignalLogEntry(
        network_ssid="Office_WLAN",
        bssid="00:14:22:01:23:45",
        signal_percent=72,
        channel=11,
        frequency_band="2.4 GHz",
        location_label="Office"
    )
    log_id = temp_db.save_signal_log(entry)
    assert log_id > 0

    logs = temp_db.get_signal_logs(limit=10)
    assert len(logs) == 1
    assert logs[0]["signal_percent"] == 72


def test_experiment_run_crud(temp_db):
    """Verifies saving academic multi-run experiment records with status and target."""
    exp_run = ExperimentRun(
        experiment_id="EXP_TEST_01",
        condition_label="Condition A",
        run_number=1,
        network_ssid="College_WiFi",
        location_label="Lab 1",
        signal_percent=85,
        ping_ms=22.0,
        jitter_ms=1.5,
        packet_loss_percent=0.0,
        download_mbps=64.0,
        upload_mbps=18.0,
        target_host="8.8.8.8",
        status="completed"
    )
    run_id = temp_db.save_experiment_run(exp_run)
    assert run_id > 0

    runs = temp_db.get_experiment_runs(experiment_id="EXP_TEST_01")
    assert len(runs) == 1
    assert runs[0]["download_mbps"] == 64.0
    assert runs[0]["target_host"] == "8.8.8.8"
    assert runs[0]["status"] == "completed"


def test_get_records_by_locations(temp_db):
    """Verifies querying records across multiple custom locations without global limits."""
    temp_db.save_speed_test(SpeedTestResult(download_mbps=50.0, upload_mbps=10.0, location_label="LocA"))
    temp_db.save_speed_test(SpeedTestResult(download_mbps=20.0, upload_mbps=5.0, location_label="LocB"))
    temp_db.save_speed_test(SpeedTestResult(download_mbps=10.0, upload_mbps=2.0, location_label="LocC"))

    locs = ["LocA", "LocB"]
    results = temp_db.get_speed_tests_by_locations(locs)
    labels = {r["location_label"] for r in results}
    assert labels == {"LocA", "LocB"}
    assert "LocC" not in labels


def test_delete_record(temp_db):
    """Verifies deleting historical records with table validation."""
    result = SpeedTestResult(download_mbps=10.0, upload_mbps=2.0)
    rec_id = temp_db.save_speed_test(result)
    assert temp_db.delete_record("speed_tests", rec_id) is True

    # Deleting non-existent record returns False
    assert temp_db.delete_record("speed_tests", 99999) is False

    # Disallowed table raises ValueError
    with pytest.raises(ValueError):
        temp_db.delete_record("malicious_table_drop", 1)


def test_app_settings(temp_db):
    """Verifies key-value settings storage."""
    temp_db.set_setting("theme", "dark_slate")
    val = temp_db.get_setting("theme")
    assert val == "dark_slate"

    # Upsert
    temp_db.set_setting("theme", "midnight")
    assert temp_db.get_setting("theme") == "midnight"
