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
| Basic strategy | Not started | `strategy/` placeholder |
| Monte Carlo | Not started | `simulation/` placeholder |
| Card counting | Not started | — |
| Statistics/viz API | Not started | — |

## Architecture

The `core` package is framework-agnostic (no FastAPI/DB imports) so it can be
driven directly by the simulation engine and reused across API endpoints.

- `core/cards.py` — `Card`, `Rank` (uses `.points`, not `.value`), `Suit`, seedable `Shoe`
- `core/hand.py` — `Hand` value logic (soft/hard aces, blackjack, bust, pair)
- `core/rules.py` — `Rules` config, `play_dealer`, `resolve` (settlement)

## Recent Decisions

| Decision | Why |
|----------|-----|
| `Rank.points` instead of `.value` | `value` is a reserved attribute on Python `Enum` |
| Seedable `Shoe(rng=random.Random(seed))` | Reproducible Monte Carlo runs |
| `resolve` returns net units of base bet | Cleanly handles double (wager=2) and surrender (-0.5) |
| `core` has no framework deps | Reusable by simulation engine and API alike |
| src layout + `pythonpath=["src"]` | Avoids import ambiguity; clean packaging |

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

Build the **basic strategy** module (`strategy/`): encode the optimal
hit/stand/double/split decision tables and expose a lookup that takes a player
`Hand` + dealer upcard + `Rules` and returns an `Action`. This unblocks both the
"optimal strategy" teaching feature and the strategy-driven Monte Carlo player.
