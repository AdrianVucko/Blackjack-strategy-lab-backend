"""Tests for basic strategy decisions across representative cells."""

from __future__ import annotations

from blackjack.core.cards import Card, Rank, Suit
from blackjack.core.enums import Action
from blackjack.core.rules import Rules
from blackjack.strategy import build_chart, decide
from tests.core.conftest import make_hand

S17 = Rules(dealer_hits_soft_17=False, surrender_allowed=False)
S17_SURR = Rules(dealer_hits_soft_17=False, surrender_allowed=True)
H17 = Rules(dealer_hits_soft_17=True, surrender_allowed=False)
H17_SURR = Rules(dealer_hits_soft_17=True, surrender_allowed=True)


def up(symbol: str) -> Card:
    rank = next(r for r in Rank if r.symbol == symbol)
    return Card(rank, Suit.HEARTS)


# --- Hard totals ---

def test_hard_11_doubles_vs_ten() -> None:
    assert decide(make_hand("6", "5"), up("10"), S17) is Action.DOUBLE


def test_hard_11_vs_ace_hits_s17_doubles_h17() -> None:
    assert decide(make_hand("6", "5"), up("A"), S17) is Action.HIT
    assert decide(make_hand("6", "5"), up("A"), H17) is Action.DOUBLE


def test_hard_12_stands_only_vs_4_5_6() -> None:
    assert decide(make_hand("10", "2"), up("4"), S17) is Action.STAND
    assert decide(make_hand("10", "2"), up("3"), S17) is Action.HIT
    assert decide(make_hand("10", "2"), up("2"), S17) is Action.HIT


def test_hard_16_vs_ten_surrender_when_allowed() -> None:
    assert decide(make_hand("10", "6"), up("10"), S17) is Action.HIT
    assert decide(make_hand("10", "6"), up("10"), S17_SURR) is Action.SURRENDER


def test_hard_15_vs_ace_surrender_only_h17() -> None:
    assert decide(make_hand("10", "5"), up("A"), S17_SURR) is Action.HIT
    assert decide(make_hand("10", "5"), up("A"), H17_SURR) is Action.SURRENDER


def test_hard_low_total_always_hits() -> None:
    assert decide(make_hand("2", "3"), up("6"), S17) is Action.HIT


def test_hard_18_stands() -> None:
    assert decide(make_hand("10", "8"), up("6"), S17) is Action.STAND


# --- Soft totals ---

def test_soft_13_doubles_vs_5_6() -> None:
    assert decide(make_hand("A", "2"), up("6"), S17) is Action.DOUBLE
    assert decide(make_hand("A", "2"), up("4"), S17) is Action.HIT


def test_soft_18_vs_9_hits_vs_6_doubles() -> None:
    assert decide(make_hand("A", "7"), up("9"), S17) is Action.HIT
    assert decide(make_hand("A", "7"), up("6"), S17) is Action.DOUBLE


def test_soft_18_vs_2_stands_s17_doubles_h17() -> None:
    assert decide(make_hand("A", "7"), up("2"), S17) is Action.STAND
    assert decide(make_hand("A", "7"), up("2"), H17) is Action.DOUBLE


def test_soft_19_vs_6_stands_s17_doubles_h17() -> None:
    assert decide(make_hand("A", "8"), up("6"), S17) is Action.STAND
    assert decide(make_hand("A", "8"), up("6"), H17) is Action.DOUBLE


# --- Pairs ---

def test_aces_and_eights_always_split() -> None:
    assert decide(make_hand("A", "A"), up("10"), S17) is Action.SPLIT
    assert decide(make_hand("8", "8"), up("A"), S17) is Action.SPLIT


def test_tens_never_split() -> None:
    assert decide(make_hand("10", "10"), up("6"), S17) is Action.STAND


def test_nines_split_but_stand_vs_7() -> None:
    assert decide(make_hand("9", "9"), up("6"), S17) is Action.SPLIT
    assert decide(make_hand("9", "9"), up("7"), S17) is Action.STAND


def test_fives_treated_as_hard_ten() -> None:
    assert decide(make_hand("5", "5"), up("6"), S17) is Action.DOUBLE
    assert decide(make_hand("5", "5"), up("10"), S17) is Action.HIT


def test_pair_split_depends_on_das() -> None:
    das = Rules(double_after_split=True)
    no_das = Rules(double_after_split=False)
    assert decide(make_hand("4", "4"), up("6"), das) is Action.SPLIT
    assert decide(make_hand("4", "4"), up("6"), no_das) is Action.HIT


# --- Availability overrides ---

def test_double_falls_back_to_hit_when_not_allowed() -> None:
    no_double = Rules(double_allowed=False)
    assert decide(make_hand("6", "5"), up("6"), no_double) is Action.HIT


def test_three_card_11_cannot_double() -> None:
    assert decide(make_hand("4", "3", "4"), up("6"), S17) is Action.HIT


# --- Chart ---

def test_build_chart_shape_and_values() -> None:
    chart = build_chart(S17)
    assert set(chart) == {"hard", "soft", "pairs"}
    assert chart["pairs"]["A,A"]["10"] == Action.SPLIT.value
    assert chart["hard"]["11"]["10"] == Action.DOUBLE.value
    assert chart["soft"]["A,7"]["9"] == Action.HIT.value
    valid = {a.value for a in Action}
    for section in chart.values():
        for row in section.values():
            assert set(row.values()) <= valid
