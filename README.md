# Blackjack Strategy Lab — Backend

Backend for **Blackjack Strategy Lab**: an application for learning blackjack rules,
demonstrating optimal strategy, practicing card counting, running Monte Carlo
simulations, and visualizing statistical results.

## Stack

- **API**: Python 3.12+ · FastAPI · Uvicorn
- **Simulation & stats**: NumPy · Pandas · SciPy
- **Charts**: Matplotlib (offline) · Plotly (web)
- **Persistence**: SQLite · SQLAlchemy 2.0
- **Testing**: pytest
- **Runtime**: Docker Compose

## Project layout

```
src/blackjack/
├── main.py            # FastAPI entry point (create_app)
├── config.py          # pydantic-settings
├── core/              # Rules engine: cards, hand, rules, enums
├── strategy/          # Basic strategy tables (planned)
├── simulation/        # Monte Carlo engine + statistics (planned)
├── api/routes/        # HTTP routers
└── db/                # SQLAlchemy engine + session
tests/core/            # Rules engine tests
```

## Getting started

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run the API (http://localhost:8000, docs at /docs)
uvicorn blackjack.main:app --reload --app-dir src

# Tests
pytest

# Lint & type-check
ruff check . && mypy
```

## Docker

```bash
docker compose up --build   # API on http://localhost:8000
```

## Core rules engine

The `core` package models the game independently of the API:

- `cards.py` — `Card`, `Rank`, `Suit`, and a seedable multi-deck `Shoe`
- `hand.py` — `Hand` with soft/hard ace, blackjack, bust, and pair logic
- `rules.py` — configurable `Rules`, dealer play, and settlement (`resolve`)

The seedable `Shoe` (via `random.Random(seed)`) makes simulations reproducible.
