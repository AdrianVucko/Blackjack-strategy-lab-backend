"""Request/response schemas for the API and helpers to bridge to the domain."""

from __future__ import annotations

from typing import Literal

import numpy as np
from pydantic import BaseModel, Field, field_validator

from blackjack.core.rules import Rules
from blackjack.counting.betting import HI_LO_RAMP, BetRamp
from blackjack.counting.systems import SYSTEMS, CountingSystem
from blackjack.simulation.statistics import Statistics

_MAX_ROUNDS = 5_000_000


class RulesSchema(BaseModel):
    num_decks: int = Field(default=6, ge=1, le=8)
    dealer_hits_soft_17: bool = True
    blackjack_payout: float = Field(default=1.5, gt=0)
    double_allowed: bool = True
    double_after_split: bool = True
    resplit_allowed: bool = True
    max_splits: int = Field(default=3, ge=0, le=4)
    surrender_allowed: bool = False
    penetration: float = Field(default=0.75, gt=0, le=1)

    def to_rules(self) -> Rules:
        return Rules(**self.model_dump())


class StatisticsSchema(BaseModel):
    rounds: int
    ev_per_round: float
    house_edge_pct: float
    variance: float
    std_dev: float
    std_error: float
    ci95: tuple[float, float]
    total_result: float
    risk_of_ruin: float | None

    @classmethod
    def from_stats(cls, stats: Statistics) -> StatisticsSchema:
        return cls(
            rounds=stats.rounds,
            ev_per_round=stats.ev_per_round,
            house_edge_pct=stats.house_edge_pct,
            variance=stats.variance,
            std_dev=stats.std_dev,
            std_error=stats.std_error,
            ci95=stats.ci95,
            total_result=stats.total_result,
            risk_of_ruin=stats.risk_of_ruin,
        )


class SimulationRequest(BaseModel):
    num_rounds: int = Field(ge=1, le=_MAX_ROUNDS)
    rules: RulesSchema = Field(default_factory=RulesSchema)
    strategy: Literal["basic", "random"] = "basic"
    bet: float = Field(default=1.0, gt=0)
    starting_bankroll: float | None = Field(default=None, gt=0)
    seed: int | None = None
    max_curve_points: int = Field(default=500, ge=2, le=5000)


class CountingRequest(SimulationRequest):
    strategy: Literal["basic"] = "basic"  # counting always plays basic strategy
    system: str = "Hi-Lo"
    base_bet: float = Field(default=1.0, gt=0)
    ramp_tiers: list[tuple[float, float]] | None = None

    @field_validator("system")
    @classmethod
    def _known_system(cls, value: str) -> str:
        if value not in SYSTEMS:
            raise ValueError(f"unknown system {value!r}; choose from {sorted(SYSTEMS)}")
        return value

    def to_system(self) -> CountingSystem:
        return SYSTEMS[self.system]

    def to_ramp(self) -> BetRamp:
        if self.ramp_tiers is None:
            return HI_LO_RAMP
        return BetRamp(tiers=tuple(self.ramp_tiers))


class SimulationResponse(BaseModel):
    run_id: int
    kind: str
    rounds_played: int
    ruined: bool
    statistics: StatisticsSchema
    bankroll_curve: list[float]


class CountingResponse(SimulationResponse):
    average_bet: float


class StrategyChartResponse(BaseModel):
    rules: RulesSchema
    chart: dict[str, dict[str, dict[str, str]]]


class RunSummary(BaseModel):
    id: int
    created_at: str
    kind: str
    rounds_played: int
    ruined: bool
    house_edge_pct: float
    ev_per_round: float


def downsample(curve: np.ndarray, max_points: int) -> list[float]:
    """Evenly downsample a curve to at most ``max_points`` points (keeping the last)."""
    n = int(curve.size)
    if n <= max_points:
        return [float(x) for x in curve]
    idx = np.linspace(0, n - 1, max_points).round().astype(int)
    idx[-1] = n - 1
    return [float(curve[i]) for i in idx]
