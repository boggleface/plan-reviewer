import sys
from pathlib import Path

from fastapi.testclient import TestClient
from ortools.sat.python import cp_model

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402

client = TestClient(app)


def test_plans_are_listed():
    response = client.get("/api/plans")
    assert response.status_code == 200
    assert {plan["id"] for plan in response.json()} == {"spring-market", "lantern-festival", "harbour-run"}


def test_pages_origin_is_allowed_by_cors():
    response = client.get(
        "/api/plans",
        headers={"Origin": "https://boggleface.github.io"},
    )
    assert response.headers["access-control-allow-origin"] == "https://boggleface.github.io"


def test_get_existing_plan():
    response = client.get("/api/plans/spring-market")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "spring-market"
    assert "text" in data
    assert "review" in data
    assert "schedule" in data
    assert data["schedule"]["status"] == "scheduled"


def test_missing_plan_returns_404():
    response = client.get("/api/plans/nonexistent-plan-id")
    assert response.status_code == 404
    assert "Plan not found" in response.json().get("detail", "")


def test_schedule_endpoint_valid():
    response = client.post(
        "/api/schedule",
        json={
            "tasks": [
                {"id": "A", "name": "Task A", "owner": "Ann", "duration_days": 2, "depends_on": []},
                {"id": "B", "name": "Task B", "owner": "Bob", "duration_days": 3, "depends_on": ["A"]},
            ],
            "deadline_day": 10,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "scheduled"
    assert data["end_day"] == 5
    assert data["meets_deadline"] is True
    assert data["days_late"] == 0


def test_schedule_rejects_duplicate_ids():
    response = client.post(
        "/api/schedule",
        json={
            "tasks": [
                {"id": "A", "name": "Task 1", "owner": None, "duration_days": 1, "depends_on": []},
                {"id": "A", "name": "Task 2", "owner": None, "duration_days": 1, "depends_on": []},
            ],
            "deadline_day": 10,
        },
    )
    assert response.status_code >= 400


def test_schedule_rejects_unknown_dependency():
    response = client.post(
        "/api/schedule",
        json={
            "tasks": [
                {"id": "A", "name": "Task A", "owner": None, "duration_days": 1, "depends_on": ["MISSING"]},
            ],
            "deadline_day": 10,
        },
    )
    assert response.status_code >= 400


def test_schedule_rejects_invalid_duration():
    response = client.post(
        "/api/schedule",
        json={
            "tasks": [
                {"id": "A", "name": "Task A", "owner": None, "duration_days": 0, "depends_on": []},
            ],
            "deadline_day": 10,
        },
    )
    assert response.status_code >= 400


def test_schedule_rejects_too_many_tasks():
    tasks = [
        {"id": f"T{i}", "name": f"Task {i}", "owner": None, "duration_days": 1, "depends_on": []}
        for i in range(61)
    ]
    response = client.post(
        "/api/schedule",
        json={"tasks": tasks, "deadline_day": 100},
    )
    assert response.status_code >= 400


def test_schedule_returns_cycle():
    response = client.post(
        "/api/schedule",
        json={
            "tasks": [
                {"id": "A", "name": "Task A", "owner": None, "duration_days": 1, "depends_on": ["B"]},
                {"id": "B", "name": "Task B", "owner": None, "duration_days": 1, "depends_on": ["A"]},
            ],
            "deadline_day": 10,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cycle"
    assert set(data["cycle"]) == {"A", "B"}
    assert data["end_day"] is None


def test_schedule_returns_feasible_result_when_solver_cannot_prove_optimality(monkeypatch):
    monkeypatch.setattr(
        cp_model.CpSolver,
        "Solve",
        lambda self, model: cp_model.FEASIBLE,
    )
    monkeypatch.setattr(
        cp_model.CpSolver,
        "Value",
        lambda self, variable: {"start_A": 0, "end_A": 1, "makespan": 1}[
            variable.Name()
        ],
    )
    response = client.post(
        "/api/schedule",
        json={
            "tasks": [
                {"id": "A", "name": "Task A", "owner": None, "duration_days": 1, "depends_on": []},
            ],
            "deadline_day": 10,
        },
    )

    assert response.status_code == 200
    assert response.json()["end_day"] == 1
    assert response.json()["optimal"] is False
