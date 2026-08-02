"""Endpoint tests for health, strategy chart, and simulation routes."""

from __future__ import annotations


def test_health(client) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_strategy_chart_default_rules(client) -> None:
    resp = client.get("/strategy/chart")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body["chart"]) == {"hard", "soft", "pairs"}
    assert body["chart"]["pairs"]["A,A"]["10"] == "split"
    assert body["chart"]["hard"]["11"]["10"] == "double"


def test_strategy_chart_reacts_to_rules(client) -> None:
    s17 = client.get("/strategy/chart", params={"dealer_hits_soft_17": False}).json()
    h17 = client.get("/strategy/chart", params={"dealer_hits_soft_17": True}).json()
    # 11 vs Ace: hit under S17, double under H17.
    assert s17["chart"]["hard"]["11"]["A"] == "hit"
    assert h17["chart"]["hard"]["11"]["A"] == "double"


def test_strategy_chart_validates_num_decks(client) -> None:
    resp = client.get("/strategy/chart", params={"num_decks": 99})
    assert resp.status_code == 422


def test_simulate_basic(client) -> None:
    resp = client.post("/simulate", json={"num_rounds": 5000, "seed": 1})
    assert resp.status_code == 200
    body = resp.json()
    assert body["rounds_played"] == 5000
    assert body["statistics"]["rounds"] == 5000
    assert body["kind"] == "basic"
    assert isinstance(body["run_id"], int)


def test_simulate_curve_is_downsampled(client) -> None:
    resp = client.post(
        "/simulate", json={"num_rounds": 5000, "seed": 1, "max_curve_points": 100}
    )
    assert len(resp.json()["bankroll_curve"]) == 100


def test_simulate_reproducible_via_seed(client) -> None:
    payload = {"num_rounds": 3000, "seed": 42}
    first = client.post("/simulate", json=payload).json()
    second = client.post("/simulate", json=payload).json()
    assert first["statistics"]["total_result"] == second["statistics"]["total_result"]


def test_simulate_random_strategy(client) -> None:
    resp = client.post(
        "/simulate", json={"num_rounds": 3000, "seed": 1, "strategy": "random"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["kind"] == "random"
    basic = client.post("/simulate", json={"num_rounds": 3000, "seed": 1}).json()
    assert body["statistics"]["ev_per_round"] < basic["statistics"]["ev_per_round"]


def test_simulate_rejects_unknown_strategy(client) -> None:
    resp = client.post("/simulate", json={"num_rounds": 100, "strategy": "nope"})
    assert resp.status_code == 422


def test_counting_rejects_random_strategy(client) -> None:
    resp = client.post(
        "/simulate/counting", json={"num_rounds": 100, "strategy": "random"}
    )
    assert resp.status_code == 422


def test_simulate_counting(client) -> None:
    resp = client.post(
        "/simulate/counting",
        json={"num_rounds": 5000, "seed": 3, "system": "Hi-Lo"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["kind"] == "counting"
    assert body["average_bet"] >= 1.0


def test_counting_rejects_unknown_system(client) -> None:
    resp = client.post(
        "/simulate/counting", json={"num_rounds": 100, "system": "Nope"}
    )
    assert resp.status_code == 422


def test_simulate_validates_num_rounds(client) -> None:
    assert client.post("/simulate", json={"num_rounds": 0}).status_code == 422


def test_run_history(client) -> None:
    created = client.post("/simulate", json={"num_rounds": 1000, "seed": 7}).json()
    run_id = created["run_id"]

    listing = client.get("/simulate/runs").json()
    assert any(run["id"] == run_id for run in listing)

    single = client.get(f"/simulate/runs/{run_id}")
    assert single.status_code == 200
    assert single.json()["id"] == run_id

    assert client.get("/simulate/runs/999999").status_code == 404
