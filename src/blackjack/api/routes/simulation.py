"""Simulation endpoints: basic Monte Carlo, counting, and run history."""

from __future__ import annotations

import random
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.orm import Session

from blackjack.api.schemas import (
    CountingRequest,
    CountingResponse,
    RunSummary,
    SimulationRequest,
    SimulationResponse,
    StatisticsSchema,
    downsample,
)
from blackjack.counting import CountingConfig, run_counting_simulation
from blackjack.db.database import get_db
from blackjack.db.models import SimulationRun
from blackjack.simulation import SimulationConfig, run_simulation
from blackjack.simulation.engine import Policy
from blackjack.strategy import RandomPolicy, decide

router = APIRouter(prefix="/simulate", tags=["simulation"])

DbSession = Annotated[Session, Depends(get_db)]


def _build_policy(strategy: str, seed: int | None) -> Policy:
    if strategy == "random":
        # Offset the seed so decisions don't replay the shoe's RNG stream.
        return RandomPolicy(random.Random(None if seed is None else seed + 1))
    return decide


def _persist(
    db: Session,
    kind: str,
    config: dict[str, Any],
    stats: StatisticsSchema,
    rounds: int,
    ruined: bool,
) -> int:
    run = SimulationRun(
        kind=kind,
        config=config,
        statistics=stats.model_dump(),
        rounds_played=rounds,
        ruined=ruined,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run.id


@router.post("", response_model=SimulationResponse)
async def simulate(req: SimulationRequest, db: DbSession) -> SimulationResponse:
    config = SimulationConfig(
        num_rounds=req.num_rounds,
        rules=req.rules.to_rules(),
        bet=req.bet,
        starting_bankroll=req.starting_bankroll,
        seed=req.seed,
    )
    policy = _build_policy(req.strategy, req.seed)
    result = await run_in_threadpool(run_simulation, config, policy=policy)
    stats = StatisticsSchema.from_stats(result.statistics)
    run_id = _persist(
        db, req.strategy, req.model_dump(), stats, result.rounds_played, result.ruined
    )
    return SimulationResponse(
        run_id=run_id,
        kind=req.strategy,
        rounds_played=result.rounds_played,
        ruined=result.ruined,
        statistics=stats,
        bankroll_curve=downsample(result.bankroll_curve, req.max_curve_points),
    )


@router.post("/counting", response_model=CountingResponse)
async def simulate_counting(req: CountingRequest, db: DbSession) -> CountingResponse:
    config = CountingConfig(
        num_rounds=req.num_rounds,
        rules=req.rules.to_rules(),
        system=req.to_system(),
        ramp=req.to_ramp(),
        base_bet=req.base_bet,
        starting_bankroll=req.starting_bankroll,
        seed=req.seed,
    )
    result = await run_in_threadpool(run_counting_simulation, config)
    stats = StatisticsSchema.from_stats(result.statistics)
    run_id = _persist(db, "counting", req.model_dump(), stats, result.rounds_played, result.ruined)
    return CountingResponse(
        run_id=run_id,
        kind="counting",
        rounds_played=result.rounds_played,
        ruined=result.ruined,
        statistics=stats,
        bankroll_curve=downsample(result.bankroll_curve, req.max_curve_points),
        average_bet=result.average_bet,
    )


@router.get("/runs", response_model=list[RunSummary])
def list_runs(db: DbSession, limit: int = 20) -> list[RunSummary]:
    stmt = select(SimulationRun).order_by(SimulationRun.id.desc()).limit(limit)
    return [_to_summary(run) for run in db.scalars(stmt)]


@router.get("/runs/{run_id}", response_model=RunSummary)
def get_run(run_id: int, db: DbSession) -> RunSummary:
    run = db.get(SimulationRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    return _to_summary(run)


def _to_summary(run: SimulationRun) -> RunSummary:
    return RunSummary(
        id=run.id,
        created_at=run.created_at.isoformat(),
        kind=run.kind,
        rounds_played=run.rounds_played,
        ruined=run.ruined,
        house_edge_pct=run.statistics["house_edge_pct"],
        ev_per_round=run.statistics["ev_per_round"],
    )
