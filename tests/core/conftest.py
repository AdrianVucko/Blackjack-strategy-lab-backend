"""Shared helpers for building hands from compact rank notation."""

from __future__ import annotations

import pytest

from blackjack.core.cards import Card, Rank, Suit
from blackjack.core.hand import Hand

_SYMBOL_TO_RANK = {rank.symbol: rank for rank in Rank}


def make_card(symbol: str, suit: Suit = Suit.SPADES) -> Card:
    return Card(_SYMBOL_TO_RANK[symbol], suit)


def make_hand(*symbols: str, from_split: bool = False) -> Hand:
    return Hand([make_card(s) for s in symbols], from_split=from_split)


@pytest.fixture
def hand_factory():
    return make_hand
