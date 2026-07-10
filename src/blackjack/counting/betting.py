"""Bet ramps mapping a count value to a wager in base-bet units."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BetRamp:
    """Step function from a count value to a bet size (in base-bet units).

    ``tiers`` is an ascending sequence of ``(threshold, units)`` pairs; the bet
    is the units of the highest threshold not exceeding the count. The first
    tier's units act as the floor for counts below every threshold.
    """

    tiers: tuple[tuple[float, float], ...]

    def units(self, count: float) -> float:
        result = self.tiers[0][1]
        for threshold, units in self.tiers:
            if count >= threshold:
                result = units
            else:
                break
        return result


# Classic 1-12 Hi-Lo spread keyed on true count.
HI_LO_RAMP = BetRamp(
    tiers=((float("-inf"), 1.0), (2.0, 2.0), (3.0, 4.0), (4.0, 8.0), (5.0, 12.0)),
)

FLAT_RAMP = BetRamp(tiers=((float("-inf"), 1.0),))
