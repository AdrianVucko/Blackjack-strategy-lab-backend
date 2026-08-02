"""Uniform-random baseline policy.

Chooses uniformly among the actions that are legal in the current state.
Serves as the worst-case reference point when comparing strategies: any
sensible strategy should beat it by a wide margin.
"""

from __future__ import annotations

import random

from blackjack.core.cards import Card
from blackjack.core.enums import Action
from blackjack.core.hand import Hand
from blackjack.core.rules import Rules


class RandomPolicy:
    """Policy callable that picks a uniformly random legal action.

    Pass a seeded ``random.Random`` for reproducible simulations; keep it
    separate from the shoe's RNG so decisions and shuffles stay independent.
    """

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng if rng is not None else random.Random()

    def __call__(
        self,
        hand: Hand,
        dealer_upcard: Card,
        rules: Rules,
        *,
        can_double: bool | None = None,
        can_split: bool | None = None,
        can_surrender: bool | None = None,
    ) -> Action:
        # Same availability inference as basic strategy's `decide`.
        is_first_two = len(hand) == 2
        if can_double is None:
            can_double = (
                rules.double_allowed
                and is_first_two
                and (not hand.from_split or rules.double_after_split)
            )
        if can_split is None:
            can_split = hand.is_pair and is_first_two
        if can_surrender is None:
            can_surrender = rules.surrender_allowed and is_first_two and not hand.from_split

        actions = [Action.HIT, Action.STAND]
        if can_double and is_first_two:
            actions.append(Action.DOUBLE)
        if can_split and hand.is_pair and is_first_two:
            actions.append(Action.SPLIT)
        if can_surrender and is_first_two:
            actions.append(Action.SURRENDER)
        return self._rng.choice(actions)
