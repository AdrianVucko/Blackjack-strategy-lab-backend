"""Tests for the numpy analysis helpers."""

from __future__ import annotations

import numpy as np

from blackjack.analysis import count_edge_curve, histogram


def test_count_edge_curve_buckets_by_floor() -> None:
    # floors: -1.5 -> -2, -0.2 -> -1, 0.9 -> 0, 1.1 & 1.8 -> 1, 3.4 -> 3
    bet_indices = np.array([-1.5, -0.2, 0.9, 1.1, 1.8, 3.4])
    nets = np.array([-2.0, -1.0, 0.0, 1.0, 1.0, 5.0])
    curve = {b.count: b for b in count_edge_curve(bet_indices, nets)}
    assert {c: b.n for c, b in curve.items()} == {-2: 1, -1: 1, 0: 1, 1: 2, 3: 1}
    assert curve[1].mean_net == 1.0
    assert curve[3].mean_net == 5.0


def test_count_edge_curve_tracks_synthetic_edge() -> None:
    rng = np.random.default_rng(0)
    tc = rng.integers(-3, 4, size=200_000).astype(float)
    # net expectation rises 2% per true count
    nets = 0.02 * tc + rng.normal(0, 1.0, size=tc.size)
    curve = count_edge_curve(tc, nets)
    counts = np.array([b.count for b in curve])
    means = np.array([b.mean_net for b in curve])
    assert means[0] < means[-1]
    assert np.corrcoef(counts, means)[0, 1] > 0.9


def test_histogram_shape() -> None:
    values = np.array([0.0, 1.0, 1.0, 2.0, 2.0, 2.0])
    centers, counts = histogram(values, bins=4)
    assert len(centers) == 4
    assert len(counts) == 4
    assert sum(counts) == values.size
