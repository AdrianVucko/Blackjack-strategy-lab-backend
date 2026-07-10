"""Statistics derived from per-round simulation results."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class Statistics:
    rounds: int
    ev_per_round: float          # mean net result per round, in base-bet units
    house_edge_pct: float        # -EV as a percentage of one base bet
    variance: float
    std_dev: float
    std_error: float             # standard error of the mean
    ci95: tuple[float, float]    # 95% confidence interval for ev_per_round
    total_result: float          # summed net over all rounds, in base-bet units
    risk_of_ruin: float | None   # None unless a bankroll is supplied


def _risk_of_ruin(mean: float, variance: float, bankroll_units: float | None) -> float | None:
    """Diffusion approximation of risk of ruin over an infinite horizon.

    Returns 1.0 when the player has no edge (mean <= 0) and the classic
    ``exp(-2 * bankroll * edge / variance)`` otherwise.
    """
    if bankroll_units is None:
        return None
    if mean <= 0:
        return 1.0
    if variance == 0:
        return 0.0
    return float(math.exp(-2.0 * mean * bankroll_units / variance))


def compute_statistics(
    nets: np.ndarray,
    *,
    bankroll_units: float | None = None,
) -> Statistics:
    """Compute summary statistics from an array of per-round net results."""
    rounds = int(nets.size)
    if rounds == 0:
        raise ValueError("nets must contain at least one round")

    mean = float(np.mean(nets))
    variance = float(np.var(nets, ddof=1)) if rounds > 1 else 0.0
    std_dev = math.sqrt(variance)
    std_error = std_dev / math.sqrt(rounds) if rounds else 0.0

    return Statistics(
        rounds=rounds,
        ev_per_round=mean,
        house_edge_pct=-mean * 100.0,
        variance=variance,
        std_dev=std_dev,
        std_error=std_error,
        ci95=(mean - 1.96 * std_error, mean + 1.96 * std_error),
        total_result=float(np.sum(nets)),
        risk_of_ruin=_risk_of_ruin(mean, variance, bankroll_units),
    )
