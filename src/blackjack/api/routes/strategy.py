"""Basic strategy chart endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from blackjack.api.schemas import RulesSchema, StrategyChartResponse
from blackjack.strategy import build_chart

router = APIRouter(prefix="/strategy", tags=["strategy"])


@router.get("/chart", response_model=StrategyChartResponse)
def get_chart(rules: Annotated[RulesSchema, Query()]) -> StrategyChartResponse:
    """Return the basic-strategy chart for the given rule set."""
    return StrategyChartResponse(rules=rules, chart=build_chart(rules.to_rules()))
