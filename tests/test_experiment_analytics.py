"""
Unit Tests for Academic Experiment Analytics
Tests calculation of sample mean, standard deviation, Pearson correlation coefficient,
and graceful handling of edge cases (zero variance, missing data, small sample sizes).
"""

import math
from netvision.core.experiment_analytics import (
    calculate_mean_and_stdev,
    calculate_pearson_correlation,
    interpret_correlation,
    summarize_experiment_runs
)
from netvision.database.models import ExperimentRun


def test_calculate_mean_and_stdev():
    # Empty list
    mean, stdev = calculate_mean_and_stdev([])
    assert mean is None
    assert stdev is None

    # Single element
    mean, stdev = calculate_mean_and_stdev([50.0])
    assert mean == 50.0
    assert stdev == 0.0

    # Normal list with None
    mean, stdev = calculate_mean_and_stdev([10.0, 20.0, 30.0, None])
    assert mean == 20.0
    assert abs(stdev - 10.0) < 0.01


def test_calculate_pearson_correlation_perfect():
    # Perfect positive correlation (y = 2x)
    xs = [10.0, 20.0, 30.0, 40.0, 50.0]
    ys = [20.0, 40.0, 60.0, 80.0, 100.0]
    r = calculate_pearson_correlation(xs, ys)
    assert r == 1.0

    # Perfect negative correlation (y = -x)
    ys_neg = [50.0, 40.0, 30.0, 20.0, 10.0]
    r_neg = calculate_pearson_correlation(xs, ys_neg)
    assert r_neg == -1.0


def test_calculate_pearson_correlation_edge_cases():
    # Less than 3 samples
    assert calculate_pearson_correlation([1.0, 2.0], [2.0, 4.0]) is None

    # Mismatched length
    assert calculate_pearson_correlation([1.0, 2.0, 3.0], [1.0, 2.0]) is None

    # Zero variance (constant signal)
    xs_const = [75.0, 75.0, 75.0, 75.0]
    ys_var = [10.0, 20.0, 30.0, 40.0]
    assert calculate_pearson_correlation(xs_const, ys_var) is None

    # List with None values
    xs_with_none = [10.0, None, 30.0, 40.0, 50.0]
    ys_with_none = [20.0, 15.0, 60.0, 80.0, 100.0]
    r = calculate_pearson_correlation(xs_with_none, ys_with_none)
    assert r is not None
    assert r > 0.99


def test_interpret_correlation():
    assert "Very Strong Positive" in interpret_correlation(0.95)
    assert "Strong Negative" in interpret_correlation(-0.65)
    assert "insufficient variance" in interpret_correlation(None)


def test_summarize_experiment_runs():
    runs = [
        ExperimentRun(
            experiment_id="EXP_1",
            run_number=1,
            condition_label="Room A",
            signal_percent=80,
            download_mbps=50.0,
            upload_mbps=20.0,
            ping_ms=15.0,
            jitter_ms=1.5,
            packet_loss_percent=0.0
        ),
        ExperimentRun(
            experiment_id="EXP_1",
            run_number=2,
            condition_label="Room A",
            signal_percent=60,
            download_mbps=35.0,
            upload_mbps=15.0,
            ping_ms=25.0,
            jitter_ms=3.0,
            packet_loss_percent=0.0
        ),
        ExperimentRun(
            experiment_id="EXP_1",
            run_number=3,
            condition_label="Room A",
            signal_percent=40,
            download_mbps=20.0,
            upload_mbps=10.0,
            ping_ms=45.0,
            jitter_ms=6.0,
            packet_loss_percent=0.0
        ),
    ]

    summary = summarize_experiment_runs(runs)
    assert summary["trial_count"] == 3
    assert summary["mean_signal"] == 60.0
    assert summary["mean_download"] == 35.0
    assert summary["mean_latency"] > 25.0
    assert summary["r_signal_download"] == 1.0  # (80,50), (60,35), (40,20) form a line!

