"""Card counting systems: per-rank tag values.

A *balanced* system's tags sum to zero across a full deck, so its edge signal is
the *true count* (running count divided by decks remaining). An *unbalanced*
system (e.g. KO) does not, and is played off the running count directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from blackjack.core.cards import Card


@dataclass(frozen=True, slots=True)
class CountingSystem:
    name: str
    values: Mapping[str, int]  # keyed by rank symbol ("2".."10", "J", "Q", "K", "A")
    balanced: bool
    level: int = 1

    def value(self, card: Card) -> int:
        return self.values[card.rank.symbol]


def _tags(spec: Mapping[str, int]) -> Mapping[str, int]:
    return MappingProxyType(dict(spec))


HI_LO = CountingSystem(
    name="Hi-Lo",
    values=_tags(
        {"2": 1, "3": 1, "4": 1, "5": 1, "6": 1, "7": 0, "8": 0, "9": 0,
         "10": -1, "J": -1, "Q": -1, "K": -1, "A": -1}
    ),
    balanced=True,
)

KO = CountingSystem(
    name="KO",
    values=_tags(
        {"2": 1, "3": 1, "4": 1, "5": 1, "6": 1, "7": 1, "8": 0, "9": 0,
         "10": -1, "J": -1, "Q": -1, "K": -1, "A": -1}
    ),
    balanced=False,
)

HI_OPT_I = CountingSystem(
    name="Hi-Opt I",
    values=_tags(
        {"2": 0, "3": 1, "4": 1, "5": 1, "6": 1, "7": 0, "8": 0, "9": 0,
         "10": -1, "J": -1, "Q": -1, "K": -1, "A": 0}
    ),
    balanced=True,
)

SYSTEMS: Mapping[str, CountingSystem] = MappingProxyType(
    {system.name: system for system in (HI_LO, KO, HI_OPT_I)}
)
