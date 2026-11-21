"""
NetVision - Latency and Jitter Monitor
Performs real ICMP ping probes via Windows ping utility or alternative TCP 3-way handshake probes.
Computes min/max/avg latency, RFC 3550 jitter / mean consecutive deviation, and packet loss percentage.
Never masks ICMP packet loss with TCP fallback.
Missing measurements are strictly preserved as None / NULL.
"""

import subprocess
import re
import time
import socket
import ipaddress
import logging
from typing import List, Optional, Callable, Dict, Any
from datetime import datetime

from netvision.database.models import LatencyTestResult
from netvision.core.subprocess_utils import run_hidden_command

logger = logging.getLogger(__name__)


def validate_target_host(host: str) -> str:
    """
    Validates target host string. Ensures it is a valid IPv4 address, IPv6 address,
    or standard RFC 1123 compliant hostname.
    Rejects strings beginning with '-' or containing shell metacharacters / option flags.
    """
    if not host or not isinstance(host, str):
        raise ValueError("Target host cannot be empty.")
    h = host.strip()
    if not h:
        raise ValueError("Target host cannot be empty.")
    if h.startswith("-") or h.startswith("/"):
        raise ValueError("Invalid target host: cannot begin with command-line option flags.")

    # Reject shell metacharacters
    if re.search(r"[ ;&|`$><\"'\t\r\n\\]", h):
        raise ValueError("Invalid characters in target host.")

    # Check if valid IP
    try:
        ipaddress.ip_address(h)
        return h
    except ValueError:
        pass

    # Validate RFC 1123 hostname
    if len(h) > 253:
        raise ValueError("Target hostname exceeds maximum length of 253 characters.")
    labels = h.split(".")
    for label in labels:
        if not label or len(label) > 63:
            raise ValueError("Hostname segments must be between 1 and 63 characters.")
        if not re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$", label):
            raise ValueError(f"Invalid characters in hostname label '{label}'.")
    return h


def calculate_jitter(rtts: List[float], method: str = "consecutive_difference") -> Optional[float]:
    """
    Computes jitter across a sequence of valid RTT (ms) samples.
    Returns None if fewer than 2 samples exist (jitter is statistical variation between samples).

    Method 1: 'consecutive_difference' (ITU-T recommendation / standard sample jitter):
      mean(|RTT_i - RTT_{i-1}|)

    Method 2: 'rfc3550' (RFC 3550 Section 6.4.1 smoothed interarrival jitter filter):
      J = J + (|D(i-1, i)| - J) / 16.0
      where D(i-1, i) = RTT_i - RTT_{i-1}
    """
    if not rtts or len(rtts) < 2:
        return None

    if method == "rfc3550":
        j = abs(rtts[1] - rtts[0])
        for i in range(2, len(rtts)):
            d = abs(rtts[i] - rtts[i - 1])
            j += (d - j) / 16.0
        return round(j, 2)
    else:
        diffs = [abs(rtts[i] - rtts[i - 1]) for i in range(1, len(rtts))]
        return round(sum(diffs) / len(diffs), 2)


def parse_windows_ping_output(output: str, returncode: int) -> Optional[float]:
    """
    Robustly parses Windows ping command output across locales.
    Returns RTT in ms, or None if probe timed out, failed, or was dropped.
    """
    if not output:
        return None

    # Check for packet loss / failure indicators
    failure_keywords = [
        "request timed out",
        "destination host unreachable",
        "general failure",
        "transmit failed",
        "could not find host",
        "destination net unreachable",
        "ttl expired in transit"
    ]
    out_lower = output.lower()
    for kw in failure_keywords:
        if kw in out_lower:
            return None

    # Sub-millisecond match: time<1ms, time < 1ms, or locale variants (temps<1ms, tiempo<1ms)
    if re.search(r"(?:time|temps|tiempo|zeit|tempo|durata)?\s*<\s*1\s*ms", out_lower):
        return 0.5  # Represent < 1ms as 0.5 ms (strictly positive sub-ms reply)

    # Standard match: time=14ms or time=14.2ms or time = 14ms
    match = re.search(r"(?:time|temps|tiempo|zeit|tempo|durata)?\s*[=:]\s*(\d+(?:\.\d+)?)\s*ms", out_lower)
    if match:
        try:
            val = float(match.group(1))
            return val
        except ValueError:
            pass

    # Generic digit before 'ms' in reply line
    reply_line = None
    for line in output.splitlines():
        ll = line.lower()
        if "reply from" in ll or "reponse de" in ll or "antwort von" in ll or "respuesta de" in ll:
            reply_line = ll
            break

    if reply_line:
        m = re.search(r"[=<:]\s*(\d+(?:\.\d+)?)\s*ms", reply_line)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                pass

    return None


