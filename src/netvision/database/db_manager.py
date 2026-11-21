"""
NetVision - Database Manager
Handles SQLite database connection, table schemas, safe migrations, and CRUD operations.
Supports WAL mode, NULL handling for unavailable metrics, and schema versioning.
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from netvision.config import DEFAULT_DB_PATH
from netvision.database.models import (
    WifiNetwork,
    SpeedTestResult,
    LatencyTestResult,
    SignalLogEntry,
    ExperimentRun
)

logger = logging.getLogger(__name__)

CURRENT_SCHEMA_VERSION = 2


class DatabaseManager:
    """Manages SQLite storage for network observations, speed tests, and telemetry."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()

    def get_connection(self) -> sqlite3.Connection:
        """Returns a configured SQLite connection with row factories and WAL enabled."""
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        return conn

    def init_database(self) -> None:
        """Creates tables, indices, and executes safe migrations."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Schema versioning table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL,
                description TEXT NOT NULL
            );
            """)

            # 1. Network Scan Sessions
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                total_networks INTEGER NOT NULL DEFAULT 0,
                active_interface TEXT,
                location_label TEXT DEFAULT 'Default'
            );
            """)

            # 2. Discovered Wi-Fi Networks
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS wifi_networks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                ssid TEXT NOT NULL,
                bssid TEXT,
                signal_percent INTEGER NOT NULL,
                channel INTEGER,
                frequency_band TEXT,
                security_type TEXT,
                is_connected INTEGER DEFAULT 0,
                radio_type TEXT,
                observed_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES scan_sessions(id) ON DELETE CASCADE
            );
            """)

            # 3. Speed Tests (allows NULL for failed/cancelled runs)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS speed_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                download_mbps REAL,
                upload_mbps REAL,
                ping_ms REAL,
                jitter_ms REAL,
                duration_sec REAL DEFAULT 0.0,
                server_name TEXT,
                network_ssid TEXT,
                location_label TEXT DEFAULT 'Default',
                status TEXT DEFAULT 'completed',
                error_message TEXT
            );
            """)

            # 4. Latency / Ping Tests (allows NULL for 100% loss / failed runs)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS latency_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                target_host TEXT NOT NULL,
                ping_count INTEGER NOT NULL,
                min_rtt_ms REAL,
                max_rtt_ms REAL,
                avg_rtt_ms REAL,
                jitter_ms REAL,
                packet_loss_percent REAL NOT NULL,
                method TEXT DEFAULT 'ICMP',
                status TEXT DEFAULT 'completed',
                network_ssid TEXT,
                location_label TEXT DEFAULT 'Default'
            );
            """)

            # 5. Continuous Signal Monitoring Logs
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS signal_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                network_ssid TEXT NOT NULL,
                bssid TEXT,
                signal_percent INTEGER NOT NULL,
                channel INTEGER,
                frequency_band TEXT,
                location_label TEXT DEFAULT 'Default'
            );
            """)

            # 6. Custom Location Labels
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL,
                description TEXT
            );
            """)

            # 7. Experiment Runs
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiment_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id TEXT NOT NULL,
                condition_label TEXT NOT NULL,
                run_number INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                network_ssid TEXT,
                location_label TEXT,
                signal_percent INTEGER,
                ping_ms REAL,
                jitter_ms REAL,
                packet_loss_percent REAL,
                download_mbps REAL,
                upload_mbps REAL,
                target_host TEXT DEFAULT '8.8.8.8',
                status TEXT DEFAULT 'completed'
            );
            """)

            # 8. Application Settings (Key-Value)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """)

            # Default locations
            defaults = ["Home", "College Library", "Classroom", "Cafe", "Office"]
            now_iso = datetime.now().isoformat()
            for loc in defaults:
                cursor.execute(
                    "INSERT OR IGNORE INTO locations (name, created_at, description) VALUES (?, ?, ?)",
                    (loc, now_iso, f"Default location tag: {loc}")
                )

            # Performance indices
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_wifi_session ON wifi_networks(session_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_speed_time ON speed_tests(timestamp);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_speed_loc ON speed_tests(location_label);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_latency_time ON latency_tests(timestamp);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_latency_loc ON latency_tests(location_label);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_signal_time ON signal_logs(timestamp);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_signal_loc ON signal_logs(location_label);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_experiment_id ON experiment_runs(experiment_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_experiment_loc ON experiment_runs(location_label);")

            conn.commit()

            # Execute migration if needed
            self._apply_migrations(conn)

    def _apply_migrations(self, conn: sqlite3.Connection) -> None:
        """Safely applies incremental schema migrations preserving existing user data."""
        cursor = conn.cursor()
        v_row = cursor.execute("SELECT MAX(version) FROM schema_version").fetchone()
        current_version = v_row[0] if v_row and v_row[0] is not None else 1

        if current_version < 2:
            logger.info("Migrating database schema from v1 to v2 (allowing NULLs and adding columns)...")

            # Check if latency_tests has NOT NULL on min_rtt_ms
            cols = {c[1]: c for c in cursor.execute("PRAGMA table_info(latency_tests)").fetchall()}
            if "method" not in cols or cols.get("min_rtt_ms", [0, 0, 0, 0])[3] == 1:
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS latency_tests_v2 (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    target_host TEXT NOT NULL,
                    ping_count INTEGER NOT NULL,
                    min_rtt_ms REAL,
                    max_rtt_ms REAL,
                    avg_rtt_ms REAL,
                    jitter_ms REAL,
                    packet_loss_percent REAL NOT NULL,
                    method TEXT DEFAULT 'ICMP',
                    status TEXT DEFAULT 'completed',
                    network_ssid TEXT,
                    location_label TEXT DEFAULT 'Default'
                );
                """)
                has_method = "method" in cols
                has_status = "status" in cols
                sel_m = "method" if has_method else "'ICMP'"
                sel_s = "status" if has_status else "'completed'"
                cursor.execute(f"""
                INSERT INTO latency_tests_v2 (id, timestamp, target_host, ping_count, min_rtt_ms, max_rtt_ms, avg_rtt_ms, jitter_ms, packet_loss_percent, method, status, network_ssid, location_label)
                SELECT id, timestamp, target_host, ping_count, min_rtt_ms, max_rtt_ms, avg_rtt_ms, jitter_ms, packet_loss_percent, {sel_m}, {sel_s}, network_ssid, location_label
                FROM latency_tests;
                """)
                cursor.execute("DROP TABLE latency_tests;")
                cursor.execute("ALTER TABLE latency_tests_v2 RENAME TO latency_tests;")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_latency_time ON latency_tests(timestamp);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_latency_loc ON latency_tests(location_label);")

            # Check if speed_tests has NOT NULL on download_mbps
            cols_sp = {c[1]: c for c in cursor.execute("PRAGMA table_info(speed_tests)").fetchall()}
            if cols_sp.get("download_mbps", [0, 0, 0, 0])[3] == 1:
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS speed_tests_v2 (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    download_mbps REAL,
                    upload_mbps REAL,
                    ping_ms REAL,
                    jitter_ms REAL,
                    duration_sec REAL DEFAULT 0.0,
                    server_name TEXT,
                    network_ssid TEXT,
                    location_label TEXT DEFAULT 'Default',
                    status TEXT DEFAULT 'completed',
                    error_message TEXT
                );
                """)
                cursor.execute("""
                INSERT INTO speed_tests_v2 (id, timestamp, download_mbps, upload_mbps, ping_ms, jitter_ms, duration_sec, server_name, network_ssid, location_label, status, error_message)
                SELECT id, timestamp, download_mbps, upload_mbps, ping_ms, jitter_ms, duration_sec, server_name, network_ssid, location_label, status, error_message
                FROM speed_tests;
                """)
                cursor.execute("DROP TABLE speed_tests;")
                cursor.execute("ALTER TABLE speed_tests_v2 RENAME TO speed_tests;")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_speed_time ON speed_tests(timestamp);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_speed_loc ON speed_tests(location_label);")

            # Check if experiment_runs has target_host and status
            cols_exp = {c[1]: c for c in cursor.execute("PRAGMA table_info(experiment_runs)").fetchall()}
            if "target_host" not in cols_exp or "status" not in cols_exp:
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS experiment_runs_v2 (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    experiment_id TEXT NOT NULL,
                    condition_label TEXT NOT NULL,
                    run_number INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    network_ssid TEXT,
                    location_label TEXT,
                    signal_percent INTEGER,
                    ping_ms REAL,
                    jitter_ms REAL,
                    packet_loss_percent REAL,
                    download_mbps REAL,
                    upload_mbps REAL,
                    target_host TEXT DEFAULT '8.8.8.8',
                    status TEXT DEFAULT 'completed'
                );
                """)
                sel_th = "target_host" if "target_host" in cols_exp else "'8.8.8.8'"
                sel_st = "status" if "status" in cols_exp else "'completed'"
                cursor.execute(f"""
                INSERT INTO experiment_runs_v2 (id, experiment_id, condition_label, run_number, timestamp, network_ssid, location_label, signal_percent, ping_ms, jitter_ms, packet_loss_percent, download_mbps, upload_mbps, target_host, status)
                SELECT id, experiment_id, condition_label, run_number, timestamp, network_ssid, location_label, signal_percent, ping_ms, jitter_ms, packet_loss_percent, download_mbps, upload_mbps, {sel_th}, {sel_st}
                FROM experiment_runs;
                """)
                cursor.execute("DROP TABLE experiment_runs;")
                cursor.execute("ALTER TABLE experiment_runs_v2 RENAME TO experiment_runs;")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_experiment_id ON experiment_runs(experiment_id);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_experiment_loc ON experiment_runs(location_label);")

            now = datetime.now().isoformat()
            cursor.execute(
                "INSERT OR REPLACE INTO schema_version (version, applied_at, description) VALUES (?, ?, ?)",
                (2, now, "Allow NULL values for missing metrics, add status/method/target_host columns, enable WAL mode and indexes")
            )
            conn.commit()
            logger.info("Database schema successfully migrated to v2.")

    # --- Scan Sessions & Networks ---

    def save_scan_session(self, networks: List[WifiNetwork], active_interface: str = "", location_label: str = "Default") -> int:
        """Saves a scan session and its discovered networks atomically."""
        now_str = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO scan_sessions (timestamp, total_networks, active_interface, location_label) VALUES (?, ?, ?, ?)",
                (now_str, len(networks), active_interface, location_label)
            )
            session_id = cursor.lastrowid
            for net in networks:
                cursor.execute("""
                INSERT INTO wifi_networks (
                    session_id, ssid, bssid, signal_percent, channel, frequency_band, security_type, is_connected, radio_type, observed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id, net.ssid, net.bssid, net.signal_percent, net.channel,
                    net.frequency_band, net.security_type, 1 if net.is_connected else 0,
                    net.radio_type, net.observed_at or now_str
                ))
            conn.commit()
            return session_id

    def get_latest_networks(self) -> List[WifiNetwork]:
        """Fetches networks from the most recent scan session."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM scan_sessions ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            if not row:
                return []
            session_id = row["id"]
            cursor.execute("""
            SELECT * FROM wifi_networks WHERE session_id = ? ORDER BY signal_percent DESC
            """, (session_id,))
            rows = cursor.fetchall()
            return [
                WifiNetwork(
                    id=r["id"],
                    session_id=r["session_id"],
                    ssid=r["ssid"],
                    bssid=r["bssid"] or "",
                    signal_percent=r["signal_percent"],
                    channel=r["channel"] or 0,
                    frequency_band=r["frequency_band"] or "2.4 GHz",
                    security_type=r["security_type"] or "Unknown",
                    is_connected=bool(r["is_connected"]),
                    radio_type=r["radio_type"] or "",
                    observed_at=r["observed_at"]
                ) for r in rows
            ]

    def get_scan_sessions(self, limit: int = 50, location: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves past scan sessions."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM scan_sessions WHERE 1=1"
            params: List[Any] = []
            if location and location != "All Locations":
                query += " AND location_label = ?"
                params.append(location)
            query += " ORDER BY id DESC LIMIT ?"
            params.append(limit)
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    # --- Speed Tests ---

    def save_speed_test(self, result: SpeedTestResult) -> int:
        """Inserts a completed, failed, or cancelled speed test measurement."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO speed_tests (
                timestamp, download_mbps, upload_mbps, ping_ms, jitter_ms, duration_sec,
                server_name, network_ssid, location_label, status, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.timestamp, result.download_mbps, result.upload_mbps, result.ping_ms,
                result.jitter_ms, result.duration_sec, result.server_name, result.network_ssid,
                result.location_label, result.status, result.error_message
            ))
            conn.commit()
            return cursor.lastrowid

    def get_speed_tests(
        self,
        limit: int = 100,
        location: Optional[str] = None,
        network: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieves speed test records with optional filtering."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM speed_tests WHERE 1=1"
            params: List[Any] = []
            if location and location != "All Locations":
                query += " AND location_label = ?"
                params.append(location)
            if network:
                query += " AND network_ssid = ?"
                params.append(network)
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)
            if status:
                query += " AND status = ?"
                params.append(status)
            query += " ORDER BY id DESC LIMIT ?"
            params.append(limit)
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_speed_tests_by_locations(self, locations: List[str]) -> List[Dict[str, Any]]:
        """Retrieves all speed test records for specified locations without artificial limits."""
        if not locations:
            return []
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ",".join(["?"] * len(locations))
            query = f"SELECT * FROM speed_tests WHERE location_label IN ({placeholders}) ORDER BY id ASC"
            cursor.execute(query, locations)
            return [dict(row) for row in cursor.fetchall()]

    def get_latest_speed_test(self, network_ssid: Optional[str] = None) -> Optional[SpeedTestResult]:
        """Returns the most recent completed speed test result."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM speed_tests WHERE status = 'completed'"
            params: List[Any] = []
            if network_ssid:
                query += " AND network_ssid = ?"
                params.append(network_ssid)
            query += " ORDER BY id DESC LIMIT 1"
            cursor.execute(query, params)
            row = cursor.fetchone()
            if not row:
                return None
            return SpeedTestResult(
                id=row["id"],
                timestamp=row["timestamp"],
                download_mbps=row["download_mbps"],
                upload_mbps=row["upload_mbps"],
                ping_ms=row["ping_ms"],
                jitter_ms=row["jitter_ms"],
                duration_sec=row["duration_sec"],
                server_name=row["server_name"] or "",
                network_ssid=row["network_ssid"] or "",
                location_label=row["location_label"] or "Default",
                status=row["status"],
                error_message=row["error_message"] or ""
            )

    # --- Latency Tests ---

    def save_latency_test(self, result: LatencyTestResult) -> int:
        """Inserts a ping/latency test result."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO latency_tests (
                timestamp, target_host, ping_count, min_rtt_ms, max_rtt_ms, avg_rtt_ms,
                jitter_ms, packet_loss_percent, method, status, network_ssid, location_label
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.timestamp, result.target_host, result.ping_count, result.min_rtt_ms,
                result.max_rtt_ms, result.avg_rtt_ms, result.jitter_ms, result.packet_loss_percent,
                result.method, result.status, result.network_ssid, result.location_label
            ))
            conn.commit()
            return cursor.lastrowid

    def get_latency_tests(
        self,
        limit: int = 100,
        location: Optional[str] = None,
        network: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieves latency test records with optional filtering."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM latency_tests WHERE 1=1"
            params: List[Any] = []
            if location and location != "All Locations":
                query += " AND location_label = ?"
                params.append(location)
            if network:
                query += " AND network_ssid = ?"
                params.append(network)
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)
            query += " ORDER BY id DESC LIMIT ?"
            params.append(limit)
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_latency_tests_by_locations(self, locations: List[str]) -> List[Dict[str, Any]]:
        """Retrieves all latency test records for specified locations."""
        if not locations:
            return []
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ",".join(["?"] * len(locations))
            query = f"SELECT * FROM latency_tests WHERE location_label IN ({placeholders}) ORDER BY id ASC"
            cursor.execute(query, locations)
            return [dict(row) for row in cursor.fetchall()]

    def get_latest_latency_test(self, network_ssid: Optional[str] = None) -> Optional[LatencyTestResult]:
        """Returns the most recent latency test result."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM latency_tests"
            params: List[Any] = []
            if network_ssid:
                query += " WHERE network_ssid = ?"
                params.append(network_ssid)
            query += " ORDER BY id DESC LIMIT 1"
            cursor.execute(query, params)
            row = cursor.fetchone()
            if not row:
                return None
            return LatencyTestResult(
                id=row["id"],
                timestamp=row["timestamp"],
                target_host=row["target_host"],
                ping_count=row["ping_count"],
                min_rtt_ms=row["min_rtt_ms"],
                max_rtt_ms=row["max_rtt_ms"],
                avg_rtt_ms=row["avg_rtt_ms"],
                jitter_ms=row["jitter_ms"],
                packet_loss_percent=row["packet_loss_percent"],
                method=row["method"] if "method" in row.keys() else "ICMP",
                status=row["status"] if "status" in row.keys() else "completed",
                network_ssid=row["network_ssid"] or "",
                location_label=row["location_label"] or "Default"
            )

    # --- Signal Logs ---

    def save_signal_log(self, entry: SignalLogEntry) -> int:
        """Saves a continuous monitoring signal entry."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO signal_logs (
                timestamp, network_ssid, bssid, signal_percent, channel, frequency_band, location_label
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.timestamp, entry.network_ssid, entry.bssid, entry.signal_percent,
                entry.channel, entry.frequency_band, entry.location_label
            ))
            conn.commit()
            return cursor.lastrowid

    def get_signal_logs(
        self,
        limit: int = 200,
        network: Optional[str] = None,
        location: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieves signal log entries."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM signal_logs WHERE 1=1"
            params: List[Any] = []
            if network:
                query += " AND network_ssid = ?"
                params.append(network)
            if location and location != "All Locations":
                query += " AND location_label = ?"
                params.append(location)
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)
            query += " ORDER BY id DESC LIMIT ?"
            params.append(limit)
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_signal_logs_by_locations(self, locations: List[str]) -> List[Dict[str, Any]]:
        """Retrieves all signal log entries for specified locations."""
        if not locations:
            return []
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ",".join(["?"] * len(locations))
            query = f"SELECT * FROM signal_logs WHERE location_label IN ({placeholders}) ORDER BY id ASC"
            cursor.execute(query, locations)
            return [dict(row) for row in cursor.fetchall()]

    # --- Experiment Runs ---

    def save_experiment_run(self, run: ExperimentRun) -> int:
        """Saves a single run of a multi-trial experiment."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO experiment_runs (
                experiment_id, condition_label, run_number, timestamp, network_ssid,
                location_label, signal_percent, ping_ms, jitter_ms, packet_loss_percent,
                download_mbps, upload_mbps, target_host, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run.experiment_id, run.condition_label, run.run_number, run.timestamp,
                run.network_ssid, run.location_label, run.signal_percent, run.ping_ms,
                run.jitter_ms, run.packet_loss_percent, run.download_mbps, run.upload_mbps,
                run.target_host, run.status
            ))
            conn.commit()
            return cursor.lastrowid

    def get_experiment_runs(self, experiment_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves experiment runs filtered by experiment id if provided."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if experiment_id:
                cursor.execute(
                    "SELECT * FROM experiment_runs WHERE experiment_id = ? ORDER BY run_number ASC, id ASC",
                    (experiment_id,)
                )
            else:
                cursor.execute("SELECT * FROM experiment_runs ORDER BY id DESC LIMIT 500")
            return [dict(row) for row in cursor.fetchall()]

    def get_saved_experiments(self) -> List[Dict[str, Any]]:
        """Returns unique experiment sessions with summary counts."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT experiment_id, condition_label, location_label, network_ssid,
                   MIN(timestamp) as started_at,
                   COUNT(*) as trial_count,
                   AVG(download_mbps) as avg_download,
                   AVG(ping_ms) as avg_ping,
                   status
            FROM experiment_runs
            GROUP BY experiment_id
            ORDER BY MIN(timestamp) DESC
            LIMIT 50;
            """)
            return [dict(row) for row in cursor.fetchall()]

    # --- Locations & Settings ---

    def get_locations(self) -> List[str]:
        """Returns list of distinct saved location names."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM locations ORDER BY name ASC")
            return [row["name"] for row in cursor.fetchall()]

    def add_location(self, name: str, description: str = "") -> bool:
        """Adds a new custom location tag."""
        if not name or not name.strip():
            return False
        clean_name = name.strip()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO locations (name, created_at, description) VALUES (?, ?, ?)",
                (clean_name, datetime.now().isoformat(), description or f"User custom location: {clean_name}")
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_record(self, table_name: str, record_id: int) -> bool:
        """Safely deletes a record from a supported table."""
        allowed_tables = {
            "speed_tests", "latency_tests", "signal_logs",
            "scan_sessions", "experiment_runs", "locations"
        }
        if table_name not in allowed_tables:
            raise ValueError(f"Table '{table_name}' is not permitted for deletion.")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {table_name} WHERE id = ?", (record_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_setting(self, key: str, default: str = "") -> str:
        """Retrieves a persistent setting value."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        """Sets a persistent setting value."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now_iso = datetime.now().isoformat()
            cursor.execute("""
            INSERT INTO app_settings (key, value, updated_at) VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
            """, (key, str(value), now_iso))
            conn.commit()

    def get_all_settings(self) -> Dict[str, str]:
        """Returns all configured settings as a key-value dictionary."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM app_settings")
            return {row["key"]: row["value"] for row in cursor.fetchall()}
