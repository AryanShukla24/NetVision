"""
NetVision - Wi-Fi Channel Analyzer
Analyzes detected access point channel occupancy and RF crowding estimates.
Implements a documented 2.4 GHz spectral overlap model (ITU/IEEE 802.11 20 MHz spectral masks).
Separates 2.4 GHz, 5 GHz, and 6 GHz bands.
Never generates recommendations when no scan data is present.
Explicitly labels congestion scores as AP-based estimates and discloses lack of RF physical spectrum hardware.
"""

from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
from netvision.database.models import WifiNetwork

# Standard non-overlapping channels in 2.4 GHz band
STANDARD_24GHZ_CHANNELS = [1, 6, 11]

# Common standard 20 MHz channels in 5 GHz band (UNII-1, UNII-2, UNII-3)
STANDARD_5GHZ_CHANNELS = [36, 40, 44, 48, 149, 153, 157, 161]


def calculate_24ghz_overlap_weight(ap_channel: int, target_channel: int) -> float:
    """
    Computes spectral overlap weight between an access point's channel and target channel.
    Standard 802.11b/g/n channels are 20 MHz wide with 5 MHz channel spacing.
    - Delta = 0: Co-channel interference (weight 1.0)
    - Delta = 1 (5 MHz overlap): High overlap (weight 0.75)
    - Delta = 2 (10 MHz overlap): Medium overlap (weight 0.50)
    - Delta = 3 (15 MHz overlap): Slight overlap (weight 0.25)
    - Delta >= 4 (>= 20 MHz): Non-overlapping (weight 0.0)
    """
    delta = abs(ap_channel - target_channel)
    if delta == 0:
        return 1.0
    elif delta == 1:
        return 0.75
    elif delta == 2:
        return 0.50
    elif delta == 3:
        return 0.25
    return 0.0


