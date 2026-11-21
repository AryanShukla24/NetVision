"""
Unit Tests for Telemetry Metric Calculations
Tests Jitter formulations (consecutive difference, RFC 3550),
Signal stability statistics, Channel-to-Band mappings,
Host validation, and Windows ping parsing.
"""

import pytest
from netvision.core.latency_monitor import (
    calculate_jitter,
    validate_target_host,
    parse_windows_ping_output
)
from netvision.core.signal_monitor import compute_signal_stability
from netvision.core.wifi_scanner import channel_to_band


def test_jitter_consecutive_difference():
    """Tests jitter calculation using mean consecutive RTT delta."""
    # Samples: 20ms, 25ms (diff 5), 23ms (diff 2), 30ms (diff 7)
    # Mean diff = (5 + 2 + 7) / 3 = 14 / 3 = 4.67
    rtts = [20.0, 25.0, 23.0, 30.0]
    jitter = calculate_jitter(rtts, method="consecutive_difference")
    assert jitter == 4.67


def test_jitter_rfc3550():
    """Tests jitter filter implementation of RFC 3550."""
    rtts = [20.0, 30.0, 20.0, 30.0]
    j = calculate_jitter(rtts, method="rfc3550")
    assert j is not None
    assert j > 0.0
    # Jitter on identical RTTs is 0.0
    assert calculate_jitter([20.0, 20.0, 20.0], method="rfc3550") == 0.0


def test_jitter_edge_cases():
    """Tests jitter behavior on empty or single-element lists: returns None (NULL)."""
    assert calculate_jitter([]) is None
    assert calculate_jitter([15.0]) is None


def test_target_host_validation():
    """Verifies that host validator accepts valid IPs and hostnames and rejects injection."""
    assert validate_target_host("8.8.8.8") == "8.8.8.8"
    assert validate_target_host("1.1.1.1") == "1.1.1.1"
    assert validate_target_host("google.com") == "google.com"
    assert validate_target_host("dns.google") == "dns.google"
    assert validate_target_host("localhost") == "localhost"

    # Reject command-line injection and invalid characters
    with pytest.raises(ValueError):
        validate_target_host("-n 5 8.8.8.8")
    with pytest.raises(ValueError):
        validate_target_host("8.8.8.8; ls")
    with pytest.raises(ValueError):
        validate_target_host("8.8.8.8 | dir")
    with pytest.raises(ValueError):
        validate_target_host("")
    with pytest.raises(ValueError):
        validate_target_host("   ")
    with pytest.raises(ValueError):
        validate_target_host("/test")


def test_parse_windows_ping_output():
    """Verifies Windows ping output parser across typical output formats."""
    # Standard reply
    out_normal = "Reply from 8.8.8.8: bytes=32 time=14ms TTL=117"
    assert parse_windows_ping_output(out_normal, 0) == 14.0

    # Sub-millisecond reply: time<1ms
    out_subms = "Reply from 127.0.0.1: bytes=32 time<1ms TTL=128"
    assert parse_windows_ping_output(out_subms, 0) == 0.5

    # Request timed out
    out_timeout = "Request timed out."
    assert parse_windows_ping_output(out_timeout, 1) is None

    # Destination host unreachable
    out_unreachable = "Reply from 192.168.1.1: Destination host unreachable."
    assert parse_windows_ping_output(out_unreachable, 1) is None

    # General failure
    out_gen_fail = "General failure."
    assert parse_windows_ping_output(out_gen_fail, 1) is None


def test_signal_stability_empty():
    """Tests stability calculation when no samples have been captured."""
    stats = compute_signal_stability([])
    assert stats["mean"] == 0.0
    assert stats["stability_label"] == "No Data"


def test_signal_stability_constant():
    """Tests stability calculation on constant signal values."""
    samples = [80, 80, 80, 80]
    stats = compute_signal_stability(samples)
    assert stats["mean"] == 80.0
    assert stats["std_dev"] == 0.0
    assert stats["stability_label"] == "Very Stable"
    assert stats["range"] == 0


def test_signal_stability_fluctuating():
    """Tests stability calculation with high signal swings."""
    samples = [20, 90, 30, 85, 25]
    stats = compute_signal_stability(samples)
    assert stats["std_dev"] > 7.0
    assert stats["stability_label"] == "Highly Unstable"
    assert stats["min"] == 20
    assert stats["max"] == 90
    assert stats["range"] == 70


def test_channel_to_band_mapping():
    """Tests 802.11 channel to frequency band mappings."""
    # 2.4 GHz channels 1 - 14
    assert channel_to_band(1) == "2.4 GHz"
    assert channel_to_band(6) == "2.4 GHz"
    assert channel_to_band(11) == "2.4 GHz"
    assert channel_to_band(14) == "2.4 GHz"

    # 5 GHz channels
    assert channel_to_band(36) == "5 GHz"
    assert channel_to_band(44) == "5 GHz"
    assert channel_to_band(149) == "5 GHz"
    assert channel_to_band(165) == "5 GHz"

    # 6 GHz (Wi-Fi 6E)
    assert channel_to_band(181) == "6 GHz"

    # Invalid channels
    assert channel_to_band(0) == "Unknown"
    assert channel_to_band(-5) == "Unknown"
