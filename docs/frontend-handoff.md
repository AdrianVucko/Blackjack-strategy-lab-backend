# Blackjack Strategy Lab — Frontend Handoff

Hand this file to a new Claude Code session working on the **frontend** repo. It
is the complete contract for talking to the backend. Nothing here needs the
backend source open — it is self-contained.

Backend repo: `https://github.com/AdrianVucko/Blackjack-strategy-lab-backend`
Backend commit this doc describes: `6712559`

---

## 1. What the app is

**Blackjack Strategy Lab** teaches blackjack: the rules, optimal *basic
strategy*, *card counting*, *Monte Carlo simulations*, and *statistical
visualization*. This backend (Python/FastAPI) does all the computation and the
frontend renders it.

**Frontend stack** (already decided): React + Tailwind CSS, Vitest for tests,
**Plotly** for charts (use `react-plotly.js`). Chart endpoints return ready-made
Plotly figure JSON — see §6.

---

## 2. Running the backend locally

```bash
# from the backend repo
docker compose up --build          # -> http://localhost:8000
# or
uvicorn blackjack.main:app --reload --app-dir src
```

- Base URL: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`
- OpenAPI schema (importable for client generation): `http://localhost:8000/openapi.json`
- **CORS** is preconfigured for `http://localhost:5173` (Vite) and
  `http://localhost:3000`. If you use another port, set `CORS_ORIGINS` in the
  backend `.env`.

Tip: you can generate a typed client from `/openapi.json` (e.g. `openapi-typescript`)
instead of hand-writing the types in §7.

---

## 3. Endpoint summary

| Method | Path | Body | Returns |
|--------|------|------|---------|
| GET | `/health` | — | `{status, version, environment}` |
| GET | `/strategy/chart` | rules as **query params** | `StrategyChartResponse` |
| POST | `/simulate` | `SimulationRequest` | `SimulationResponse` |
| POST | `/simulate/counting` | `CountingRequest` | `CountingResponse` |
| GET | `/simulate/runs?limit=20` | — | `RunSummary[]` |
| GET | `/simulate/runs/{id}` | — | `RunSummary` (404 if missing) |
| POST | `/viz/bankroll` | `SimulationRequest` | Plotly figure JSON |
| POST | `/viz/result-distribution` | `SimulationRequest` | Plotly figure JSON |
| POST | `/viz/counting/edge-curve` | `CountingRequest` | Plotly figure JSON |
| POST | `/viz/counting/true-count-distribution` | `CountingRequest` | Plotly figure JSON |

Validation failures return HTTP **422** with FastAPI's error body. Unknown run id
returns **404**.

---

## 4. Data models (request/response shapes)

All numbers are JSON numbers. Fields show `name: type = default`.

### Rules (`rules` object, used everywhere)
```
num_decks: int (1..8) = 6
dealer_hits_soft_17: bool = true
blackjack_payout: float (>0) = 1.5          # 1.5 = 3:2, 1.2 = 6:5
double_allowed: bool = true
double_after_split: bool = true
resplit_allowed: bool = true
max_splits: int (0..4) = 3
surrender_allowed: bool = false
penetration: float (0..1] = 0.75            # fraction of shoe dealt before reshuffle
```

### SimulationRequest
```
num_rounds: int (1..5_000_000)              # REQUIRED
rules: Rules = {defaults above}
bet: float (>0) = 1.0
starting_bankroll: float (>0) | null = null # set to enable ruin + risk_of_ruin
seed: int | null = null                     # set for reproducible results
max_curve_points: int (2..5000) = 500       # bankroll_curve is downsampled to this
```

### CountingRequest  (extends SimulationRequest with)
```
system: "Hi-Lo" | "KO" | "Hi-Opt I" = "Hi-Lo"
base_bet: float (>0) = 1.0                   # money value of one betting unit
ramp_tiers: [ [count, units], ... ] | null = null
    # optional custom bet ramp. Step function on the count (true count for
    # balanced systems, running count for KO). Ascending by count; first tier is
    # the floor. Default = classic 1-12 Hi-Lo spread:
    #   [[-Infinity,1],[2,2],[3,4],[4,8],[5,12]]
    # NOTE: JSON has no -Infinity. Use a very negative number like -999 for the
    # floor tier, e.g. [[-999,1],[2,2],[3,4],[4,8],[5,12]].
```

