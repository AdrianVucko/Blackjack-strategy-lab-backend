# Blackjack Strategy Lab — Backend

## Overview

Backend for **Blackjack Strategy Lab**, a learning application for blackjack rules,
optimal strategy, card counting, Monte Carlo simulations, and statistical
visualization. This repo is the Python/FastAPI backend; the React frontend lives
separately.

## Tech Stack

Python, FastAPI, NumPy, Pandas, SciPy, Matplotlib, Plotly, SQLite, SQLAlchemy, pytest, Docker Compose

## Current Status

| Area | Status | Notes |
|------|--------|-------|
| Project scaffold | Done | src layout, pyproject, Docker, pytest config |
| Core rules engine | Done | cards, hand, rules — 39 tests passing |
| FastAPI app | Done | `create_app`, CORS, `/health` |
| DB layer | Skeleton | engine/session/Base ready; no models yet |
| Basic strategy | Done | 4-8 deck tables, `decide()` + `build_chart()` — 19 tests |
| Monte Carlo | Done | round engine + simulator + stats — 14 tests; edge/std validated |
| Card counting | Not started | — |
| Statistics/viz API | Not started | — |

## Architecture

The `core` package is framework-agnostic (no FastAPI/DB imports) so it can be
driven directly by the simulation engine and reused across API endpoints.

- `core/cards.py` — `Card`, `Rank` (uses `.points`, not `.value`), `Suit`, seedable `Shoe`
- `core/hand.py` — `Hand` value logic (soft/hard aces, blackjack, bust, pair)
- `core/rules.py` — `Rules` config, `play_dealer`, `resolve` (settlement)
- `strategy/basic_strategy.py` — code-table basic strategy; `decide(hand, upcard, rules)` and `build_chart(rules)`
- `simulation/engine.py` — `play_round(shoe, rules, policy)`: full round incl. peek, split, double, surrender
- `simulation/simulator.py` — `run_simulation(config)`: seeded loop, bankroll/ruin tracking
- `simulation/statistics.py` — EV, house edge, variance, std dev, 95% CI, risk of ruin (diffusion approx)

## Recent Decisions

| Decision | Why |
|----------|-----|
| `Rank.points` instead of `.value` | `value` is a reserved attribute on Python `Enum` |
| Seedable `Shoe(rng=random.Random(seed))` | Reproducible Monte Carlo runs |
| `resolve` returns net units of base bet | Cleanly handles double (wager=2) and surrender (-0.5) |
| `core` has no framework deps | Reusable by simulation engine and API alike |
| src layout + `pythonpath=["src"]` | Avoids import ambiguity; clean packaging |
| Basic strategy as S17 code tables + H17 patch | One source of truth; rule variants derived, not duplicated |
| Simulation returns net in base-bet units; simulator scales by `bet` | Keeps engine bet-agnostic; bankroll math lives in one place |
| Risk of ruin via diffusion approx `exp(-2·b·μ/σ²)` | Closed-form, no extra trials; returns 1.0 when player has no edge |
| Pluggable `policy` on `play_round`/`run_simulation` | Lets counting inject bet/deviation logic later without engine changes |

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

Two candidates, pick per priority:

1. **Card counting** (`counting/`): Hi-Lo running/true count from the `Shoe`, and a
   count-based betting/deviation policy plugged into `run_simulation` via the
   existing `policy` hook — to quantify the counter's edge vs. flat betting.
2. **API layer**: expose `strategy.build_chart` and `run_simulation` through
   FastAPI endpoints returning Plotly-ready JSON, plus SQLAlchemy models to
   persist simulation configs/results (DB layer already scaffolded).
