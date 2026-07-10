"""Deterministic round-engine tests using a stacked shoe."""

from __future__ import annotations

import random

from blackjack.core.cards import Card, Rank, Shoe, Suit
from blackjack.core.rules import Rules
from blackjack.simulation.engine import play_round

_SYMBOL_TO_RANK = {rank.symbol: rank for rank in Rank}

S17 = Rules(dealer_hits_soft_17=False)
S17_SURR = Rules(dealer_hits_soft_17=False, surrender_allowed=True)


def stacked_shoe(*symbols: str) -> Shoe:
    """A shoe that deals the given ranks front-first (suit is irrelevant)."""
    shoe = Shoe(num_decks=1, rng=random.Random(0))
    shoe.set_cards([Card(_SYMBOL_TO_RANK[s], Suit.SPADES) for s in symbols])
    return shoe


def test_player_stands_and_dealer_busts_wins_one() -> None:
    # p 10,10=20; dealer up 9 + hole 7 = 16, draws 10 -> bust
    shoe = stacked_shoe("10", "9", "10", "7", "10")
    assert play_round(shoe, S17).net == 1.0


def test_player_blackjack_pays_three_to_two() -> None:
    shoe = stacked_shoe("A", "9", "K", "7")
    result = play_round(shoe, S17)
    assert result.net == 1.5


def test_dealer_blackjack_peek_loses() -> None:
    # dealer up A + hole K = blackjack; player 20 loses
    shoe = stacked_shoe("10", "A", "10", "K")
    assert play_round(shoe, S17).net == -1.0


def test_double_scales_result() -> None:
    # p 6,5=11 vs dealer 6 -> double; draws 9 -> 20; dealer 6+10, draws 10 -> bust
    shoe = stacked_shoe("6", "6", "5", "10", "9", "10")
    assert play_round(shoe, S17).net == 2.0


def test_split_produces_two_hands() -> None:
    # p 8,8 vs dealer 6 -> split; each 8 draws 10 -> 18; dealer 6+10 draws 10 -> bust
    shoe = stacked_shoe("8", "6", "8", "10", "10", "10", "10")
    result = play_round(shoe, S17)
    assert result.num_hands == 2
    assert result.net == 2.0


def test_surrender_loses_half() -> None:
    # p 10,6=16 vs dealer 10 (hole 6, no BJ) -> surrender
    shoe = stacked_shoe("10", "10", "6", "6")
    assert play_round(shoe, S17_SURR).net == -0.5
