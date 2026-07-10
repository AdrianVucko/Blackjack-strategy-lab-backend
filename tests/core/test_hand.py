"""Tests for hand value logic: soft/hard aces, blackjack, bust, pairs."""

from __future__ import annotations

from tests.core.conftest import make_hand


def test_simple_hard_total() -> None:
    assert make_hand("10", "7").total == 17


def test_single_ace_is_soft() -> None:
    hand = make_hand("A", "6")
    assert hand.total == 17
    assert hand.is_soft


def test_ace_downgrades_to_avoid_bust() -> None:
    hand = make_hand("A", "6", "10")
    assert hand.total == 17
    assert not hand.is_soft


def test_two_aces() -> None:
    hand = make_hand("A", "A")
    assert hand.total == 12
    assert hand.is_soft


def test_blackjack_detected() -> None:
    hand = make_hand("A", "K")
    assert hand.total == 21
    assert hand.is_blackjack


def test_21_from_split_is_not_blackjack() -> None:
    hand = make_hand("A", "K", from_split=True)
    assert hand.total == 21
    assert not hand.is_blackjack


def test_three_card_21_is_not_blackjack() -> None:
    hand = make_hand("7", "7", "7")
    assert hand.total == 21
    assert not hand.is_blackjack


def test_bust() -> None:
    hand = make_hand("10", "9", "5")
    assert hand.total == 24
    assert hand.is_bust


def test_pair_by_rank_value() -> None:
    assert make_hand("8", "8").is_pair
    assert make_hand("K", "10").is_pair  # both value 10
    assert not make_hand("9", "8").is_pair
