"""Numpy analysis helpers that turn simulation arrays into plottable data.

Kept free of any plotting library so the numbers are independently testable;
:mod:`blackjack.viz` turns these into Plotly figures.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class EdgeBucket:
    count: int          # integer count bucket (floor of the bet index)
    mean_net: float     # mean per-round net in this bucket (base-bet units)
    n: int              # number of rounds in the bucket
    ci95_half: float    # half-width of the 95% CI on mean_net


def count_edge_curve(
    bet_indices: np.ndarray,
    nets: np.ndarray,
    *,
    low: int = -5,
    high: int = 6,
) -> list[EdgeBucket]:
    """Mean per-round net grouped by integer count bucket (``floor`` of the index).

    Use with a flat bet ramp so ``nets`` are per-unit results and each bucket's
    ``mean_net`` reads directly as the player edge at that count.
    """
    buckets = np.floor(bet_indices).astype(int)
    curve: list[EdgeBucket] = []
    for count in range(low, high):
        mask = buckets == count
        n = int(mask.sum())
        if n == 0:
            continue
        sample = nets[mask]
        mean = float(sample.mean())
        se = float(sample.std(ddof=1) / np.sqrt(n)) if n > 1 else 0.0
        curve.append(EdgeBucket(count=count, mean_net=mean, n=n, ci95_half=1.96 * se))
    return curve


def histogram(values: np.ndarray, *, bins: int = 40) -> tuple[list[float], list[int]]:
    """Return ``(bin_centers, counts)`` for a histogram of ``values``."""
    counts, edges = np.histogram(values, bins=bins)
    centers = (edges[:-1] + edges[1:]) / 2
    return [float(c) for c in centers], [int(c) for c in counts]
