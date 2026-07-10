"""Monte Carlo simulation of a card counter using a bet ramp.

Playing decisions use basic strategy; the counter's edge here comes from bet
variation (betting correlation). Index-play deviations and insurance are future
enhancements. The dealer's hole card is counted when dealt, a common and minor
idealization.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

import numpy as np

from blackjack.core.rules import Rules
from blackjack.counting.betting import HI_LO_RAMP, BetRamp
from blackjack.counting.counter import Counter
from blackjack.counting.shoe import CountingShoe
from blackjack.counting.systems import HI_LO, CountingSystem
from blackjack.simulation.engine import play_round
from blackjack.simulation.statistics import Statistics, compute_statistics

_MIN_CARDS_PER_ROUND = 15


@dataclass(frozen=True, slots=True)
class CountingConfig:
    num_rounds: int
    rules: Rules = field(default_factory=Rules)
    system: CountingSystem = HI_LO
    ramp: BetRamp = HI_LO_RAMP
    base_bet: float = 1.0
    starting_bankroll: float | None = None
    seed: int | None = None


@dataclass(slots=True)
class CountingResult:
    config: CountingConfig
    nets: np.ndarray            # per-round net, in base-bet units (already bet-scaled)
    bets: np.ndarray            # per-round wager, in base-bet units
    bet_indices: np.ndarray     # per-round count value used for bet sizing
    bankroll_curve: np.ndarray  # cumulative money incl. base_bet scaling and bankroll
    rounds_played: int
    ruined: bool
    average_bet: float
    statistics: Statistics


def run_counting_simulation(config: CountingConfig) -> CountingResult:
    """Run a counting simulation and return per-round results and statistics."""
    if config.num_rounds < 1:
        raise ValueError("num_rounds must be at least 1")

    rng = random.Random(config.seed)
    counter = Counter(config.system)
    shoe = CountingShoe(
        counter,
        num_decks=config.rules.num_decks,
        penetration=config.rules.penetration,
        rng=rng,
    )

    nets = np.empty(config.num_rounds, dtype=np.float64)
    bets = np.empty(config.num_rounds, dtype=np.float64)
    indices = np.empty(config.num_rounds, dtype=np.float64)
    bankroll = config.starting_bankroll
    ruined = False
    rounds_played = 0

    for i in range(config.num_rounds):
        if shoe.needs_shuffle() or shoe.cards_remaining < _MIN_CARDS_PER_ROUND:
            shoe.shuffle()

        bet_index = counter.bet_index(shoe.decks_remaining)
        wager = config.ramp.units(bet_index)
        indices[i] = bet_index
        bets[i] = wager

        result = play_round(shoe, config.rules)
        net = result.net * wager
        nets[i] = net
        rounds_played += 1

        if bankroll is not None:
            bankroll += net * config.base_bet
            if bankroll <= 0:
                ruined = True
                nets = nets[: i + 1]
                bets = bets[: i + 1]
                indices = indices[: i + 1]
                break

    base = config.starting_bankroll or 0.0
    bankroll_curve = base + np.cumsum(nets) * config.base_bet

    bankroll_units = (
        config.starting_bankroll / config.base_bet
        if config.starting_bankroll is not None and config.base_bet > 0
        else None
    )
    statistics = compute_statistics(nets, bankroll_units=bankroll_units)

    return CountingResult(
        config=config,
        nets=nets,
        bets=bets,
        bet_indices=indices,
        bankroll_curve=bankroll_curve,
        rounds_played=rounds_played,
        ruined=ruined,
        average_bet=float(np.mean(bets)),
        statistics=statistics,
    )
