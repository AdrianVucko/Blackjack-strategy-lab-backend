"""Tests for the visualization endpoints returning Plotly figure JSON."""

from __future__ import annotations


def _assert_figure(body: dict) -> None:
    assert "data" in body and "layout" in body
    assert isinstance(body["data"], list) and body["data"]
    assert "title" in body["layout"]


def test_bankroll_figure(client) -> None:
    resp = client.post(
        "/viz/bankroll",
        json={"num_rounds": 5000, "seed": 1, "starting_bankroll": 500, "bet": 5},
    )
    assert resp.status_code == 200
    body = resp.json()
    _assert_figure(body)
    assert body["data"][0]["type"] == "scatter"


def test_bankroll_figure_respects_max_points(client) -> None:
    resp = client.post(
        "/viz/bankroll", json={"num_rounds": 5000, "seed": 1, "max_curve_points": 100}
    )
    assert len(resp.json()["data"][0]["x"]) == 100


def test_result_distribution_figure(client) -> None:
    resp = client.post("/viz/result-distribution", json={"num_rounds": 5000, "seed": 2})
    assert resp.status_code == 200
    _assert_figure(resp.json())


def test_edge_curve_figure(client) -> None:
    resp = client.post(
        "/viz/counting/edge-curve", json={"num_rounds": 100000, "seed": 4, "system": "Hi-Lo"}
    )
    assert resp.status_code == 200
    body = resp.json()
    _assert_figure(body)
    bar = body["data"][0]
    assert bar["type"] == "bar"
    # Edge rises with the count: the -1 bucket is below the +2 bucket (both well sampled).
    edge = dict(zip(bar["x"], bar["y"], strict=False))
    assert edge[-1] < edge[2]


def test_true_count_distribution_figure(client) -> None:
    resp = client.post(
        "/viz/counting/true-count-distribution", json={"num_rounds": 10000, "seed": 5}
    )
    assert resp.status_code == 200
    _assert_figure(resp.json())


def test_viz_validates_request(client) -> None:
    assert client.post("/viz/bankroll", json={"num_rounds": 0}).status_code == 422
    assert (
        client.post(
            "/viz/counting/edge-curve", json={"num_rounds": 100, "system": "Nope"}
        ).status_code
        == 422
    )
