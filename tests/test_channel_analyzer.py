"""
Unit Tests for Channel Analyzer and Spectrum Occupancy
Tests grouping networks across bands, 2.4 GHz overlap modeling, and empty scan handling.
"""

from netvision.core.channel_analyzer import ChannelAnalyzer, calculate_24ghz_overlap_weight
from netvision.database.models import WifiNetwork


def test_channel_analyzer_distribution():
    """Tests grouping networks across 2.4 GHz and 5 GHz bands and congestion scoring."""
    sample_nets = [
        # Channel 6 crowded (3 APs)
        WifiNetwork(ssid="Net1", channel=6, signal_percent=80, frequency_band="2.4 GHz"),
        WifiNetwork(ssid="Net2", channel=6, signal_percent=75, frequency_band="2.4 GHz"),
        WifiNetwork(ssid="Net3", channel=6, signal_percent=60, frequency_band="2.4 GHz"),
        # Channel 1 clear (0 APs)
        # Channel 11 (1 AP)
        WifiNetwork(ssid="Net4", channel=11, signal_percent=50, frequency_band="2.4 GHz"),
        # 5 GHz channel 36 (1 AP)
        WifiNetwork(ssid="Net5", channel=36, signal_percent=85, frequency_band="5 GHz"),
    ]

    analysis = ChannelAnalyzer.analyze_channels(sample_nets)
    assert analysis["total_networks"] == 5
    assert analysis["has_data"] is True

    band_24 = analysis["band_24"]
    # Channel 1 has 0 APs and 0 overlap, so Channel 1 should be recommended!
    assert band_24["recommended_channel"] == 1
    assert band_24["recommended_score"] == 0.0

    # Channel 6 should be marked Moderate or Heavy congestion
    ch6_info = next((c for c in band_24["channels"] if c["channel"] == 6), None)
    assert ch6_info is not None
    assert ch6_info["count"] == 3
    assert ch6_info["congestion"] in ["Moderate", "Heavy"]


def test_channel_analyzer_empty_scan():
    """Verifies that no recommendation is fabricated when scan data is empty."""
    analysis = ChannelAnalyzer.analyze_channels([])
    assert analysis["has_data"] is False
    assert analysis["total_networks"] == 0
    assert analysis["band_24"]["recommended_channel"] is None
    assert analysis["band_5"]["recommended_channel"] is None
    assert "No wireless" in analysis["band_24"]["reasoning"]


def test_24ghz_overlap_weights():
    """Verifies 2.4 GHz 20 MHz channel overlap weighting function."""
    # Co-channel
    assert calculate_24ghz_overlap_weight(1, 1) == 1.0
    assert calculate_24ghz_overlap_weight(6, 6) == 1.0

    # Adjacent channels
    assert calculate_24ghz_overlap_weight(2, 1) == 0.75
    assert calculate_24ghz_overlap_weight(3, 1) == 0.50
    assert calculate_24ghz_overlap_weight(4, 1) == 0.25

    # Non-overlapping (>= 4 channels away)
    assert calculate_24ghz_overlap_weight(5, 1) == 0.0
    assert calculate_24ghz_overlap_weight(6, 1) == 0.0
    assert calculate_24ghz_overlap_weight(11, 1) == 0.0
