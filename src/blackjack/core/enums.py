"""Enumerations shared across the core domain."""

from enum import StrEnum


class Action(StrEnum):
    """A decision a player can make on a hand."""

    HIT = "hit"
    STAND = "stand"
    DOUBLE = "double"
    SPLIT = "split"
    SURRENDER = "surrender"


class Outcome(StrEnum):
    """The result of a settled hand from the player's perspective."""

    WIN = "win"
    LOSE = "lose"
    PUSH = "push"
    BLACKJACK = "blackjack"
    SURRENDER = "surrender"
