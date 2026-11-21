"""
NetVision - Network Speed Tester
Measures genuine WAN download and upload throughput, TCP edge ping, and genuine jitter.
Uses direct chunked streaming with Cloudflare's Global Edge infrastructure.
Excludes TCP/TLS connection setup from throughput timing.
Provides fully cancellable downloads and uploads, total test timeouts,
and honest NULL handling for failed or incomplete metrics.
"""

import time
import socket
import logging
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from netvision.database.models import SpeedTestResult
from netvision.core.latency_monitor import calculate_jitter

logger = logging.getLogger(__name__)

DEFAULT_SERVER_NAME = "Cloudflare Global Edge (Anycast CDN)"
SERVER_HOST = "speed.cloudflare.com"
DOWN_BASE_URL = f"https://{SERVER_HOST}/__down?bytes="
UP_URL = f"https://{SERVER_HOST}/__up"


class CloudflareSpeedEngine:
    """
    Direct CDN speed test engine querying Cloudflare's global edge speed test service.
    Implements true chunked streaming, warm-up exclusion, and cancellable transfers.
    """

    @classmethod
    def measure_edge_latency_and_jitter(
        cls,
        samples_count: int = 5,
        timeout_sec: float = 2.5,
        should_stop: Optional[Callable[[], bool]] = None
    ) -> Dict[str, Optional[float]]:
        """
        Measures real TCP 3-way handshake round-trip time (RTT) to the edge server.
        Uses multiple samples to calculate genuine ping and genuine jitter.
        Does NOT confuse HTTP request duration with ping.
        """
        rtts: List[float] = []
        for _ in range(samples_count):
            if should_stop and should_stop():
                break
            start = time.perf_counter()
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(timeout_sec)
                s.connect((SERVER_HOST, 443))
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                s.close()
                rtts.append(round(elapsed_ms, 2))
            except Exception as e:
                logger.debug(f"Edge RTT probe failed: {e}")
            time.sleep(0.08)

        if not rtts:
            return {"ping_ms": None, "jitter_ms": None}

        ping_val = round(sum(rtts) / len(rtts), 1)
        jitter_val = calculate_jitter(rtts, method="consecutive_difference")
        return {"ping_ms": ping_val, "jitter_ms": jitter_val}

    @classmethod
    def measure_download(
        cls,
        target_bytes: int = 10_000_000,
        progress_cb: Optional[Callable[[float, float], None]] = None,
        should_stop: Optional[Callable[[], bool]] = None,
        total_timeout: float = 20.0
    ) -> float:
        """
        Downloads data in chunks. Performs a warm-up phase (1 MB) to establish
        TCP window scaling, then measures steady-state throughput.
        Periodically checks should_stop() for cancellation.
        """
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NetVision/1.0"})

        # Step 1: Warm-up phase (1 MB tier) to avoid TCP slow-start penalizing measurement
        try:
            warmup_url = f"{DOWN_BASE_URL}1000000"
            with session.get(warmup_url, stream=True, timeout=5.0) as resp:
                resp.raise_for_status()
                for _ in resp.iter_content(chunk_size=32768):
                    if should_stop and should_stop():
                        raise InterruptedError("Cancelled during warm-up")
        except InterruptedError:
            raise
        except Exception as e:
            logger.warning(f"Download warm-up note: {e}")

        if should_stop and should_stop():
            raise InterruptedError("Download cancelled by user")

        # Step 2: Main measurement transfer
        main_url = f"{DOWN_BASE_URL}{target_bytes}"
        total_read = 0
        chunk_size = 65536
        overall_start = time.perf_counter()
        transfer_start = time.perf_counter()

        try:
            with session.get(main_url, stream=True, timeout=total_timeout) as resp:
                resp.raise_for_status()
                transfer_start = time.perf_counter()

                for chunk in resp.iter_content(chunk_size=chunk_size):
                    if should_stop and should_stop():
                        raise InterruptedError("Download cancelled by user")

                    # Check total timeout
                    if (time.perf_counter() - overall_start) > total_timeout:
                        logger.warning("Download hit maximum test duration timeout.")
                        break

                    if not chunk:
                        break

                    total_read += len(chunk)
                    elapsed = time.perf_counter() - transfer_start

                    if elapsed > 0.05 and progress_cb:
                        instant_mbps = (total_read * 8.0) / (elapsed * 1_000_000.0)
                        pct = min(100.0, (total_read / target_bytes) * 100.0)
                        progress_cb(pct, round(instant_mbps, 2))

            total_elapsed = time.perf_counter() - transfer_start
            if total_elapsed <= 0.001 or total_read == 0:
                return 0.0

            mbps = (total_read * 8.0) / (total_elapsed * 1_000_000.0)
            return round(mbps, 2)

        except requests.exceptions.HTTPError as e:
            logger.error(f"Download HTTP error: {e}")
            raise
        except requests.exceptions.Timeout:
            logger.error("Download timed out.")
            raise
        except InterruptedError:
            raise
        except Exception as e:
            logger.error(f"Download failed: {e}")
            raise

    @classmethod
    def measure_upload(
        cls,
        target_bytes: int = 5_000_000,
        progress_cb: Optional[Callable[[float, float], None]] = None,
        should_stop: Optional[Callable[[], bool]] = None,
        total_timeout: float = 20.0
    ) -> float:
        """
        Streams binary data via HTTP POST using a chunk generator.
        Checks cancellation continuously on every 64KB chunk.
        """
        session = requests.Session()
        chunk_size = 65536
        test_payload_chunk = b"N" * chunk_size
        bytes_sent = 0
        transfer_start = 0.0

        def chunk_stream():
            nonlocal bytes_sent, transfer_start
            sent = 0
            transfer_start = time.perf_counter()

            while sent < target_bytes:
                if should_stop and should_stop():
                    raise InterruptedError("Upload cancelled by user")

                if (time.perf_counter() - transfer_start) > total_timeout:
                    logger.warning("Upload hit total timeout.")
                    break

                to_send = min(chunk_size, target_bytes - sent)
                payload = test_payload_chunk[:to_send]
                yield payload

                sent += to_send
                bytes_sent = sent
                elapsed = time.perf_counter() - transfer_start

                if elapsed > 0.05 and progress_cb:
                    instant_mbps = (sent * 8.0) / (elapsed * 1_000_000.0)
                    pct = min(100.0, (sent / target_bytes) * 100.0)
                    progress_cb(pct, round(instant_mbps, 2))

        try:
            resp = session.post(
                UP_URL,
                data=chunk_stream(),
                headers={
                    "Content-Type": "application/octet-stream",
                    "User-Agent": "NetVision/1.0"
                },
                timeout=total_timeout
            )
            resp.raise_for_status()

            total_elapsed = time.perf_counter() - transfer_start
            if total_elapsed <= 0.001 or bytes_sent == 0:
                return 0.0

            mbps = (bytes_sent * 8.0) / (total_elapsed * 1_000_000.0)
            return round(mbps, 2)

        except InterruptedError:
            raise
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            raise


