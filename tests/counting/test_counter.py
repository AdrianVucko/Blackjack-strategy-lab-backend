"""Tests for counting systems, the Counter, and bet ramps."""

from __future__ import annotations

import random

from blackjack.core.cards import Card, Rank, Suit, build_deck
from blackjack.counting.betting import HI_LO_RAMP, BetRamp
from blackjack.counting.counter import Counter
from blackjack.counting.shoe import CountingShoe
from blackjack.counting.systems import HI_LO, HI_OPT_I, KO

_SYMBOL_TO_RANK = {rank.symbol: rank for rank in Rank}


def card(symbol: str) -> Card:
    return Card(_SYMBOL_TO_RANK[symbol], Suit.SPADES)


def test_hi_lo_tag_values() -> None:
    assert HI_LO.value(card("5")) == 1
    assert HI_LO.value(card("7")) == 0
    assert HI_LO.value(card("K")) == -1
    assert HI_LO.value(card("A")) == -1


def test_balanced_systems_sum_to_zero_over_full_deck() -> None:
    for system in (HI_LO, HI_OPT_I):
        assert sum(system.value(c) for c in build_deck()) == 0


def test_ko_is_unbalanced() -> None:
    assert sum(KO.value(c) for c in build_deck()) == 4  # +1 for each 7 (four 7s)
    assert KO.balanced is False


def test_counter_tracks_running_count() -> None:
    counter = Counter(HI_LO)
    counter.observe_many([card("5"), card("6"), card("K")])
    assert counter.running_count == 1
    assert counter.cards_seen == 3


def test_true_count_divides_by_decks_remaining() -> None:
    counter = Counter(HI_LO)
    counter.observe_many([card("2")] * 6)  # running +6
    assert counter.true_count(3.0) == 2.0


def test_reset_clears_count() -> None:
    counter = Counter(HI_LO)
    counter.observe(card("5"))
    counter.reset()
    assert counter.running_count == 0
    assert counter.cards_seen == 0


def test_counting_shoe_updates_and_resets_on_shuffle() -> None:
    counter = Counter(HI_LO)
    shoe = CountingShoe(counter, num_decks=1, rng=random.Random(1))
    for _ in range(10):
        shoe.deal()
    assert counter.cards_seen == 10
    shoe.shuffle()
    assert counter.running_count == 0
    assert counter.cards_seen == 0


def test_counting_shoe_full_deck_returns_to_zero() -> None:
    counter = Counter(HI_LO)
    shoe = CountingShoe(counter, num_decks=1, rng=random.Random(2))
    for _ in range(52):
        shoe.deal()
    assert counter.running_count == 0


def test_bet_ramp_steps() -> None:
    assert HI_LO_RAMP.units(-3) == 1.0
    assert HI_LO_RAMP.units(1.5) == 1.0
    assert HI_LO_RAMP.units(2.0) == 2.0
    assert HI_LO_RAMP.units(3.9) == 4.0
    assert HI_LO_RAMP.units(10) == 12.0


def test_custom_bet_ramp() -> None:
    ramp = BetRamp(tiers=((float("-inf"), 1.0), (1.0, 5.0)))
    assert ramp.units(0) == 1.0
    assert ramp.units(1) == 5.0
