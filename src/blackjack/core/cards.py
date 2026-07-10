"""Cards, ranks, suits, and the dealing shoe."""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum, StrEnum


class Suit(StrEnum):
    CLUBS = "C"
    DIAMONDS = "D"
    HEARTS = "H"
    SPADES = "S"


class Rank(Enum):
    """Card ranks with their base blackjack value (ace is 11 by default).

    ``points`` is used instead of ``value`` because ``value`` is reserved by Enum.
    """

    TWO = ("2", 2)
    THREE = ("3", 3)
    FOUR = ("4", 4)
    FIVE = ("5", 5)
    SIX = ("6", 6)
    SEVEN = ("7", 7)
    EIGHT = ("8", 8)
    NINE = ("9", 9)
    TEN = ("10", 10)
    JACK = ("J", 10)
    QUEEN = ("Q", 10)
    KING = ("K", 10)
    ACE = ("A", 11)

    def __init__(self, symbol: str, points: int) -> None:
        self.symbol = symbol
        self.points = points

    @property
    def is_ace(self) -> bool:
        return self is Rank.ACE


@dataclass(frozen=True, slots=True)
class Card:
    rank: Rank
    suit: Suit

    @property
    def value(self) -> int:
        """Base blackjack value; ace counts as 11 here (softness handled by Hand)."""
        return self.rank.points

    def __str__(self) -> str:
        return f"{self.rank.symbol}{self.suit.value}"


def build_deck() -> list[Card]:
    """A single standard 52-card deck."""
    return [Card(rank, suit) for suit in Suit for rank in Rank]


class Shoe:
    """A multi-deck shoe that deals cards and reshuffles at a cut-card penetration.

    A seedable RNG makes shuffles reproducible for Monte Carlo simulations.
    """

    def __init__(
        self,
        num_decks: int = 6,
        penetration: float = 0.75,
        rng: random.Random | None = None,
    ) -> None:
        if num_decks < 1:
            raise ValueError("num_decks must be at least 1")
        if not 0.0 < penetration <= 1.0:
            raise ValueError("penetration must be in (0, 1]")

        self.num_decks = num_decks
        self.penetration = penetration
        self._rng = rng or random.Random()
        self._cards: list[Card] = []
        self._dealt = 0
        self.shuffle()

    @property
    def cards_remaining(self) -> int:
        return len(self._cards) - self._dealt

    @property
    def total_cards(self) -> int:
        return self.num_decks * 52

    @property
    def decks_remaining(self) -> float:
        return self.cards_remaining / 52

    def shuffle(self) -> None:
        self._cards = [card for _ in range(self.num_decks) for card in build_deck()]
        self._rng.shuffle(self._cards)
        self._dealt = 0

    def set_cards(self, cards: list[Card]) -> None:
        """Replace the remaining cards with a fixed sequence (dealt front-first).

        Useful for deterministic tests and scripted teaching scenarios.
        """
        self._cards = list(cards)
        self._dealt = 0

    def needs_shuffle(self) -> bool:
        """True once the dealt fraction has passed the penetration cut card."""
        return self._dealt >= self.penetration * self.total_cards

    def deal(self) -> Card:
        if self.cards_remaining == 0:
            raise IndexError("shoe is empty")
        card = self._cards[self._dealt]
        self._dealt += 1
        return card
