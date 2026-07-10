"""Visualization endpoints returning Plotly figure JSON for the frontend."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from blackjack import viz
from blackjack.api.schemas import CountingRequest, SimulationRequest
from blackjack.counting import CountingConfig, run_counting_simulation
from blackjack.counting.betting import FLAT_RAMP
from blackjack.simulation import SimulationConfig, run_simulation
from blackjack.viz import PlotlyFigure

router = APIRouter(prefix="/viz", tags=["visualization"])


def _sim_config(req: SimulationRequest) -> SimulationConfig:
    return SimulationConfig(
        num_rounds=req.num_rounds,
        rules=req.rules.to_rules(),
        bet=req.bet,
        starting_bankroll=req.starting_bankroll,
        seed=req.seed,
    )


@router.post("/bankroll", response_model=None)
async def bankroll(req: SimulationRequest) -> PlotlyFigure:
    result = await run_in_threadpool(run_simulation, _sim_config(req))
    return viz.bankroll_figure(result.bankroll_curve, max_points=req.max_curve_points)


@router.post("/result-distribution", response_model=None)
async def result_distribution(req: SimulationRequest) -> PlotlyFigure:
    result = await run_in_threadpool(run_simulation, _sim_config(req))
    return viz.result_distribution_figure(result.nets)


@router.post("/counting/edge-curve", response_model=None)
async def edge_curve(req: CountingRequest) -> PlotlyFigure:
    # A flat ramp makes each round's net a per-unit result, so buckets read as edge.
    config = CountingConfig(
        num_rounds=req.num_rounds,
        rules=req.rules.to_rules(),
        system=req.to_system(),
        ramp=FLAT_RAMP,
        seed=req.seed,
    )
    result = await run_in_threadpool(run_counting_simulation, config)
    return viz.edge_curve_figure(result.bet_indices, result.nets)


@router.post("/counting/true-count-distribution", response_model=None)
async def true_count_distribution(req: CountingRequest) -> PlotlyFigure:
    config = CountingConfig(
        num_rounds=req.num_rounds,
        rules=req.rules.to_rules(),
        system=req.to_system(),
        ramp=req.to_ramp(),
        base_bet=req.base_bet,
        seed=req.seed,
    )
    result = await run_in_threadpool(run_counting_simulation, config)
    return viz.true_count_distribution_figure(result.bet_indices)
