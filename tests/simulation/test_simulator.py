"""Simulator loop and statistics tests."""

from __future__ import annotations

import numpy as np

from blackjack.core.rules import Rules
from blackjack.simulation import SimulationConfig, compute_statistics, run_simulation


def test_simulation_is_reproducible_with_seed() -> None:
    config = SimulationConfig(num_rounds=2000, rules=Rules(), seed=123)
    first = run_simulation(config)
    second = run_simulation(config)
    assert np.array_equal(first.nets, second.nets)
    assert first.statistics.total_result == second.statistics.total_result


def test_basic_strategy_house_edge_is_small_and_negative() -> None:
    result = run_simulation(SimulationConfig(num_rounds=50_000, rules=Rules(), seed=7))
    # Basic strategy loses slowly: house edge is a small positive percentage.
    assert 0.0 < result.statistics.house_edge_pct < 2.0


def test_standard_deviation_is_in_expected_range() -> None:
    result = run_simulation(SimulationConfig(num_rounds=50_000, rules=Rules(), seed=7))
    assert 1.0 < result.statistics.std_dev < 1.6


def test_bankroll_curve_tracks_cumulative_result() -> None:
    config = SimulationConfig(num_rounds=1000, seed=1, bet=5.0, starting_bankroll=1000.0)
    result = run_simulation(config)
    expected_final = 1000.0 + float(np.sum(result.nets)) * 5.0
    assert result.bankroll_curve[-1] == expected_final


def test_ruin_stops_early_when_bankroll_depleted() -> None:
    config = SimulationConfig(num_rounds=100_000, seed=42, bet=50.0, starting_bankroll=100.0)
    result = run_simulation(config)
    assert result.ruined
    assert result.rounds_played < config.num_rounds


def test_risk_of_ruin_between_zero_and_one() -> None:
    config = SimulationConfig(num_rounds=20_000, seed=3, bet=1.0, starting_bankroll=200.0)
    result = run_simulation(config)
    ror = result.statistics.risk_of_ruin
    assert ror is not None
    assert 0.0 <= ror <= 1.0


def test_risk_of_ruin_is_one_without_edge() -> None:
    nets = np.array([-1.0, 1.0, -1.0, 1.0, -0.2])  # negative mean
    stats = compute_statistics(nets, bankroll_units=100.0)
    assert stats.risk_of_ruin == 1.0


def test_statistics_without_bankroll_has_no_risk_of_ruin() -> None:
    result = run_simulation(SimulationConfig(num_rounds=500, seed=9))
    assert result.statistics.risk_of_ruin is None