class ChannelAnalyzer:
    """
    Analyzes nearby access points per channel and band, applies spectral overlap modeling,
    and produces honest, evidence-based recommendations.
    """

    @classmethod
    def analyze_channels(cls, networks: List[WifiNetwork]) -> Dict[str, Any]:
        """
        Processes discovered networks.
        Returns complete analysis dictionary. If networks is empty, indicates no data.
        """
        if not networks:
            return {
                "has_data": False,
                "total_networks": 0,
                "band_24": {
                    "band_name": "2.4 GHz",
                    "channels": [],
                    "recommended_channel": None,
                    "recommended_score": None,
                    "reasoning": "No wireless access points detected or no scan has been performed yet."
                },
                "band_5": {
                    "band_name": "5 GHz",
                    "channels": [],
                    "recommended_channel": None,
                    "recommended_score": None,
                    "reasoning": "No 5 GHz wireless networks detected in scan."
                },
                "band_6": {
                    "band_name": "6 GHz",
                    "channels": [],
                    "recommended_channel": None,
                    "reasoning": "No 6 GHz (Wi-Fi 6E) networks detected."
                },
                "recommendation_24": None,
                "recommendation_5": None,
                "disclaimer": (
                    "Estimates are calculated from beacon frames of nearby detected access points. "
                    "Consumer Wi-Fi cards cannot measure non-802.11 RF noise, microwave interference, "
                    "or exact airtime duty cycles without specialized RF spectrum analyzer hardware."
                )
            }

        ch_24: List[WifiNetwork] = []
        ch_5: List[WifiNetwork] = []
        ch_6: List[WifiNetwork] = []

        for net in networks:
            if net.channel <= 0:
                continue

            # Identify band rigorously
            if net.frequency_band == "6 GHz":
                ch_6.append(net)
            elif net.frequency_band == "5 GHz" or (32 <= net.channel <= 177):
                ch_5.append(net)
            elif net.frequency_band == "2.4 GHz" or (1 <= net.channel <= 14):
                ch_24.append(net)

        summary_24 = cls._analyze_24ghz_band(ch_24)
        summary_5 = cls._analyze_5ghz_band(ch_5)
        summary_6 = cls._analyze_6ghz_band(ch_6)

        return {
            "has_data": True,
            "total_networks": len(networks),
            "band_24": summary_24,
            "band_5": summary_5,
            "band_6": summary_6,
            "recommendation_24": summary_24.get("recommended_channel"),
            "recommendation_5": summary_5.get("recommended_channel"),
            "disclaimer": (
                "Estimates are calculated from beacon frames of nearby detected access points. "
                "Consumer Wi-Fi cards cannot measure non-802.11 RF noise, microwave interference, "
                "or exact airtime duty cycles without specialized RF spectrum analyzer hardware."
            )
        }

    @classmethod
    def _analyze_24ghz_band(cls, networks: List[WifiNetwork]) -> Dict[str, Any]:
        """Analyzes 2.4 GHz band applying adjacent-channel overlap weights."""
        if not networks:
            return {
                "band_name": "2.4 GHz",
                "channels": [],
                "recommended_channel": None,
                "recommended_score": None,
                "reasoning": "No 2.4 GHz networks detected in range."
            }

        ap_map: Dict[int, List[WifiNetwork]] = defaultdict(list)
        for net in networks:
            ap_map[net.channel].append(net)

        # Include standard channels and any active detected channels
        all_channels = sorted(set(STANDARD_24GHZ_CHANNELS + list(ap_map.keys())))
        channel_data = []

        for ch in all_channels:
            nets = ap_map.get(ch, [])
            count = len(nets)
            avg_sig = (sum(n.signal_percent for n in nets) / count) if count > 0 else 0.0

            # Calculate congestion score including direct AP count and signal weight
            co_channel_score = sum(1.0 + (n.signal_percent / 100.0) for n in nets)

            if count == 0:
                congestion = "Clear"
            elif count <= 2:
                congestion = "Low"
            elif count <= 4:
                congestion = "Moderate"
            else:
                congestion = "Heavy"

            channel_data.append({
                "channel": ch,
                "count": count,
                "networks": [n.ssid for n in nets],
                "avg_signal": round(avg_sig, 1),
                "congestion": congestion,
                "co_channel_score": round(co_channel_score, 2)
            })

        # Calculate overlap-aware recommendation for standard channels [1, 6, 11]
        best_channel = None
        min_overlap_score = float("inf")

        for cand in STANDARD_24GHZ_CHANNELS:
            score = 0.0
            for net in networks:
                w = calculate_24ghz_overlap_weight(net.channel, cand)
                if w > 0:
                    score += w * (1.0 + (net.signal_percent / 100.0))
            if score < min_overlap_score:
                min_overlap_score = score
                best_channel = cand

        direct_count = len(ap_map.get(best_channel, []))
        reasoning = (
            f"Channel {best_channel} is recommended as having the lowest cumulative "
            f"co-channel and adjacent-channel overlap score ({min_overlap_score:.1f}, {direct_count} direct APs) "
            f"among the non-overlapping 2.4 GHz channels (1, 6, 11)."
        )

        return {
            "band_name": "2.4 GHz",
            "channels": channel_data,
            "recommended_channel": best_channel,
            "recommended_score": round(min_overlap_score, 2),
            "reasoning": reasoning
        }

    @classmethod
    def _analyze_5ghz_band(cls, networks: List[WifiNetwork]) -> Dict[str, Any]:
        """Analyzes 5 GHz band channels (no adjacent 20 MHz overlap)."""
        if not networks:
            return {
                "band_name": "5 GHz",
                "channels": [],
                "recommended_channel": None,
                "recommended_score": None,
                "reasoning": "No 5 GHz networks detected in range."
            }

        ap_map: Dict[int, List[WifiNetwork]] = defaultdict(list)
        for net in networks:
            ap_map[net.channel].append(net)

        all_channels = sorted(set(STANDARD_5GHZ_CHANNELS + list(ap_map.keys())))
        channel_data = []

        for ch in all_channels:
            nets = ap_map.get(ch, [])
            count = len(nets)
            avg_sig = (sum(n.signal_percent for n in nets) / count) if count > 0 else 0.0

            if count == 0:
                congestion = "Clear"
            elif count <= 2:
                congestion = "Low"
            elif count <= 4:
                congestion = "Moderate"
            else:
                congestion = "Heavy"

            channel_data.append({
                "channel": ch,
                "count": count,
                "networks": [n.ssid for n in nets],
                "avg_signal": round(avg_sig, 1),
                "congestion": congestion
            })

        # Best channel among standard 5 GHz channels
        best_channel = None
        min_count = float("inf")
        for cand in STANDARD_5GHZ_CHANNELS:
            c = len(ap_map.get(cand, []))
            if c < min_count:
                min_count = c
                best_channel = cand

        reasoning = (
            f"Channel {best_channel} currently has the fewest competing access points ({min_count} APs) "
            f"among standard 5 GHz channels. 5 GHz offers significantly higher channel capacity."
        )

        return {
            "band_name": "5 GHz",
            "channels": channel_data,
            "recommended_channel": best_channel,
            "recommended_load": min_count,
            "reasoning": reasoning
        }

    @classmethod
    def _analyze_6ghz_band(cls, networks: List[WifiNetwork]) -> Dict[str, Any]:
        """Analyzes 6 GHz Wi-Fi 6E channels when identifiable."""
        if not networks:
            return {
                "band_name": "6 GHz",
                "channels": [],
                "recommended_channel": None,
                "reasoning": "No 6 GHz (Wi-Fi 6E) networks detected."
            }

        ap_map: Dict[int, List[WifiNetwork]] = defaultdict(list)
        for net in networks:
            ap_map[net.channel].append(net)

        channel_data = []
        for ch in sorted(ap_map.keys()):
            nets = ap_map[ch]
            channel_data.append({
                "channel": ch,
                "count": len(nets),
                "networks": [n.ssid for n in nets],
                "avg_signal": round(sum(n.signal_percent for n in nets) / len(nets), 1)
            })

        return {
            "band_name": "6 GHz",
            "channels": channel_data,
            "recommended_channel": channel_data[0]["channel"] if channel_data else None,
            "reasoning": "6 GHz band offers wide pristine spectrum with AFC coordination."
        }
