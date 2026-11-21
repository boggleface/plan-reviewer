import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.scheduler import schedule  # noqa: E402


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
