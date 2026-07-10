"""Tests for the card-counting simulation."""

from __future__ import annotations

import numpy as np

from blackjack.core.rules import Rules
from blackjack.counting import CountingConfig, run_counting_simulation
from blackjack.counting.betting import FLAT_RAMP


def test_counting_is_reproducible_with_seed() -> None:
    config = CountingConfig(num_rounds=3000, seed=99)
    first = run_counting_simulation(config)
    second = run_counting_simulation(config)
    assert np.array_equal(first.nets, second.nets)


def test_bet_ramp_produces_variable_bets() -> None:
    result = run_counting_simulation(CountingConfig(num_rounds=20_000, seed=5))
    assert result.average_bet > 1.0
    assert result.bets.max() > result.bets.min()


def test_higher_true_count_raises_average_bet() -> None:
    result = run_counting_simulation(CountingConfig(num_rounds=40_000, seed=11))
    high = result.bets[result.bet_indices >= 3.0]
    low = result.bets[result.bet_indices <= 0.0]
    assert high.size and low.size
    assert high.mean() > low.mean()


def test_high_counts_are_favorable_low_counts_are_not() -> None:
    # The scientific basis of counting: player edge rises with the true count.
    # Measured with a flat ramp so each round's net is the per-unit result.
    result = run_counting_simulation(
        CountingConfig(num_rounds=700_000, rules=Rules(), ramp=FLAT_RAMP, seed=2024)
    )
    tc, net = result.bet_indices, result.nets
    high = net[tc >= 1].mean()
    low = net[tc <= -2].mean()
    assert low < -0.01          # low counts are clearly unfavorable
    assert high >= 0.0          # high counts are at least break-even
    assert high - low > 0.02    # edge rises materially with the count


def test_flat_ramp_matches_flat_expectation_sign() -> None:
    result = run_counting_simulation(
        CountingConfig(num_rounds=50_000, ramp=FLAT_RAMP, seed=7)
    )
    assert result.average_bet == 1.0
    assert result.statistics.ev_per_round < 0  # no spread -> house edge remains
