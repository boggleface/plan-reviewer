import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.scheduler import schedule  # noqa: E402
from ortools.sat.python import cp_model  # noqa: E402


def task(id, duration_days, depends_on=(), owner=None):
    return {
        "id": id,
        "name": id,
        "owner": owner,
        "duration_days": duration_days,
        "depends_on": list(depends_on),
    }


def test_single_task_ends_after_its_duration():
    result = schedule([task("A", 3)], 10)
    assert result["schedule"] == [{"id": "A", "start_day": 0, "end_day": 3}]
    assert result["end_day"] == 3
    assert result["meets_deadline"] is True
    assert result["days_late"] == 0


def test_dependent_task_starts_after_its_dependency():
    result = schedule([task("A", 3), task("B", 2, ["A"])], 10)
    by_id = {item["id"]: item for item in result["schedule"]}
    assert by_id["B"]["start_day"] == 3
    assert result["end_day"] == 5


def test_circular_dependencies_are_reported():
    result = schedule(
        [
            task("A", 3, ["B"]),
            task("B", 2, ["A"]),
        ],
        10,
    )

    assert result["status"] == "cycle"
    assert result["schedule"] == []
    assert result["end_day"] is None
    assert set(result["cycle"]) == {"A", "B"}


def test_self_dependency_is_cycle():
    result = schedule([task("A", 1, ["A"])], 10)
    assert result["status"] == "cycle"
    assert result["schedule"] == []
    assert result["cycle"] == ["A"]


def test_same_owner_tasks_do_not_overlap():
    result = schedule(
        [
            task("A", 3, owner="Ann"),
            task("B", 2, owner="Ann"),
        ],
        10,
    )
    a = next(s for s in result["schedule"] if s["id"] == "A")
    b = next(s for s in result["schedule"] if s["id"] == "B")
    assert a["end_day"] <= b["start_day"] or b["end_day"] <= a["start_day"]
    assert result["end_day"] == 5


def test_null_owner_tasks_can_overlap():
    result = schedule(
        [
            task("A", 3, owner=None),
            task("B", 2, owner=None),
        ],
        10,
    )
    a = next(s for s in result["schedule"] if s["id"] == "A")
    b = next(s for s in result["schedule"] if s["id"] == "B")
    assert a["start_day"] == 0
    assert b["start_day"] == 0
    assert result["end_day"] == 3


def test_contract_example_produces_correct_schedule():
    tasks = [
        {"id": "A", "name": "Book the hall", "owner": "Ann", "duration_days": 3, "depends_on": []},
        {"id": "B", "name": "Sign the contract", "owner": "Ann", "duration_days": 2, "depends_on": ["A"]},
        {"id": "C", "name": "Design the poster", "owner": "Ann", "duration_days": 4, "depends_on": []},
        {"id": "D", "name": "Print the poster", "owner": "Bob", "duration_days": 2, "depends_on": ["C"]},
    ]
    result = schedule(tasks, 10)
    assert result["status"] == "scheduled"
    assert result["end_day"] == 9
    assert result["meets_deadline"] is True
    assert result["days_late"] == 0

    by_id = {s["id"]: s for s in result["schedule"]}
    # Ann's tasks: C, A, B should not overlap
    assert max(by_id["C"]["start_day"], by_id["A"]["start_day"]) >= min(by_id["C"]["end_day"], by_id["A"]["end_day"])
    assert max(by_id["A"]["start_day"], by_id["B"]["start_day"]) >= min(by_id["A"]["end_day"], by_id["B"]["end_day"])
    # Dependencies respected
    assert by_id["B"]["start_day"] >= by_id["A"]["end_day"]
    assert by_id["D"]["start_day"] >= by_id["C"]["end_day"]


def test_finds_optimal_schedule_for_owner_resource_counterexample():
    tasks = [
        task("T0", 3, owner="C"),
        task("T1", 5, ["T0"], owner="B"),
        task("T2", 4, owner="B"),
    ]

    result = schedule(tasks, 100)
    by_id = {item["id"]: item for item in result["schedule"]}

    assert result["end_day"] == 9
    assert by_id["T0"] == {"id": "T0", "start_day": 0, "end_day": 3}
    assert by_id["T2"] == {"id": "T2", "start_day": 0, "end_day": 4}
    assert by_id["T1"] == {"id": "T1", "start_day": 4, "end_day": 9}


def test_feasible_unproven_solver_result_is_returned(monkeypatch):
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

    result = schedule([task("A", 1)], 10)

    assert result["status"] == "scheduled"
    assert result["schedule"] == [{"id": "A", "start_day": 0, "end_day": 1}]
    assert result["end_day"] == 1
    assert result["optimal"] is False


def test_unknown_solver_result_falls_back_to_feasible_schedule(monkeypatch):
    monkeypatch.setattr(
        cp_model.CpSolver,
        "Solve",
        lambda self, model: cp_model.UNKNOWN,
    )

    result = schedule(
        [
            task("A", 2),
            task("B", 3, ["A"]),
            task("C", 4),
        ],
        20,
    )

    by_id = {item["id"]: item for item in result["schedule"]}
    assert result["end_day"] == 9
    assert by_id["A"]["end_day"] <= by_id["B"]["start_day"]
    assert result["optimal"] is False


def test_sixty_task_schedule_finishes_within_contract_limit():
    tasks = [
        task(
            f"T{i}",
            (i % 7) + 1,
            [f"T{i - 1}"] if i else [],
            owner=f"Owner{i % 5}",
        )
        for i in range(60)
    ]

    started = time.perf_counter()
    result = schedule(tasks, 500)
    elapsed = time.perf_counter() - started

    assert result["status"] == "scheduled"
    assert len(result["schedule"]) == 60
    assert elapsed < 10


def test_deadline_missed():
    result = schedule([task("A", 15)], 10)
    assert result["meets_deadline"] is False
    assert result["days_late"] == 5


def test_empty_task_list():
    result = schedule([], 10)
    assert result["status"] == "scheduled"
    assert result["end_day"] == 0
    assert result["schedule"] == []
    assert result["meets_deadline"] is True
    assert result["days_late"] == 0


def test_empty_task_list_with_negative_deadline_reports_days_late():
    result = schedule([], -3)

    assert result["end_day"] == 0
    assert result["meets_deadline"] is False
    assert result["days_late"] == 3
