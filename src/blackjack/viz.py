"""Plotly figure builders returning JSON-serializable figure dicts.

Each builder returns ``dict`` (via Plotly's JSON encoder, so numpy arrays are
converted) ready to hand to react-plotly on the frontend.
"""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import plotly.graph_objects as go

from blackjack.analysis import count_edge_curve, histogram

_WIN = "#2ca02c"
_LOSS = "#d62728"
_TEMPLATE = "plotly_white"

PlotlyFigure = dict[str, Any]


def _to_dict(fig: go.Figure) -> PlotlyFigure:
    return json.loads(fig.to_json())


def _downsample_xy(curve: np.ndarray, max_points: int) -> tuple[list[int], list[float]]:
    n = int(curve.size)
    if n <= max_points:
        idx = np.arange(n)
    else:
        idx = np.linspace(0, n - 1, max_points).round().astype(int)
        idx[-1] = n - 1
    return [int(i) for i in idx], [float(curve[i]) for i in idx]


def bankroll_figure(bankroll_curve: np.ndarray, *, max_points: int = 500) -> PlotlyFigure:
    x, y = _downsample_xy(bankroll_curve, max_points)
    fig = go.Figure(go.Scatter(x=x, y=y, mode="lines", name="Bankroll", line={"color": "#1f77b4"}))
    fig.update_layout(
        title="Bankroll over rounds",
        xaxis_title="Round",
        yaxis_title="Cumulative result",
        template=_TEMPLATE,
    )
    return _to_dict(fig)


def result_distribution_figure(nets: np.ndarray, *, bins: int = 40) -> PlotlyFigure:
    centers, counts = histogram(nets, bins=bins)
    fig = go.Figure(go.Bar(x=centers, y=counts, marker_color="#1f77b4"))
    fig.update_layout(
        title="Distribution of per-round results",
        xaxis_title="Net result (base-bet units)",
        yaxis_title="Rounds",
        template=_TEMPLATE,
        bargap=0.02,
    )
    return _to_dict(fig)


def edge_curve_figure(bet_indices: np.ndarray, nets: np.ndarray) -> PlotlyFigure:
    curve = count_edge_curve(bet_indices, nets)
    counts = [b.count for b in curve]
    edges = [b.mean_net * 100 for b in curve]
    errors = [b.ci95_half * 100 for b in curve]
    colors = [_WIN if e >= 0 else _LOSS for e in edges]
    fig = go.Figure(
        go.Bar(
            x=counts,
            y=edges,
            marker_color=colors,
            error_y={"type": "data", "array": errors},
            hovertext=[f"n={b.n:,}" for b in curve],
        )
    )
    fig.add_hline(y=0, line_color="black", line_width=1)
    fig.update_layout(
        title="Player edge by true count",
        xaxis_title="True count (floored)",
        yaxis_title="Edge (%)",
        template=_TEMPLATE,
    )
    return _to_dict(fig)


def true_count_distribution_figure(bet_indices: np.ndarray, *, bins: int = 40) -> PlotlyFigure:
    centers, counts = histogram(bet_indices, bins=bins)
    fig = go.Figure(go.Bar(x=centers, y=counts, marker_color="#9467bd"))
    fig.update_layout(
        title="Distribution of true counts seen",
        xaxis_title="True count",
        yaxis_title="Rounds",
        template=_TEMPLATE,
        bargap=0.02,
    )
    return _to_dict(fig)
