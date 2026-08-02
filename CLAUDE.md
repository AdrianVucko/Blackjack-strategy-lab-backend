# Blackjack Strategy Lab — Backend

## Overview

Backend for **Blackjack Strategy Lab**, a learning application for blackjack rules,
optimal strategy, card counting, Monte Carlo simulations, and statistical
visualization. This repo is the Python/FastAPI backend; the React frontend lives
separately.

## Tech Stack

Python, FastAPI, NumPy, Pandas, SciPy, Matplotlib, Plotly, SQLite, SQLAlchemy, pytest, Docker Compose

## Current Status

Backend is **feature-complete**: the full brief (rules → strategy → simulation →
counting → API → visualization) plus CI is shipped and on `origin/master`
(commit `a715e43`). 107 tests; ruff + mypy (strict) clean. Frontend API contract
lives at `docs/frontend-handoff.md`. Added since: uniform-random baseline policy
(`strategy/random_policy.py`, selectable via `strategy: "basic" | "random"` on
`POST /simulate`) as the worst-case reference for the thesis experiments. 118 tests.

Open / backlog (optional enhancements — none in progress):

| Area | Status | Notes |
|------|--------|-------|
| Counting depth | Backlog | index-play deviations + insurance (currently bet-variation only) |
| Bankroll fan | Backlog | multi-session percentile-band viz for risk analysis |
| Alembic migrations | Backlog | once the DB schema stabilizes |

## Architecture

The `core` package is framework-agnostic (no FastAPI/DB imports) so it can be
driven directly by the simulation engine and reused across API endpoints.

- `core/cards.py` — `Card`, `Rank` (uses `.points`, not `.value`), `Suit`, seedable `Shoe`
- `core/hand.py` — `Hand` value logic (soft/hard aces, blackjack, bust, pair)
- `core/rules.py` — `Rules` config, `play_dealer`, `resolve` (settlement)
- `strategy/basic_strategy.py` — code-table basic strategy; `decide(hand, upcard, rules)` and `build_chart(rules)`
- `strategy/random_policy.py` — `RandomPolicy`: uniform-random legal action (baseline strategy)
- `simulation/engine.py` — `play_round(shoe, rules, policy)`: full round incl. peek, split, double, surrender
- `simulation/simulator.py` — `run_simulation(config)`: seeded loop, bankroll/ruin tracking
- `simulation/statistics.py` — EV, house edge, variance, std dev, 95% CI, risk of ruin (diffusion approx)
- `counting/systems.py` — `CountingSystem` tags (Hi-Lo, KO, Hi-Opt I); `SYSTEMS` registry
- `counting/counter.py` — running/true count; `counting/shoe.py` — `CountingShoe` auto-counts every deal
- `counting/betting.py` — `BetRamp` (count -> units); `counting/simulation.py` — `run_counting_simulation`
- `api/schemas.py` — Pydantic request/response models; `RulesSchema.to_rules()`, `downsample()`
- `api/routes/strategy.py` — `GET /strategy/chart`; `api/routes/simulation.py` — `POST /simulate[/counting]`, `GET /simulate/runs[/{id}]`
- `db/models.py` — `SimulationRun` (persists kind, config JSON, statistics JSON)
- `analysis.py` — numpy helpers (`count_edge_curve`, `histogram`), plotting-library-free
- `viz.py` — Plotly figure builders returning JSON dicts (via `fig.to_json`)
- `api/routes/viz.py` — `POST /viz/bankroll`, `/viz/result-distribution`, `/viz/counting/edge-curve`, `/viz/counting/true-count-distribution`

## Recent Decisions

| Decision | Why |
|----------|-----|
| `Rank.points` instead of `.value` | `value` is a reserved attribute on Python `Enum` |
| Seedable `Shoe(rng=random.Random(seed))` | Reproducible Monte Carlo runs |
| `core` has no framework deps | Reusable by simulation engine and API alike |
| src layout + `pythonpath=["src"]` | Avoids import ambiguity; clean packaging |
| Basic strategy as S17 code tables + H17 patch | One source of truth; rule variants derived, not duplicated |
| Simulation returns net in base-bet units; simulator scales by `bet` | Keeps engine bet-agnostic; bankroll math lives in one place |
| Risk of ruin via diffusion approx `exp(-2·b·μ/σ²)` | Closed-form, no extra trials; returns 1.0 when player has no edge |
| Pluggable `policy` on `play_round`/`run_simulation` | Lets counting inject bet/deviation logic later without engine changes |
| `CountingShoe` subclasses `Shoe` to auto-count on `deal()` | Counts all dealt cards with zero engine changes |
| Counting bet index = true count (balanced) / running count (unbalanced KO) | Matches how each system is actually played |
| Counting validated via count-conditional edge, not aggregate EV | Bet-weighted variance makes single-seed aggregate EV too noisy to test |
| Simulations run via `run_in_threadpool` | CPU-bound loops must not block the async event loop |
| Bankroll curve downsampled (`max_curve_points`) in responses | Keeps payloads small for Plotly; full array stays server-side |
| Tables created in FastAPI `lifespan` (no Alembic yet) | Simple for SQLite dev; add migrations if the schema grows |
| Viz returns Plotly figure JSON (not PNG) | Frontend is react-plotly; interactive client-side rendering |
| `analysis.py` (numpy) split from `viz.py` (plotly) | Numbers stay unit-testable without a plotting lib |
| Edge-curve endpoint forces a flat bet ramp | Makes each round's net a per-unit result so buckets read as edge |
| String enums use `StrEnum`; mypy scoped to `src`; plotly stubs ignored | Clean strict mypy + ruff without typing the test suite or vendoring stubs |
| Random policy seeded with `seed + 1`, not `seed` | Same seed as the shoe would replay the identical RNG stream and correlate decisions with shuffles |
| `/simulate` persists `kind` = requested strategy (`basic`/`random`) | Run history distinguishes baseline vs basic-strategy runs; additive for the frontend |

## Development Commands

```bash
pip install -e ".[dev]"                          # install with dev tools
uvicorn blackjack.main:app --reload --app-dir src  # run API
pytest                                            # tests
ruff check . && mypy                              # lint + type-check
docker compose up --build                         # containerized
```

Note: full dependency install (NumPy/SciPy/Matplotlib) targets Python 3.12.

## Next Step

Backend work is done and pushed; the frontend is being built in a separate repo
using `docs/frontend-handoff.md` as the API contract. If returning to the
backend, pick a backlog item above — **counting depth (index-play deviations +
insurance)** is the highest-value next step; it extends the pluggable `policy`
and touches `strategy/basic_strategy.py` + `counting/simulation.py`.

Note: the full scientific stack (NumPy/SciPy/Matplotlib) targets Python 3.12;
this machine runs 3.14, so verification used a venv with pytest + numpy + plotly
+ the FastAPI stack. Use Python 3.12 (or Docker) for the complete install.
