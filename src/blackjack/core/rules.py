"""Table rules, dealer play, and hand settlement."""

from __future__ import annotations

from dataclasses import dataclass

from blackjack.core.cards import Shoe
from blackjack.core.enums import Outcome
from blackjack.core.hand import Hand


@dataclass(frozen=True, slots=True)
class Rules:
    """Configurable table rules affecting strategy and house edge."""

    num_decks: int = 6
    dealer_hits_soft_17: bool = True
    blackjack_payout: float = 1.5
    double_allowed: bool = True
    double_after_split: bool = True
    resplit_allowed: bool = True
    max_splits: int = 3
    surrender_allowed: bool = False
    penetration: float = 0.75


def play_dealer(hand: Hand, shoe: Shoe, rules: Rules) -> Hand:
    """Play the dealer to completion per the standard hit/stand rules.

    Dealer draws below 17 and, when ``dealer_hits_soft_17`` is set, also draws
    on a soft 17. Mutates and returns the given hand.
    """
    while True:
        total = hand.total
        if total < 17:
            hand.add(shoe.deal())
            continue
        if total == 17 and hand.is_soft and rules.dealer_hits_soft_17:
            hand.add(shoe.deal())
            continue
        return hand


def resolve(
    player: Hand,
    dealer: Hand,
    rules: Rules,
    *,
    wager: float = 1.0,
    surrendered: bool = False,
) -> tuple[Outcome, float]:
    """Settle a player hand against the dealer.

    Returns the outcome and the net result in units of the base bet
    (positive = player profit, negative = loss).
    """
    if surrendered:
        return Outcome.SURRENDER, -0.5

    player_bj = player.is_blackjack
    dealer_bj = dealer.is_blackjack

    if player_bj and dealer_bj:
        return Outcome.PUSH, 0.0
    if player_bj:
        return Outcome.BLACKJACK, rules.blackjack_payout
    if dealer_bj:
        return Outcome.LOSE, -wager

    if player.is_bust:
        return Outcome.LOSE, -wager
    if dealer.is_bust:
        return Outcome.WIN, wager

    if player.total > dealer.total:
        return Outcome.WIN, wager
    if player.total < dealer.total:
        return Outcome.LOSE, -wager
    return Outcome.PUSH, 0.0
