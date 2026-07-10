"""Running and true count tracking for a counting system."""

from __future__ import annotations

from collections.abc import Iterable

from blackjack.core.cards import Card
from blackjack.counting.systems import CountingSystem

_MIN_DECKS = 0.5  # floor to keep the true count from exploding near a reshuffle


class Counter:
    def __init__(self, system: CountingSystem) -> None:
        self.system = system
        self._running = 0
        self._seen = 0

    @property
    def running_count(self) -> int:
        return self._running

    @property
    def cards_seen(self) -> int:
        return self._seen

    def observe(self, card: Card) -> None:
        self._running += self.system.value(card)
        self._seen += 1

    def observe_many(self, cards: Iterable[Card]) -> None:
        for card in cards:
            self.observe(card)

    def reset(self) -> None:
        self._running = 0
        self._seen = 0

    def true_count(self, decks_remaining: float) -> float:
        return self._running / max(decks_remaining, _MIN_DECKS)

    def bet_index(self, decks_remaining: float) -> float:
        """The count value used for bet sizing: true count if balanced, else running."""
        return self.true_count(decks_remaining) if self.system.balanced else float(self._running)
