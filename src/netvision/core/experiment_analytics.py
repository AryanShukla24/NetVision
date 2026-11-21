"""
NetVision - Academic Experiment Analytics Module
Computes genuine statistics, spread (standard deviation), and Pearson correlation
coefficients for multi-trial network performance experiments.
"""

import math
import statistics
from typing import List, Tuple, Optional, Dict, Any
from netvision.database.models import ExperimentRun


def calculate_mean_and_stdev(values: List[Optional[float]]) -> Tuple[Optional[float], Optional[float]]:
    """
    Computes sample mean and sample standard deviation for a list of values,
    excluding None entries. Returns (None, None) if no valid values exist.
    """
    valid = [v for v in values if v is not None and not math.isnan(v)]
    if not valid:
        return None, None
    if len(valid) == 1:
        return round(float(valid[0]), 2), 0.0

    mean_val = round(float(statistics.mean(valid)), 2)
    stdev_val = round(float(statistics.stdev(valid)), 2)
    return mean_val, stdev_val


def calculate_pearson_correlation(x: List[Optional[float]], y: List[Optional[float]]) -> Optional[float]:
    """
    Computes genuine Pearson correlation coefficient r between two series:
        r = sum((x - mean_x) * (y - mean_y)) / sqrt(sum((x - mean_x)^2) * sum((y - mean_y)^2))

    Returns None if:
    - Lists have different lengths
    - Fewer than 3 valid paired samples exist
    - Either series has zero variance (constant values)
    """
    if len(x) != len(y):
        return None

    paired = [
        (float(xi), float(yi))
        for xi, yi in zip(x, y)
        if xi is not None and yi is not None and not math.isnan(xi) and not math.isnan(yi)
    ]

    if len(paired) < 3:
        return None

    xs = [p[0] for p in paired]
    ys = [p[1] for p in paired]

    mean_x = statistics.mean(xs)
    mean_y = statistics.mean(ys)

    var_x = sum((xi - mean_x) ** 2 for xi in xs)
    var_y = sum((yi - mean_y) ** 2 for yi in ys)

    if var_x <= 1e-9 or var_y <= 1e-9:
        return None

    cov_xy = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(xs, ys))
    r = cov_xy / math.sqrt(var_x * var_y)
    # Clamp to [-1.0, 1.0] to guard against floating-point imprecision
    return round(float(max(-1.0, min(1.0, r))), 3)


def interpret_correlation(r: Optional[float]) -> str:
    """Provides academic interpretation of the correlation coefficient."""
    if r is None:
        return "N/A (insufficient variance or samples < 3)"
    abs_r = abs(r)
    direction = "Positive" if r > 0 else "Negative"
    if abs_r >= 0.8:
        strength = "Very Strong"
    elif abs_r >= 0.6:
        strength = "Strong"
    elif abs_r >= 0.4:
        strength = "Moderate"
    elif abs_r >= 0.2:
        strength = "Weak"
    else:
        strength = "Negligible"
    return f"r = {r:+.3f} ({strength} {direction})"


def summarize_experiment_runs(runs: List[ExperimentRun]) -> Dict[str, Any]:
    """Generates complete statistical summary across a set of trial runs."""
    signals = [r.signal_percent for r in runs]
    downloads = [r.download_mbps for r in runs]
    uploads = [r.upload_mbps for r in runs]
    latencies = [r.ping_ms for r in runs]
    jitters = [r.jitter_ms for r in runs]

    m_sig, s_sig = calculate_mean_and_stdev([float(s) if s is not None else None for s in signals])
    m_down, s_down = calculate_mean_and_stdev(downloads)
    m_up, s_up = calculate_mean_and_stdev(uploads)
    m_lat, s_lat = calculate_mean_and_stdev(latencies)
    m_jit, s_jit = calculate_mean_and_stdev(jitters)

    r_signal_download = calculate_pearson_correlation(
        [float(s) if s is not None else None for s in signals],
        downloads
    )

    return {
        "trial_count": len(runs),
        "mean_signal": m_sig,
        "stdev_signal": s_sig,
        "mean_download": m_down,
        "stdev_download": s_down,
        "mean_upload": m_up,
        "stdev_upload": s_up,
        "mean_latency": m_lat,
        "stdev_latency": s_lat,
        "mean_jitter": m_jit,
        "stdev_jitter": s_jit,
        "r_signal_download": r_signal_download,
        "r_interpretation": interpret_correlation(r_signal_download),
    }