### Statistics (inside simulation responses)
```
rounds: int
ev_per_round: float          # mean net per round, in base-bet units (negative = house edge)
house_edge_pct: float        # -ev_per_round * 100
variance: float
std_dev: float               # ~1.15 per hand for basic strategy
std_error: float
ci95: [float, float]         # 95% CI for ev_per_round
total_result: float          # summed net over all rounds, in base-bet units
risk_of_ruin: float | null   # null unless starting_bankroll was provided (0..1)
```

### SimulationResponse
```
run_id: int
kind: "basic"
rounds_played: int           # < num_rounds if the bankroll was ruined early
ruined: bool
statistics: Statistics
bankroll_curve: float[]      # cumulative money over rounds, downsampled
```

### CountingResponse  (extends SimulationResponse with)
```
kind: "counting"
average_bet: float           # mean wager in base-bet units (shows the spread in use)
```

### StrategyChartResponse
```
rules: Rules
chart: {
  hard:  { "8".."17":  { "2".."10","A": Action } },
  soft:  { "A,2".."A,9": { "2".."10","A": Action } },
  pairs: { "A,A","10,10","9,9","8,8","7,7","6,6","4,4","3,3","2,2": { "2".."10","A": Action } },
}
```
- `Action` is one of: `"hit" | "stand" | "double" | "split" | "surrender"`.
- The chart only lists *decision* rows. Hard totals ≤7 are always `hit` and ≥18
  are always `stand`, so they are not included — handle those two cases in the UI
  if you render a full grid.
- **`pairs` has no `5,5`** — a pair of fives is never split, it is played as a
  hard 10 (see `hard["10"]`). Render `5,5` by reusing the hard-10 row.
- Dealer-upcard columns are `"2"`..`"10"` and `"A"` (ace).
- The chart **changes with the rules** (e.g. `dealer_hits_soft_17`,
  `surrender_allowed`, `double_after_split`), so re-fetch when rules change.

### RunSummary
```
id: int
created_at: string (ISO 8601)
kind: "basic" | "counting"
rounds_played: int
ruined: bool
house_edge_pct: float
ev_per_round: float
```

---

## 5. Example requests

```bash
# Strategy chart for a 6-deck H17 game with surrender (query params = rule fields)
curl "http://localhost:8000/strategy/chart?dealer_hits_soft_17=true&surrender_allowed=true"

# Basic Monte Carlo, reproducible, with a bankroll (enables risk of ruin)
curl -X POST http://localhost:8000/simulate \
  -H 'content-type: application/json' \
  -d '{"num_rounds":100000,"seed":2024,"bet":10,"starting_bankroll":1000,
       "rules":{"dealer_hits_soft_17":false}}'

# Card counting with the default 1-12 Hi-Lo spread
curl -X POST http://localhost:8000/simulate/counting \
  -H 'content-type: application/json' \
  -d '{"num_rounds":200000,"seed":7,"system":"Hi-Lo","base_bet":10}'
```

A `/simulate` response looks like:
```json
{
  "run_id": 1, "kind": "basic", "rounds_played": 100000, "ruined": false,
  "statistics": {
    "rounds": 100000, "ev_per_round": -0.005, "house_edge_pct": 0.5,
    "variance": 1.33, "std_dev": 1.154, "std_error": 0.0036,
    "ci95": [-0.012, 0.002], "total_result": -500.0, "risk_of_ruin": 0.42
  },
  "bankroll_curve": [1000.0, 995.0, 1002.5, ...]  // <= max_curve_points points
}
```

---

## 6. Rendering the chart endpoints (Plotly)

The four `/viz/*` endpoints return a **complete Plotly figure** as JSON with
`data` and `layout` keys. Feed them straight into `react-plotly.js`:

```tsx
import Plot from "react-plotly.js";

const res = await fetch("http://localhost:8000/viz/bankroll", {
  method: "POST",
  headers: { "content-type": "application/json" },
  body: JSON.stringify({ num_rounds: 50000, seed: 1, starting_bankroll: 1000, bet: 10 }),
});
const fig = await res.json();

<Plot data={fig.data} layout={fig.layout} style={{ width: "100%", height: "100%" }} />
```

The figures:
- `/viz/bankroll` — line chart, bankroll/equity over rounds (respects `max_curve_points`).
- `/viz/result-distribution` — histogram of per-round net results.
- `/viz/counting/edge-curve` — **the money shot**: bar chart of player edge (%)
  by true count, green above 0 / red below. Reproduces the count→edge relationship.
- `/viz/counting/true-count-distribution` — histogram of true counts seen.

You can either use these prebuilt figures, or call the data endpoints and build
your own Plotly/D3 charts client-side for full styling control. For a Tailwind-
themed UI you may prefer the latter for stat cards but the prebuilt figures are
fine for the analytical plots.

---

