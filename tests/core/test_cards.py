"""Tests for cards, ranks, and the shoe."""

from __future__ import annotations

import random

import pytest

from blackjack.core.cards import Card, Rank, Shoe, Suit, build_deck


def test_deck_has_52_unique_cards() -> None:
    deck = build_deck()
    assert len(deck) == 52
    assert len(set(deck)) == 52


@pytest.mark.parametrize(
    ("symbol", "expected_value"),
    [("2", 2), ("10", 10), ("J", 10), ("Q", 10), ("K", 10), ("A", 11)],
)
def test_rank_values(symbol: str, expected_value: int) -> None:
    rank = next(r for r in Rank if r.symbol == symbol)
    assert rank.points == expected_value


def test_card_str() -> None:
    assert str(Card(Rank.ACE, Suit.SPADES)) == "AS"


def test_shoe_size_matches_num_decks() -> None:
    shoe = Shoe(num_decks=6)
    assert shoe.total_cards == 6 * 52
    assert shoe.cards_remaining == 6 * 52


def test_shoe_deal_decrements_remaining() -> None:
    shoe = Shoe(num_decks=1)
    shoe.deal()
    assert shoe.cards_remaining == 51


def test_shoe_is_seedable_and_reproducible() -> None:
    first = [str(c) for c in _drain(Shoe(num_decks=1, rng=random.Random(42)))]
    second = [str(c) for c in _drain(Shoe(num_decks=1, rng=random.Random(42)))]
    assert first == second


def test_needs_shuffle_triggers_at_penetration() -> None:
    shoe = Shoe(num_decks=1, penetration=0.5)
    assert not shoe.needs_shuffle()
    for _ in range(26):
        shoe.deal()
    assert shoe.needs_shuffle()


def test_deal_from_empty_shoe_raises() -> None:
    shoe = Shoe(num_decks=1)
    _drain(shoe)
    with pytest.raises(IndexError):
        shoe.deal()


@pytest.mark.parametrize("num_decks", [0, -1])
def test_invalid_num_decks_raises(num_decks: int) -> None:
    with pytest.raises(ValueError):
        Shoe(num_decks=num_decks)


@pytest.mark.parametrize("penetration", [0.0, 1.5])
def test_invalid_penetration_raises(penetration: float) -> None:
    with pytest.raises(ValueError):
        Shoe(penetration=penetration)


def _drain(shoe: Shoe) -> list[Card]:
    return [shoe.deal() for _ in range(shoe.cards_remaining)]