class LatencyMonitor:
    """
    Executes ICMP echo probes or TCP 3-way handshake probes.
    Keeps measurement methods strictly isolated.
    """

    def __init__(self, target_host: str = "8.8.8.8", timeout_ms: int = 1500, method: str = "ICMP"):
        self.target_host = validate_target_host(target_host or "8.8.8.8")
        self.timeout_ms = max(200, min(10000, timeout_ms))
        self.method = "TCP_CONNECT" if method.upper() in ("TCP", "TCP_CONNECT") else "ICMP"
        self._is_running = False

    def probe_single(self) -> Optional[float]:
        """
        Executes a single probe using the configured method (ICMP or TCP_CONNECT).
        Returns RTT in ms, or None if lost/timed out.
        """
        if self.method == "TCP_CONNECT":
            return self._probe_tcp_connect()
        return self._probe_icmp()

    def _probe_icmp(self) -> Optional[float]:
        """Executes a single Windows ping probe without visible consoles or TCP fallback."""
        cmd = ["ping", "-n", "1", "-w", str(self.timeout_ms), self.target_host]
        try:
            res = run_hidden_command(
                cmd,
                timeout=(self.timeout_ms / 1000.0) + 1.5,
                check=False,
            )
            if res.returncode not in (0, 1) and res.stderr and res.stderr.strip():
                logger.warning(
                    "ICMP ping to %s returned %d: %s",
                    self.target_host,
                    res.returncode,
                    res.stderr.strip(),
                )
            return parse_windows_ping_output(res.stdout, res.returncode)
        except subprocess.TimeoutExpired:
            logger.warning("ICMP probe to %s timed out.", self.target_host)
            return None
        except FileNotFoundError:
            logger.error("Windows ping utility was not found on PATH.")
            return None
        except Exception as e:
            logger.error("ICMP probe exception for %s: %s", self.target_host, e)
            return None

    def _probe_tcp_connect(self) -> Optional[float]:
        """
        Measures round-trip time of a TCP 3-way handshake (SYN/ACK).
        Exposed strictly as an alternative measurement method when ICMP is blocked by policy.
        """
        ports = [53, 443, 80]
        timeout_sec = self.timeout_ms / 1000.0

        for port in ports:
            start = time.perf_counter()
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout_sec)
            try:
                s.connect((self.target_host, port))
                rtt = (time.perf_counter() - start) * 1000.0
                s.close()
                return round(rtt, 2)
            except (ConnectionRefusedError, socket.timeout):
                s.close()
                continue
            except Exception:
                s.close()
                continue
        return None

    def run_test(
        self,
        count: int = 10,
        interval_sec: float = 0.5,
        progress_callback: Optional[Callable[[int, int, Optional[float]], None]] = None,
        should_stop: Optional[Callable[[], bool]] = None,
        network_ssid: str = "",
        location_label: str = "Default",
        jitter_method: str = "consecutive_difference"
    ) -> LatencyTestResult:
        """
        Executes 'count' probes using the isolated measurement method,
        invokes progress_callback(step, total, rtt), and returns a LatencyTestResult DTO.
        """
        self._is_running = True
        rtt_list: List[float] = []
        sent = 0
        lost = 0
        cancelled = False

        for i in range(1, count + 1):
            if should_stop and should_stop():
                logger.info("Latency test cancelled by user.")
                cancelled = True
                break

            sent += 1
            rtt = self.probe_single()

            if rtt is not None:
                rtt_list.append(rtt)
            else:
                lost += 1

            if progress_callback:
                progress_callback(i, count, rtt)

            if i < count and not (should_stop and should_stop()):
                time.sleep(interval_sec)

        self._is_running = False

        packet_loss = round((lost / sent) * 100.0, 1) if sent > 0 else 100.0

        if rtt_list:
            min_rtt: Optional[float] = min(rtt_list)
            max_rtt: Optional[float] = max(rtt_list)
            avg_rtt: Optional[float] = round(sum(rtt_list) / len(rtt_list), 2)
            jitter: Optional[float] = calculate_jitter(rtt_list, method=jitter_method)
        else:
            # All probes lost: measurements are NULL, not 0.0
            min_rtt = None
            max_rtt = None
            avg_rtt = None
            jitter = None

        status = "cancelled" if cancelled else ("completed" if sent > 0 else "failed")

        return LatencyTestResult(
            target_host=self.target_host,
            ping_count=sent,
            min_rtt_ms=min_rtt,
            max_rtt_ms=max_rtt,
            avg_rtt_ms=avg_rtt,
            jitter_ms=jitter,
            packet_loss_percent=packet_loss,
            method=self.method,
            status=status,
            network_ssid=network_ssid,
            location_label=location_label,
            timestamp=datetime.now().isoformat()
        )