class SpeedTester:
    """Orchestrates download, upload, ping, and jitter tests with real-time UI callbacks."""

    def __init__(self):
        self._abort = False

    def abort(self) -> None:
        """Signals current running speed test to cancel."""
        self._abort = True

    def run_speed_test(
        self,
        progress_callback: Optional[Callable[[str, float, float], None]] = None,
        # callback args: (phase_name, percent_complete, current_speed_mbps)
        network_ssid: str = "",
        location_label: str = "Default"
    ) -> SpeedTestResult:
        """
        Runs complete speed test suite against verified CDN edge infrastructure.
        Returns a populated SpeedTestResult DTO.
        """
        self._abort = False
        start_wall_time = time.perf_counter()
        timestamp_now = datetime.now().isoformat()
        server_name = DEFAULT_SERVER_NAME

        ping_val: Optional[float] = None
        jitter_val: Optional[float] = None
        down_mbps: Optional[float] = None
        up_mbps: Optional[float] = None

        try:
            # Phase 1: Real TCP Edge Latency & Jitter Probing
            if progress_callback:
                progress_callback("Connecting to CDN edge server & measuring latency...", 10.0, 0.0)

            lat_metrics = CloudflareSpeedEngine.measure_edge_latency_and_jitter(
                samples_count=5,
                should_stop=lambda: self._abort
            )
            ping_val = lat_metrics["ping_ms"]
            jitter_val = lat_metrics["jitter_ms"]

            if self._abort:
                raise InterruptedError("Test cancelled by user")

            # Phase 2: Steady-state Download Test
            if progress_callback:
                progress_callback("Testing Download Speed...", 20.0, 0.0)

            def down_cb(pct: float, current_mbps: float):
                overall_pct = 20.0 + (pct * 0.45)  # Maps 0-100% to 20-65%
                if progress_callback:
                    progress_callback("Testing Download Speed...", overall_pct, current_mbps)

            down_mbps = CloudflareSpeedEngine.measure_download(
                target_bytes=10_000_000,
                progress_cb=down_cb,
                should_stop=lambda: self._abort
            )

            if self._abort:
                raise InterruptedError("Test cancelled by user")

            # Phase 3: Cancellable Chunked Upload Test
            if progress_callback:
                progress_callback("Testing Upload Speed...", 65.0, 0.0)

            def up_cb(pct: float, current_mbps: float):
                overall_pct = 65.0 + (pct * 0.35)  # Maps 0-100% to 65-100%
                if progress_callback:
                    progress_callback("Testing Upload Speed...", overall_pct, current_mbps)

            up_mbps = CloudflareSpeedEngine.measure_upload(
                target_bytes=5_000_000,
                progress_cb=up_cb,
                should_stop=lambda: self._abort
            )

            duration = round(time.perf_counter() - start_wall_time, 2)
            if progress_callback:
                progress_callback("Test Complete", 100.0, down_mbps or 0.0)

            return SpeedTestResult(
                download_mbps=down_mbps,
                upload_mbps=up_mbps,
                ping_ms=ping_val,
                jitter_ms=jitter_val,
                duration_sec=duration,
                server_name=server_name,
                network_ssid=network_ssid,
                location_label=location_label,
                timestamp=timestamp_now,
                status="completed"
            )

        except InterruptedError:
            duration = round(time.perf_counter() - start_wall_time, 2)
            return SpeedTestResult(
                download_mbps=down_mbps,
                upload_mbps=up_mbps,
                ping_ms=ping_val,
                jitter_ms=jitter_val,
                duration_sec=duration,
                server_name=server_name,
                network_ssid=network_ssid,
                location_label=location_label,
                timestamp=timestamp_now,
                status="cancelled",
                error_message="Test was stopped by the user."
            )

        except Exception as e:
            logger.exception("Speed test failed")
            duration = round(time.perf_counter() - start_wall_time, 2)
            return SpeedTestResult(
                download_mbps=None,
                upload_mbps=None,
                ping_ms=ping_val,
                jitter_ms=jitter_val,
                duration_sec=duration,
                server_name=server_name,
                network_ssid=network_ssid,
                location_label=location_label,
                timestamp=timestamp_now,
                status="failed",
                error_message=f"Network error: {str(e)}"
            )