## 7. TypeScript types (copy into the frontend)

```ts
export type Action = "hit" | "stand" | "double" | "split" | "surrender";
export type CountingSystem = "Hi-Lo" | "KO" | "Hi-Opt I";

export interface Rules {
  num_decks: number;
  dealer_hits_soft_17: boolean;
  blackjack_payout: number;
  double_allowed: boolean;
  double_after_split: boolean;
  resplit_allowed: boolean;
  max_splits: number;
  surrender_allowed: boolean;
  penetration: number;
}

export interface SimulationRequest {
  num_rounds: number;
  rules?: Partial<Rules>;
  bet?: number;
  starting_bankroll?: number | null;
  seed?: number | null;
  max_curve_points?: number;
}

export interface CountingRequest extends SimulationRequest {
  system?: CountingSystem;
  base_bet?: number;
  ramp_tiers?: [number, number][] | null;
}

export interface Statistics {
  rounds: number;
  ev_per_round: number;
  house_edge_pct: number;
  variance: number;
  std_dev: number;
  std_error: number;
  ci95: [number, number];
  total_result: number;
  risk_of_ruin: number | null;
}

export interface SimulationResponse {
  run_id: number;
  kind: "basic" | "counting";
  rounds_played: number;
  ruined: boolean;
  statistics: Statistics;
  bankroll_curve: number[];
}

export interface CountingResponse extends SimulationResponse {
  average_bet: number;
}

export type UpcardKey = "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" | "10" | "A";
export type ChartRow = Record<UpcardKey, Action>;
export interface StrategyChartResponse {
  rules: Rules;
  chart: {
    hard: Record<string, ChartRow>;
    soft: Record<string, ChartRow>;
    pairs: Record<string, ChartRow>;
  };
}

export interface RunSummary {
  id: number;
  created_at: string;
  kind: "basic" | "counting";
  rounds_played: number;
  ruined: boolean;
  house_edge_pct: number;
  ev_per_round: number;
}

// Plotly figures come back as { data: any[]; layout: Record<string, unknown> }
export interface PlotlyFigure {
  data: unknown[];
  layout: Record<string, unknown>;
}
```

---

## 8. Suggested frontend structure (maps features → endpoints)

| Page / view | Uses | Notes |
|-------------|------|-------|
| **Rules configurator** | shared `Rules` state | Drives every other call; keep in a context/store |
| **Basic strategy chart** | `GET /strategy/chart` | Color-coded grid (hard/soft/pairs tabs). Suggested colors: hit=red, stand=green, double=blue, split=yellow, surrender=grey. Re-fetch on rules change |
| **Simulator** | `POST /simulate`, `POST /viz/bankroll`, `POST /viz/result-distribution` | Stat cards from `statistics`; bankroll + distribution charts |
| **Card counting lab** | `POST /simulate/counting`, `POST /viz/counting/edge-curve`, `POST /viz/counting/true-count-distribution` | System picker + bet-ramp editor (`ramp_tiers`); show `average_bet`; edge curve is the teaching centerpiece |
| **Run history** | `GET /simulate/runs`, `GET /simulate/runs/{id}` | Table of past runs |

---

## 9. Behaviour notes / gotchas

- **Reproducibility:** pass the same `seed` (+ identical request) to get identical
  results — good for demos and snapshot tests.
- **Long sims:** `num_rounds` up to 5,000,000. Large runs take seconds; show a
  loading state. They run off the event loop server-side so the API stays
  responsive, but a single request still blocks until done — consider a spinner.
- **Ruin:** `risk_of_ruin` is only returned when `starting_bankroll` is set. When
  a run is `ruined`, `rounds_played < num_rounds` and the curve ends at ruin.
- **House edge sign:** `ev_per_round` is negative for basic strategy (house wins
  slowly, ~0.5% S17 / ~0.75% H17). Card counting shifts the *count-conditional*
  edge positive at high counts — visualize with the edge-curve endpoint rather
  than expecting a single positive aggregate number (bet-weighted variance is
  large).
- **`bankroll_curve`** is downsampled to `max_curve_points`; it is for plotting,
  not exact per-round values.
- **Counting decisions** currently use basic strategy for play and vary only the
  *bet* (index-play deviations + insurance are a planned backend enhancement).

---

## 10. How to start the frontend session

Point the new session at this file, e.g.:
> "Read `docs/frontend-handoff.md` (copied into this repo). Build the React +
> Tailwind frontend for Blackjack Strategy Lab against that API contract. Start
> with the Rules configurator + Basic strategy chart."

Everything the frontend needs about the backend is in this document.
