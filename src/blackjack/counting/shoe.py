"""A shoe that feeds every dealt card to an attached counter."""

from __future__ import annotations

import random

from blackjack.core.cards import Card, Shoe
from blackjack.counting.counter import Counter


class CountingShoe(Shoe):
    """A :class:`Shoe` that updates a :class:`Counter` on every deal.

    Because the round engine draws through ``deal()``, wrapping the shoe means
    all cards are counted with no engine changes. Reshuffling resets the count,
    matching a fresh shoe.
    """

    def __init__(
        self,
        counter: Counter,
        *,
        num_decks: int = 6,
        penetration: float = 0.75,
        rng: random.Random | None = None,
    ) -> None:
        self._counter = counter
        super().__init__(num_decks=num_decks, penetration=penetration, rng=rng)

    def deal(self) -> Card:
        card = super().deal()
        self._counter.observe(card)
        return card

    def shuffle(self) -> None:
        super().shuffle()
        self._counter.reset()
