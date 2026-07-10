"""Basic strategy lookup for 4-8 deck games.

Encodes the standard multi-deck basic strategy as compact code tables and
resolves them into concrete :class:`Action` decisions given the table rules
(dealer soft-17, double, double-after-split, surrender).

Code legend (per cell):
    H  hit                         S  stand
    D  double else hit             d  double else stand
    R  surrender else hit          r  surrender else stand
    P  split                       p  split if DAS else hit

Columns are dealer upcards 2, 3, 4, 5, 6, 7, 8, 9, 10, A (index = value - 2).
Base tables assume the dealer stands on soft 17 (S17); H17 patches are applied
when ``rules.dealer_hits_soft_17`` is set.
"""

from __future__ import annotations

from blackjack.core.cards import Card
from blackjack.core.enums import Action
from blackjack.core.hand import Hand
from blackjack.core.rules import Rules

UPCARDS: tuple[int, ...] = (2, 3, 4, 5, 6, 7, 8, 9, 10, 11)

# fmt: off
_HARD_S17: dict[int, str] = {
    8:  "HHHHHHHHHH",
    9:  "HDDDDHHHHH",
    10: "DDDDDDDDHH",
    11: "DDDDDDDDDH",
    12: "HHSSSHHHHH",
    13: "SSSSSHHHHH",
    14: "SSSSSHHHHH",
    15: "SSSSSHHHRH",
    16: "SSSSSHHRRR",
    17: "SSSSSSSSSS",
}

_SOFT_S17: dict[int, str] = {
    12: "HHHHHHHHHH",
    13: "HHHDDHHHHH",
    14: "HHHDDHHHHH",
    15: "HHDDDHHHHH",
    16: "HHDDDHHHHH",
    17: "HDDDDHHHHH",
    18: "SDDDDSSHHH",
    19: "SSSSSSSSSS",
    20: "SSSSSSSSSS",
}

_PAIRS_S17: dict[int, str] = {
    11: "PPPPPPPPPP",  # A,A
    10: "SSSSSSSSSS",
    9:  "PPPPPSPPSS",
    8:  "PPPPPPPPPP",
    7:  "PPPPPPHHHH",
    6:  "pPPPPHHHHH",
    4:  "HHHppHHHHH",
    3:  "ppPPPPHHHH",
    2:  "ppPPPPHHHH",
}
# fmt: on


def _patch(row: str, index: int, char: str) -> str:
    return row[:index] + char + row[index + 1 :]


def _tables(rules: Rules) -> tuple[dict[int, str], dict[int, str], dict[int, str]]:
    hard = dict(_HARD_S17)
    soft = dict(_SOFT_S17)
    pairs = dict(_PAIRS_S17)
    if rules.dealer_hits_soft_17:
        hard[11] = _patch(hard[11], 9, "D")  # double 11 vs A
        hard[15] = _patch(hard[15], 9, "R")  # surrender 15 vs A
        hard[17] = _patch(hard[17], 9, "r")  # surrender 17 vs A
        soft[18] = _patch(soft[18], 0, "d")  # A,7 double-else-stand vs 2
        soft[19] = _patch(soft[19], 4, "d")  # A,8 double-else-stand vs 6
    return hard, soft, pairs


def _column(dealer_upcard: Card) -> int:
    value = 11 if dealer_upcard.rank.is_ace else dealer_upcard.rank.points
    return value - 2


def _resolve(
    code: str,
    *,
    can_double: bool,
    can_surrender: bool,
    das: bool,
) -> Action:
    match code:
        case "H":
            return Action.HIT
        case "S":
            return Action.STAND
        case "D":
            return Action.DOUBLE if can_double else Action.HIT
        case "d":
            return Action.DOUBLE if can_double else Action.STAND
        case "R":
            return Action.SURRENDER if can_surrender else Action.HIT
        case "r":
            return Action.SURRENDER if can_surrender else Action.STAND
        case "P":
            return Action.SPLIT
        case "p":
            return Action.SPLIT if das else Action.HIT
    raise ValueError(f"unknown strategy code: {code!r}")


def decide(
    hand: Hand,
    dealer_upcard: Card,
    rules: Rules,
    *,
    can_double: bool | None = None,
    can_split: bool | None = None,
    can_surrender: bool | None = None,
) -> Action:
    """Return the basic-strategy action for ``hand`` against ``dealer_upcard``.

    Availability of double/split/surrender is inferred from the hand and rules
    when not passed explicitly, so callers mid-round can override them (e.g. no
    resplits remaining).
    """
    col = _column(dealer_upcard)
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

    hard, soft, pairs = _tables(rules)

    if can_split and hand.is_pair:
        row = pairs.get(hand.cards[0].rank.points)
        if row is not None:
            return _resolve(
                row[col],
                can_double=can_double,
                can_surrender=can_surrender,
                das=rules.double_after_split,
            )

    total = hand.total
    if hand.is_soft:
        row = soft.get(total)
        if row is None:
            return Action.STAND
        return _resolve(
            row[col], can_double=can_double, can_surrender=can_surrender, das=rules.double_after_split
        )

    if total <= 7:
        return Action.HIT
    if total >= 18:
        return Action.STAND
    return _resolve(
        hard[total][col],
        can_double=can_double,
        can_surrender=can_surrender,
        das=rules.double_after_split,
    )


_PAIR_LABELS: dict[int, str] = {
    11: "A,A", 10: "10,10", 9: "9,9", 8: "8,8", 7: "7,7",
    6: "6,6", 5: "5,5", 4: "4,4", 3: "3,3", 2: "2,2",
}


def build_chart(rules: Rules) -> dict[str, dict[str, dict[str, str]]]:
    """Render the full basic-strategy chart as nested dicts for the frontend.

    Structure: ``{section: {hand_label: {dealer_upcard: action}}}`` where
    sections are ``hard``, ``soft``, and ``pairs``, and actions are
    :class:`Action` string values. Assumes a fresh two-card decision.
    """
    hard, soft, pairs = _tables(rules)
    das = rules.double_after_split
    surrender = rules.surrender_allowed

    def render(row: str) -> dict[str, str]:
        return {
            _upcard_label(upcard): _resolve(
                row[i], can_double=True, can_surrender=surrender, das=das
            ).value
            for i, upcard in enumerate(UPCARDS)
        }

    return {
        "hard": {str(total): render(row) for total, row in sorted(hard.items())},
        "soft": {f"A,{total - 11}": render(row) for total, row in sorted(soft.items()) if total > 12},
        "pairs": {_PAIR_LABELS[points]: render(row) for points, row in sorted(pairs.items())},
    }


def _upcard_label(upcard: int) -> str:
    return "A" if upcard == 11 else str(upcard)
