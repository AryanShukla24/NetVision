"""
Unit Tests for Rule-Based Network Recommendation Engine
Verifies that diagnostic findings are strictly evidence-backed.
"""

from netvision.core.recommendation_engine import RecommendationEngine
from netvision.database.models import ConnectedInterfaceInfo, SpeedTestResult, LatencyTestResult


def test_disconnected_recommendation():
    """Verifies that disconnected interface triggers critical advice."""
    info = ConnectedInterfaceInfo(state="disconnected")
    recs = RecommendationEngine.evaluate(interface_info=info)
    assert len(recs) == 1
    assert recs[0].severity == "Critical"
    assert "Disconnected" in recs[0].title


def test_weak_signal_recommendation():
    """Verifies critical advice for poor Wi-Fi signal (< 35%)."""
    info = ConnectedInterfaceInfo(
        state="connected",
        ssid="Home_Net",
        signal_percent=25,
        frequency_band="2.4 GHz"
    )
    recs = RecommendationEngine.evaluate(interface_info=info)
    sig_rec = next((r for r in recs if "Signal" in r.title), None)
    assert sig_rec is not None
    assert sig_rec.severity == "Critical"
    assert "25%" in sig_rec.evidence


def test_high_packet_loss_recommendation():
    """Verifies critical recommendation when packet loss exceeds threshold."""
    info = ConnectedInterfaceInfo(state="connected", ssid="Lab_WiFi", signal_percent=85)
    lat = LatencyTestResult(
        target_host="8.8.8.8",
        ping_count=20,
        min_rtt_ms=20,
        max_rtt_ms=40,
        avg_rtt_ms=25.0,
        jitter_ms=2.0,
        packet_loss_percent=15.0  # High loss
    )
    recs = RecommendationEngine.evaluate(interface_info=info, latency_result=lat)
    loss_rec = next((r for r in recs if "Packet Loss" in r.title), None)
    assert loss_rec is not None
    assert loss_rec.severity == "Critical"
    assert "15.0%" in loss_rec.evidence


def test_isp_bottleneck_detection():
    """Verifies diagnostic advice when Wi-Fi signal is strong but download is slow."""
    info = ConnectedInterfaceInfo(state="connected", ssid="Fast_WiFi", signal_percent=90)
    speed = SpeedTestResult(
        download_mbps=5.0,  # Slow
        upload_mbps=1.0,
        status="completed"
    )
    recs = RecommendationEngine.evaluate(interface_info=info, speed_result=speed)
    isp_rec = next((r for r in recs if "ISP or Gateway" in r.title), None)
    assert isp_rec is not None
    assert "5.0 Mbps" in isp_rec.evidence
