"""A blackjack hand and its value logic (soft/hard aces, blackjack, bust)."""

from __future__ import annotations

from dataclasses import dataclass, field

from blackjack.core.cards import Card


@dataclass(slots=True)
class Hand:
    cards: list[Card] = field(default_factory=list)
    from_split: bool = False

    def add(self, card: Card) -> None:
        self.cards.append(card)

    @property
    def total(self) -> int:
        """Best total <= 21 when possible; otherwise the busted hard total."""
        hard = sum(card.value if not card.rank.is_ace else 1 for card in self.cards)
        aces = sum(1 for card in self.cards if card.rank.is_ace)
        total = hard
        # Promote one ace from 1 to 11 while it keeps the hand at or below 21.
        if aces and total + 10 <= 21:
            total += 10
        return total

    @property
    def is_soft(self) -> bool:
        """True when an ace is currently counted as 11."""
        hard = sum(card.value if not card.rank.is_ace else 1 for card in self.cards)
        aces = sum(1 for card in self.cards if card.rank.is_ace)
        return bool(aces) and hard + 10 <= 21

    @property
    def is_blackjack(self) -> bool:
        """A natural 21: exactly two cards, not from a split."""
        return len(self.cards) == 2 and self.total == 21 and not self.from_split

    @property
    def is_bust(self) -> bool:
        return self.total > 21

    @property
    def is_pair(self) -> bool:
        return len(self.cards) == 2 and self.cards[0].rank.points == self.cards[1].rank.points

    def __len__(self) -> int:
        return len(self.cards)

    def __str__(self) -> str:
        return " ".join(str(card) for card in self.cards)
