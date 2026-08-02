"""Tests for the uniform-random baseline policy."""

from __future__ import annotations

import random

from blackjack.core.cards import Card, Rank, Suit
from blackjack.core.enums import Action
from blackjack.core.rules import Rules
from blackjack.simulation import SimulationConfig, run_simulation
from blackjack.strategy import RandomPolicy
from tests.core.conftest import make_hand

RULES = Rules(surrender_allowed=True)


def up(symbol: str) -> Card:
    rank = next(r for r in Rank if r.symbol == symbol)
    return Card(rank, Suit.HEARTS)


def sample_actions(policy: RandomPolicy, *symbols: str, n: int = 200, **kwargs) -> set[Action]:
    return {policy(make_hand(*symbols), up("10"), RULES, **kwargs) for _ in range(n)}


def test_two_card_hand_covers_all_legal_actions() -> None:
    actions = sample_actions(RandomPolicy(random.Random(1)), "8", "8")
    assert actions == {Action.HIT, Action.STAND, Action.DOUBLE, Action.SPLIT, Action.SURRENDER}


def test_non_pair_never_splits() -> None:
    actions = sample_actions(RandomPolicy(random.Random(2)), "10", "6")
    assert Action.SPLIT not in actions
    assert actions == {Action.HIT, Action.STAND, Action.DOUBLE, Action.SURRENDER}


def test_three_card_hand_only_hits_or_stands() -> None:
    actions = sample_actions(RandomPolicy(random.Random(3)), "2", "3", "4")
    assert actions == {Action.HIT, Action.STAND}


def test_respects_can_split_override() -> None:
    actions = sample_actions(RandomPolicy(random.Random(4)), "8", "8", can_split=False)
    assert Action.SPLIT not in actions


def test_split_hand_cannot_surrender() -> None:
    policy = RandomPolicy(random.Random(5))
    hand = make_hand("8", "3", from_split=True)
    actions = {policy(hand, up("10"), RULES) for _ in range(200)}
    assert Action.SURRENDER not in actions


def test_no_double_when_rules_forbid() -> None:
    policy = RandomPolicy(random.Random(6))
    rules = Rules(double_allowed=False, surrender_allowed=False)
    actions = {policy(make_hand("6", "5"), up("10"), rules) for _ in range(200)}
    assert actions == {Action.HIT, Action.STAND}


def test_seeded_policy_is_reproducible() -> None:
    def run(seed: int) -> list[Action]:
        policy = RandomPolicy(random.Random(seed))
        return [policy(make_hand("10", "6"), up("10"), RULES) for _ in range(50)]

    assert run(7) == run(7)
    assert run(7) != run(8)


def test_random_play_loses_far_more_than_basic_strategy() -> None:
    config = SimulationConfig(num_rounds=20_000, seed=11)
    basic = run_simulation(config)
    rand = run_simulation(config, policy=RandomPolicy(random.Random(12)))
    assert rand.statistics.ev_per_round < -0.10
    assert rand.statistics.ev_per_round < basic.statistics.ev_per_round
