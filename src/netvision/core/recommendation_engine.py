"""
NetVision - Rule-Based Network Recommendation Engine
Generates transparent, evidence-backed diagnostic suggestions from actual collected metrics.
Uses centralized configurable thresholds and avoids mixing data from unrelated networks.
Discloses when insufficient information exists.
"""

from typing import List, Dict, Any, Optional
from netvision.config import DEFAULT_THRESHOLDS
from netvision.database.models import ConnectedInterfaceInfo, SpeedTestResult, LatencyTestResult, get_signal_category


class Recommendation:
    """Represents a single diagnostic recommendation."""
    def __init__(self, title: str, category: str, severity: str, evidence: str, advice: str):
        self.title = title
        self.category = category       # "Wi-Fi RF", "Internet Throughput", "Latency/Gaming", "Configuration"
        self.severity = severity       # "Critical", "Warning", "Good", "Tip", "Info"
        self.evidence = evidence       # The measured value supporting this advice
        self.advice = advice           # Actionable step for the user

    def to_dict(self) -> Dict[str, str]:
        return {
            "title": self.title,
            "category": self.category,
            "severity": self.severity,
            "evidence": self.evidence,
            "advice": self.advice
        }


class RecommendationEngine:
    """Evaluates telemetry data against network engineering best practices using centralized thresholds."""

    @classmethod
    def evaluate(
        cls,
        interface_info: Optional[ConnectedInterfaceInfo] = None,
        speed_result: Optional[SpeedTestResult] = None,
        latency_result: Optional[LatencyTestResult] = None,
        channel_analysis: Optional[Dict[str, Any]] = None,
        thresholds: Optional[Dict[str, Any]] = None
    ) -> List[Recommendation]:
        """Runs the rule evaluation matrix against available measurements."""
        recs: List[Recommendation] = []
        th = thresholds or DEFAULT_THRESHOLDS

        sig_th = th.get("signal", DEFAULT_THRESHOLDS["signal"])
        lat_th = th.get("latency", DEFAULT_THRESHOLDS["latency"])
        loss_th = th.get("packet_loss", DEFAULT_THRESHOLDS["packet_loss"])
        speed_th = th.get("download_speed", DEFAULT_THRESHOLDS["download_speed"])

        # 1. Connection State
        if not interface_info or interface_info.state != "connected":
            recs.append(Recommendation(
                title="Wi-Fi Disconnected",
                category="Configuration",
                severity="Critical",
                evidence="Wi-Fi interface state is 'disconnected'",
                advice="Ensure your Wi-Fi adapter is turned on and connect to an available network."
            ))
            return recs

        # 2. Signal Strength Evaluation (Uses centralized threshold)
        sig = interface_info.signal_percent
        if sig is None or sig <= 0:
            recs.append(Recommendation(
                title="No Wi-Fi Signal",
                category="Wi-Fi RF",
                severity="Critical",
                evidence="Signal percentage is 0% or unavailable",
                advice="Check that the wireless access point is powered on and within broadcast range."
            ))
        elif sig < sig_th.get("fair", 30):
            recs.append(Recommendation(
                title="Critically Weak Wi-Fi Signal",
                category="Wi-Fi RF",
                severity="Critical",
                evidence=f"Current signal strength is {sig}% (Poor, threshold < {sig_th.get('fair', 30)}%)",
                advice="Move closer to the wireless access point or remove physical barriers (thick walls, metal structures)."
            ))
        elif sig < sig_th.get("good", 50):
            recs.append(Recommendation(
                title="Moderate Wi-Fi Signal Attenuation",
                category="Wi-Fi RF",
                severity="Warning",
                evidence=f"Current signal strength is {sig}% (Fair, threshold < {sig_th.get('good', 50)}%)",
                advice="You may experience occasional frame retransmissions or reduced throughput. Consider relocating closer to the AP."
            ))
        else:
            cat = "Excellent" if sig >= sig_th.get("excellent", 75) else "Good"
            recs.append(Recommendation(
                title="Strong Wi-Fi Radio Link",
                category="Wi-Fi RF",
                severity="Good",
                evidence=f"Current signal strength is {sig}% ({cat})",
                advice="Physical signal reception is strong and adequate for high-bandwidth tasks."
            ))

        # 3. Frequency Band Check (2.4 GHz vs 5 GHz vs 6 GHz)
        if interface_info.frequency_band == "2.4 GHz":
            recs.append(Recommendation(
                title="Connected on 2.4 GHz Frequency Band",
                category="Wi-Fi RF",
                severity="Tip",
                evidence="Active connection is using 2.4 GHz band",
                advice="2.4 GHz penetrates solid obstacles better but has limited bandwidth and high contention. If your router supports a 5 GHz SSID, connect to it for higher throughput."
            ))
        elif interface_info.frequency_band == "5 GHz":
            recs.append(Recommendation(
                title="Connected on 5 GHz Frequency Band",
                category="Wi-Fi RF",
                severity="Good",
                evidence="Active connection is using 5 GHz band",
                advice="5 GHz band provides wider channels and lower co-channel congestion compared to 2.4 GHz."
            ))

        # 4. Latency and Packet Loss Evaluation
        if latency_result and latency_result.status == "completed":
            avg_lat = latency_result.avg_rtt_ms
            loss = latency_result.packet_loss_percent
            jitter = latency_result.jitter_ms

            if loss > loss_th.get("poor", 5.0):
                recs.append(Recommendation(
                    title="High Packet Loss Detected",
                    category="Latency/Gaming",
                    severity="Critical",
                    evidence=f"Packet loss is {loss:.1f}% to {latency_result.target_host}",
                    advice="Unanswered probes indicate packet drops. Check for heavy background torrents, router queue overflow, or local RF interference."
                ))
            elif loss > loss_th.get("good", 1.0):
                recs.append(Recommendation(
                    title="Intermittent Packet Loss",
                    category="Latency/Gaming",
                    severity="Warning",
                    evidence=f"Packet loss is {loss:.1f}% to {latency_result.target_host}",
                    advice="A small percentage of packets were dropped. Real-time VoIP or online multiplayer gaming may experience micro-stutters."
                ))

            if avg_lat is not None:
                if avg_lat > lat_th.get("fair", 100.0):
                    recs.append(Recommendation(
                        title="High Round-Trip Latency",
                        category="Latency/Gaming",
                        severity="Warning",
                        evidence=f"Average ping is {avg_lat:.1f} ms (threshold > {lat_th.get('fair', 100)} ms)",
                        advice="High ping affects responsive interactive applications. Check if distant servers are being queried or if local link is congested."
                    ))
                elif avg_lat <= lat_th.get("excellent", 30.0):
                    recs.append(Recommendation(
                        title="Low Latency Performance",
                        category="Latency/Gaming",
                        severity="Good",
                        evidence=f"Average ping is {avg_lat:.1f} ms to {latency_result.target_host}",
                        advice="Round-trip latency is excellent for cloud gaming, VoIP, and video calls."
                    ))

            if jitter is not None and jitter > 15.0:
                recs.append(Recommendation(
                    title="Elevated Network Jitter",
                    category="Latency/Gaming",
                    severity="Warning",
                    evidence=f"Jitter is {jitter:.1f} ms",
                    advice="High delay variation indicates bufferbloat or fluctuating channel contention."
                ))
        else:
            recs.append(Recommendation(
                title="Latency Unmeasured for Active Link",
                category="Latency/Gaming",
                severity="Info",
                evidence="No completed latency test recorded for current session",
                advice="Execute a latency test in the Latency Monitor tab to assess ping and packet loss."
            ))

        # 5. Throughput & ISP Bottleneck Evaluation
        if speed_result and speed_result.status == "completed" and speed_result.download_mbps is not None:
            down = speed_result.download_mbps
            up = speed_result.upload_mbps or 0.0

            # ISP Bottleneck: Strong RF signal but low WAN download speed
            if sig >= 75 and down < speed_th.get("fair", 10.0):
                recs.append(Recommendation(
                    title="Potential ISP or Gateway Bottleneck",
                    category="Internet Throughput",
                    severity="Warning",
                    evidence=f"Wi-Fi signal is strong ({sig}%), but download speed is only {down:.1f} Mbps",
                    advice="Your local wireless link to the router is optimal, but external WAN download throughput is restricted. Check router WAN cable, ISP bandwidth tier, or active background downloads."
                ))
            elif down >= speed_th.get("excellent", 50.0):
                recs.append(Recommendation(
                    title="High-Speed Internet Throughput",
                    category="Internet Throughput",
                    severity="Good",
                    evidence=f"Measured download speed is {down:.1f} Mbps",
                    advice="Bandwidth is sufficient for 4K streaming, large file transfers, and concurrent multi-device usage."
                ))
            elif down < speed_th.get("fair", 10.0):
                recs.append(Recommendation(
                    title="Constrained Download Bandwidth",
                    category="Internet Throughput",
                    severity="Warning",
                    evidence=f"Measured download speed is {down:.1f} Mbps (threshold < {speed_th.get('fair', 10.0)} Mbps)",
                    advice="Bandwidth may feel sluggish for streaming or multi-user access."
                ))
        else:
            recs.append(Recommendation(
                title="Throughput Unmeasured for Active Link",
                category="Internet Throughput",
                severity="Info",
                evidence="No completed speed test recorded for current session",
                advice="Execute a speed test in the Speed Test tab to verify download and upload throughput."
            ))

        # 6. Channel Congestion Optimization
        if channel_analysis and channel_analysis.get("has_data"):
            rec_ch = channel_analysis.get("recommendation_24")
            if interface_info.channel > 0 and rec_ch and interface_info.channel != rec_ch and interface_info.frequency_band == "2.4 GHz":
                recs.append(Recommendation(
                    title="Suboptimal 2.4 GHz Channel Configuration",
                    category="Wi-Fi RF",
                    severity="Tip",
                    evidence=f"Connected on channel {interface_info.channel}, but channel {rec_ch} has less spectral overlap in this environment",
                    advice=f"Consider logging into your router's administration portal and changing the 2.4 GHz channel to Channel {rec_ch}."
                ))

        return recs
