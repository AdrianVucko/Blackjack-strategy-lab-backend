"""Monte Carlo simulation loop over many blackjack rounds."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

import numpy as np

from blackjack.core.cards import Shoe
from blackjack.core.rules import Rules
from blackjack.simulation.engine import Policy, play_round
from blackjack.simulation.statistics import Statistics, compute_statistics
from blackjack.strategy import decide

_MIN_CARDS_PER_ROUND = 15


@dataclass(frozen=True, slots=True)
class SimulationConfig:
    num_rounds: int
    rules: Rules = field(default_factory=Rules)
    bet: float = 1.0
    starting_bankroll: float | None = None
    seed: int | None = None


@dataclass(slots=True)
class SimulationResult:
    config: SimulationConfig
    nets: np.ndarray            # per-round net, in base-bet units
    bankroll_curve: np.ndarray  # cumulative money incl. bet scaling and starting bankroll
    rounds_played: int
    ruined: bool
    statistics: Statistics


def run_simulation(config: SimulationConfig, *, policy: Policy = decide) -> SimulationResult:
    """Run ``config.num_rounds`` rounds and return results with summary statistics."""
    if config.num_rounds < 1:
        raise ValueError("num_rounds must be at least 1")

    rng = random.Random(config.seed)
    shoe = Shoe(
        num_decks=config.rules.num_decks,
        penetration=config.rules.penetration,
        rng=rng,
    )

    nets = np.empty(config.num_rounds, dtype=np.float64)
    bankroll = config.starting_bankroll
    ruined = False
    rounds_played = 0

    for i in range(config.num_rounds):
        if shoe.needs_shuffle() or shoe.cards_remaining < _MIN_CARDS_PER_ROUND:
            shoe.shuffle()

        result = play_round(shoe, config.rules, policy=policy)
        nets[i] = result.net
        rounds_played += 1

        if bankroll is not None:
            bankroll += result.net * config.bet
            if bankroll <= 0:
                ruined = True
                nets = nets[: i + 1]
                break

    base = config.starting_bankroll or 0.0
    bankroll_curve = base + np.cumsum(nets) * config.bet

    bankroll_units = (
        config.starting_bankroll / config.bet
        if config.starting_bankroll is not None and config.bet > 0
        else None
    )
    statistics = compute_statistics(nets, bankroll_units=bankroll_units)

    return SimulationResult(
        config=config,
        nets=nets,
        bankroll_curve=bankroll_curve,
        rounds_played=rounds_played,
        ruined=ruined,
        statistics=statistics,
    )
