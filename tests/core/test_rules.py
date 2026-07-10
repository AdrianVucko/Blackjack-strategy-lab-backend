"""Tests for dealer play and hand settlement."""

from __future__ import annotations

import random

from blackjack.core.cards import Shoe
from blackjack.core.enums import Outcome
from blackjack.core.rules import Rules, play_dealer, resolve
from tests.core.conftest import make_hand

RULES = Rules()


def test_dealer_stands_on_hard_17() -> None:
    hand = make_hand("10", "7")
    play_dealer(hand, Shoe(rng=random.Random(0)), RULES)
    assert hand.total == 17
    assert len(hand) == 2


def test_dealer_hits_soft_17_when_enabled() -> None:
    hand = make_hand("A", "6")
    play_dealer(hand, Shoe(rng=random.Random(0)), Rules(dealer_hits_soft_17=True))
    assert len(hand) > 2


def test_dealer_stands_soft_17_when_disabled() -> None:
    hand = make_hand("A", "6")
    play_dealer(hand, Shoe(rng=random.Random(0)), Rules(dealer_hits_soft_17=False))
    assert hand.total == 17
    assert len(hand) == 2


def test_dealer_hits_until_at_least_17() -> None:
    hand = make_hand("5", "6")
    play_dealer(hand, Shoe(rng=random.Random(0)), RULES)
    assert hand.total >= 17


def test_player_blackjack_pays_three_to_two() -> None:
    outcome, net = resolve(make_hand("A", "K"), make_hand("10", "8"), RULES)
    assert outcome is Outcome.BLACKJACK
    assert net == 1.5


def test_both_blackjack_pushes() -> None:
    outcome, net = resolve(make_hand("A", "K"), make_hand("A", "Q"), RULES)
    assert outcome is Outcome.PUSH
    assert net == 0.0


def test_dealer_blackjack_beats_regular_21() -> None:
    outcome, net = resolve(make_hand("7", "7", "7"), make_hand("A", "K"), RULES)
    assert outcome is Outcome.LOSE
    assert net == -1.0


def test_player_bust_loses() -> None:
    outcome, net = resolve(make_hand("10", "9", "5"), make_hand("10", "7"), RULES)
    assert outcome is Outcome.LOSE
    assert net == -1.0


def test_dealer_bust_wins() -> None:
    outcome, net = resolve(make_hand("10", "9"), make_hand("10", "6", "10"), RULES)
    assert outcome is Outcome.WIN
    assert net == 1.0


def test_higher_total_wins() -> None:
    outcome, net = resolve(make_hand("10", "10"), make_hand("10", "8"), RULES)
    assert outcome is Outcome.WIN
    assert net == 1.0


def test_equal_total_pushes() -> None:
    outcome, net = resolve(make_hand("10", "8"), make_hand("10", "8"), RULES)
    assert outcome is Outcome.PUSH
    assert net == 0.0


def test_doubled_wager_scales_result() -> None:
    outcome, net = resolve(make_hand("10", "10"), make_hand("10", "8"), RULES, wager=2.0)
    assert outcome is Outcome.WIN
    assert net == 2.0


def test_surrender_loses_half() -> None:
    outcome, net = resolve(make_hand("10", "6"), make_hand("10", "7"), RULES, surrendered=True)
    assert outcome is Outcome.SURRENDER
    assert net == -0.5
